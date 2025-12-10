from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, status
from app.database.supabase_client import supabase
from app.models.photo import UploadResponse, SignedURLResponse, SignedURLRequest, PhotoResponse
from app.models.auth import UserResponse
# from app.routes.auth import get_current_user_dep
from app.utils.auth_stub import get_mock_current_user as get_current_user_dep
from app.utils.storage_utils import build_storage_path, generate_thumbnail
from app.utils.validation import validate_file_size, validate_mime_type
from uuid import UUID
from datetime import datetime
import os

router = APIRouter(prefix="/photos", tags=["Photos"])

SUPABASE_BUCKET_NAME = os.getenv("SUPABASE_BUCKET_NAME", "photos")

@router.post("/upload", response_model=UploadResponse)
async def upload_photo(
    group_id: UUID = Form(...),
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user_dep)
):
    # Validate membership
    member_check = supabase.table("group_members").select("approved").eq("group_id", str(group_id)).eq("user_id", str(current_user.id)).single().execute()
    if not member_check.data or not member_check.data["approved"]:
        raise HTTPException(status_code=403, detail="Not authorized to upload to this group")

    # Validate file
    file_content = await file.read()
    validate_file_size(len(file_content))
    validate_mime_type(file.content_type)
    
    # Build path
    storage_path = build_storage_path(group_id, current_user.id, file.filename)
    
    try:
        # Upload to Storage
        supabase.storage.from_(SUPABASE_BUCKET_NAME).upload(
            path=storage_path,
            file=file_content,
            file_options={"content-type": file.content_type}
        )
        
        # Insert Metadata
        photo_data = {
            "group_id": str(group_id),
            "uploader_id": str(current_user.id),
            "storage_path": storage_path,
            "filename": file.filename,
            "mime_type": file.content_type,
            "size": len(file_content),
            "uploaded_at": datetime.utcnow().isoformat()
        }
        
        photo_response = supabase.table("photos").insert(photo_data).execute()
        if not photo_response.data:
             # Rollback storage if DB fails (simple attempt)
             supabase.storage.from_(SUPABASE_BUCKET_NAME).remove([storage_path])
             raise HTTPException(status_code=500, detail="Failed to save photo metadata")
             
        photo = photo_response.data[0]
        
        # Generate and upload thumbnail (optional, best effort)
        try:
            thumb_bytes = generate_thumbnail(file_content)
            thumb_path = f"photos/{group_id}/thumbs/{os.path.basename(storage_path)}"
            supabase.storage.from_(SUPABASE_BUCKET_NAME).upload(
                path=thumb_path,
                file=thumb_bytes,
                file_options={"content-type": "image/jpeg"}
            )
            # Ideally store thumb_path in DB, but for now we can derive it or just use it
        except Exception as e:
            print(f"Thumbnail generation failed: {e}")

        return UploadResponse(
            id=photo["id"],
            storage_path=photo["storage_path"],
            filename=photo["filename"],
            mime_type=photo["mime_type"],
            size=photo["size"],
            uploaded_at=photo["uploaded_at"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/groups/{group_id}", response_model=list[PhotoResponse])
async def list_group_photos(
    group_id: UUID,
    current_user: UserResponse = Depends(get_current_user_dep)
):
    # Validate membership
    member_check = supabase.table("group_members").select("approved").eq("group_id", str(group_id)).eq("user_id", str(current_user.id)).single().execute()
    if not member_check.data or not member_check.data["approved"]:
        raise HTTPException(status_code=403, detail="Not authorized to view photos")
        
    try:
        response = supabase.table("photos").select("*").eq("group_id", str(group_id)).execute()
        photos = []
        for p in response.data:
            # Generate a temporary signed URL for thumbnail if needed, or just return metadata
            # For now, let's just return metadata. Frontend can request signed URLs.
            photos.append(PhotoResponse(
                id=p["id"],
                filename=p["filename"],
                mime_type=p["mime_type"],
                size=p["size"],
                uploaded_at=p["uploaded_at"]
            ))
        return photos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/signed-urls", response_model=list[SignedURLResponse])
async def get_signed_urls(
    request: SignedURLRequest,
    current_user: UserResponse = Depends(get_current_user_dep)
):
    # For each photo, check permission (must be in a group user is member of)
    # This can be N+1 queries, optimized by fetching all photos and checking groups
    
    try:
        photo_ids = [str(pid) for pid in request.photo_ids]
        photos_response = supabase.table("photos").select("id, storage_path, group_id").in_("id", photo_ids).execute()
        
        if not photos_response.data:
            return []
            
        # Check permissions for all groups involved
        group_ids = list(set([p["group_id"] for p in photos_response.data]))
        
        # Get user's approved groups
        memberships = supabase.table("group_members").select("group_id").eq("user_id", str(current_user.id)).eq("approved", True).in_("group_id", group_ids).execute()
        allowed_group_ids = [m["group_id"] for m in memberships.data]
        
        urls = []
        for p in photos_response.data:
            if p["group_id"] in allowed_group_ids:
                # Generate signed URL
                signed_url = supabase.storage.from_(SUPABASE_BUCKET_NAME).create_signed_url(
                    path=p["storage_path"], 
                    expires_in=request.expires_in_seconds
                )
                # Note: supabase-py create_signed_url returns a dict or string depending on version
                # Assuming it returns {'signedURL': '...'} or similar, or just the string.
                # Adjust based on actual library behavior.
                url_str = signed_url if isinstance(signed_url, str) else signed_url.get("signedURL")
                
                urls.append(SignedURLResponse(
                    photo_id=p["id"],
                    signed_url=url_str
                ))
                
        return urls
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{photo_id}")
async def delete_photo(
    photo_id: UUID,
    current_user: UserResponse = Depends(get_current_user_dep)
):
    try:
        # Get photo details
        photo_response = supabase.table("photos").select("*").eq("id", str(photo_id)).single().execute()
        if not photo_response.data:
            raise HTTPException(status_code=404, detail="Photo not found")
            
        photo = photo_response.data
        group_id = photo["group_id"]
        uploader_id = photo["uploader_id"]
        
        # Check permission: Uploader OR Group Owner
        is_uploader = uploader_id == str(current_user.id)
        
        group_response = supabase.table("groups").select("owner_user_id").eq("id", group_id).single().execute()
        is_owner = group_response.data and group_response.data["owner_user_id"] == str(current_user.id)
        
        if not (is_uploader or is_owner):
            raise HTTPException(status_code=403, detail="Not authorized to delete this photo")
            
        # Delete from Storage
        supabase.storage.from_(SUPABASE_BUCKET_NAME).remove([photo["storage_path"]])
        
        # Delete from DB
        supabase.table("photos").delete().eq("id", str(photo_id)).execute()
        
        return {"message": "Photo deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
