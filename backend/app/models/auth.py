from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any

class UserSignup(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    username: str = Field(..., min_length=3)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    username: Optional[str] = None
    metadata: Dict[str, Any] = {}
