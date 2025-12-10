from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class UploadResponse(BaseModel):
    id: UUID
    storage_path: str
    filename: str
    mime_type: str
    size: int
    uploaded_at: datetime

class SignedURLResponse(BaseModel):
    photo_id: UUID
    signed_url: str
    expires_at: Optional[datetime] = None

class SignedURLRequest(BaseModel):
    photo_ids: List[UUID]
    expires_in_seconds: Optional[int] = 3600

class PhotoResponse(BaseModel):
    id: UUID
    filename: str
    mime_type: str
    size: int
    uploaded_at: datetime
    thumbnail_url: Optional[str] = None
