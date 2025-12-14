from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class CreateGroupRequest(BaseModel):
    title: str
    expires_in_days: Optional[int] = 7

class CreateGroupResponse(BaseModel):
    id: UUID
    code: str
    created_at: datetime

class JoinGroupRequest(BaseModel):
    code: str

class ApproveMemberRequest(BaseModel):
    member_id: UUID
    approve: bool

class GroupMemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    username: Optional[str]
    approved: bool

class GroupDetailsResponse(BaseModel):
    id: UUID
    code: str
    owner_user_id: UUID
    title: str
    expires_at: Optional[datetime]

class ExtendGroupRequest(BaseModel):
    extend_days: int
