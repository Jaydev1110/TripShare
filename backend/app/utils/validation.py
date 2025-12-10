from fastapi import HTTPException

MAX_UPLOAD_SIZE_MB = 20
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp"]

def validate_file_size(size: int):
    if size > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large. Max size is {MAX_UPLOAD_SIZE_MB}MB")

def validate_mime_type(mime_type: str):
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_MIME_TYPES)}")
