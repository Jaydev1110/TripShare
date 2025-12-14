from fastapi import APIRouter, HTTPException, Depends, Response
from app.database.supabase_client import supabase
from app.models.group import (
    CreateGroupRequest, CreateGroupResponse, JoinGroupRequest,
    ApproveMemberRequest, GroupMemberResponse, GroupDetailsResponse,
    ExtendGroupRequest
)
from app.models.auth import UserResponse
from app.dependencies import get_current_user_dep
from app.utils.group_utils import generate_group_code, can_manage_group
from app.utils.time_utils import is_group_expired
from datetime import datetime, timedelta
import qrcode
from io import BytesIO

router = APIRouter(prefix="/groups", tags=["Groups"])

@router.get("", response_model=list[GroupDetailsResponse])
async def list_my_groups(
    current_user: UserResponse = Depends(get_current_user_dep)
):
    try:
        # Get groups where user is a member
        # 1. Get group_ids from group_members
        memberships = supabase.table("group_members").select("group_id").eq("user_id", str(current_user.id)).execute()
        
        if not memberships.data:
            return []
            
        group_ids = [m["group_id"] for m in memberships.data]
        
        # 2. Fetch group details
        groups_response = supabase.table("groups").select("*").in_("id", group_ids).execute()
        
        groups = []
        for g in groups_response.data:
            groups.append(GroupDetailsResponse(**g))
            
        return groups
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("", response_model=CreateGroupResponse)
async def create_group(
    group_data: CreateGroupRequest,
    current_user: UserResponse = Depends(get_current_user_dep)
):
    code = generate_group_code()
    expires_at = datetime.utcnow() + timedelta(days=group_data.expires_in_days)
    
    try:
        # Insert group
        group_response = supabase.table("groups").insert({
            "code": code,
            "owner_user_id": str(current_user.id),
            "title": group_data.title,
            "expires_at": expires_at.isoformat()
        }).execute()
        
        if not group_response.data:
             raise HTTPException(status_code=500, detail="Failed to create group")
             
        group = group_response.data[0]
        
        # Add owner as approved member
        supabase.table("group_members").insert({
            "group_id": group["id"],
            "user_id": str(current_user.id),
            "approved": True
        }).execute()
        
        return CreateGroupResponse(
            id=group["id"],
            code=group["code"],
            created_at=group["created_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{group_id}", response_model=GroupDetailsResponse)
async def get_group_details(
    group_id: str,
    current_user: UserResponse = Depends(get_current_user_dep)
):
    try:
        response = supabase.table("groups").select("*").eq("id", group_id).single().execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Group not found")
            
        group = response.data
        return GroupDetailsResponse(**group)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/join")
async def join_group(
    join_request: JoinGroupRequest,
    current_user: UserResponse = Depends(get_current_user_dep)
):
    try:
        # Find group by code
        group_response = supabase.table("groups").select("*").eq("code", join_request.code).single().execute()
        if not group_response.data:
            raise HTTPException(status_code=404, detail="Invalid group code")
            
        group_id = group_response.data["id"]
        group_data = group_response.data

        # Check for expiry
        if is_group_expired(group_data):
            raise HTTPException(status_code=410, detail="Group has expired")
        
        # Check if already a member
        member_check = supabase.table("group_members").select("*").eq("group_id", group_id).eq("user_id", str(current_user.id)).execute()
        if member_check.data:
            return {"message": "Already a member", "status": "exists"}
            
        # Add as pending member
        supabase.table("group_members").insert({
            "group_id": group_id,
            "user_id": str(current_user.id),
            "approved": False
        }).execute()
        
        return {"message": "Join request sent", "status": "pending"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{group_id}/members", response_model=list[GroupMemberResponse])
async def list_members(
    group_id: str,
    current_user: UserResponse = Depends(get_current_user_dep)
):
    try:
        # Check if user is member
        member_check = supabase.table("group_members").select("approved").eq("group_id", group_id).eq("user_id", str(current_user.id)).single().execute()
        if not member_check.data or not member_check.data["approved"]:
             raise HTTPException(status_code=403, detail="Not authorized to view members")

        # Get members with user details
        # Note: Supabase join syntax might differ, doing simple fetch for now
        # Ideally: .select("*, users(username)")
        members_response = supabase.table("group_members").select("*, users(username)").eq("group_id", group_id).execute()
        
        members = []
        for m in members_response.data:
            username = m.get("users", {}).get("username") if m.get("users") else None
            members.append(GroupMemberResponse(
                id=m["id"],
                user_id=m["user_id"],
                username=username,
                approved=m["approved"]
            ))
            
        return members
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{group_id}/approve")
async def approve_member(
    group_id: str,
    request: ApproveMemberRequest,
    current_user: UserResponse = Depends(get_current_user_dep)
):
    if not can_manage_group(current_user.id, group_id):
        raise HTTPException(status_code=403, detail="Only owner can approve members")
        
    try:
        supabase.table("group_members").update({"approved": request.approve}).eq("id", str(request.member_id)).execute()
        return {"message": "Member updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{group_id}/leave")
async def leave_group(
    group_id: str,
    current_user: UserResponse = Depends(get_current_user_dep)
):
    try:
        supabase.table("group_members").delete().eq("group_id", group_id).eq("user_id", str(current_user.id)).execute()
        return {"message": "Left group"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{group_id}")
async def delete_group(
    group_id: str,
    current_user: UserResponse = Depends(get_current_user_dep)
):
    if not can_manage_group(current_user.id, group_id):
        raise HTTPException(status_code=403, detail="Only owner can delete group")
        
    try:
        # Cascading delete should handle members/photos if configured in DB
        # Otherwise need manual deletion
        supabase.table("groups").delete().eq("id", group_id).execute()
        return {"message": "Group deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{group_id}/extend")
async def extend_group(
    group_id: str,
    request: ExtendGroupRequest,
    current_user: UserResponse = Depends(get_current_user_dep)
):
    if not can_manage_group(current_user.id, group_id):
        raise HTTPException(status_code=403, detail="Only owner can extend group")
        
    try:
        # Get current expiry
        group_response = supabase.table("groups").select("expires_at").eq("id", group_id).single().execute()
        if not group_response.data:
            raise HTTPException(status_code=404, detail="Group not found")
            
        current_expires_at_str = group_response.data["expires_at"]
        # Parse existing expiry
        # Note: simplistic parsing, assuming Supabase DB format is ISO
        current_expires_at = datetime.fromisoformat(current_expires_at_str.replace('Z', '+00:00'))
        
        # If already expired, can we extend? 
        # Requirement: "Cannot extend a permanently deleted group"
        # If it's in DB, it's not permanently deleted yet.
        # So yes, owner can extend to resurrect it before cleanup runs.
        
        # Calculate new expiry
        # If completely expired, should we extend from NOW or from old expiry?
        # Usually from NOW if it was expired, or add to existing if not.
        # Let's simple add to existing for now, or ensure it's at least NOW + days.
        
        # Logic: New Expiry = max(Now, OldExpiry) + Days
        now = datetime.utcnow()
        if current_expires_at.tzinfo:
            now = now.replace(tzinfo=current_expires_at.tzinfo) # Match TZ
            
        base_time = max(now, current_expires_at)
        new_expires_at = base_time + timedelta(days=request.extend_days)
        
        # Update
        supabase.table("groups").update({"expires_at": new_expires_at.isoformat()}).eq("id", group_id).execute()
        
        return {"message": "Group extended", "new_expires_at": new_expires_at.isoformat()}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{group_id}/qr")
async def get_group_qr(
    group_id: str,
    current_user: UserResponse = Depends(get_current_user_dep)
):
    try:
        group_response = supabase.table("groups").select("code").eq("id", group_id).single().execute()
        if not group_response.data:
            raise HTTPException(status_code=404, detail="Group not found")
            
        code = group_response.data["code"]
        # In a real app, this would be a deep link URL
        qr_data = f"tripshare://join?code={code}"
        
        img = qrcode.make(qr_data)
        buf = BytesIO()
        img.save(buf)
        buf.seek(0)
        
        return Response(content=buf.getvalue(), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
