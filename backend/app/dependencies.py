import os
from fastapi import Header, HTTPException, Depends
from app.models.auth import UserResponse
from app.utils.auth_stub import get_mock_current_user
from app.routes.auth import get_current_user_dep as get_real_current_user

# Dependency that switches based on environment variable
async def get_current_user_dep(authorization: str = Header(None)) -> UserResponse:
    if os.getenv("MOCK_AUTH", "false").lower() == "true":
         # Use stub
         # Stub requires a header usually for signature matching, but our stub ignores it
         # But we need to ensure Depends signature matches if we were strict.
         return await get_mock_current_user()
    else:
         # Reuse the real auth dependency logic
         # get_real_current_user expects HTTPAuthorizationCredentials
         # We need to bridge this if we want to be clean.
         # But `get_real_current_user` uses `Depends(security)` where security is HTTPBearer()
         # HTTPBearer() parses the header for us.
         
         # If this function is used AS a dependency, FastAPI resolves its params.
         # But we can't easily conditionally call `Depends`.
         
         # BETTER APPROACH:
         # Define the dependency to use the "Real" one's signature (HTTPBearer)
         # and then check env.
         pass

# Re-implementing correctly:
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
security = HTTPBearer()

async def get_current_user_dep(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserResponse:
    if os.getenv("MOCK_AUTH", "false").lower() == "true":
        return await get_mock_current_user()
    else:
        return await get_real_current_user(credentials)
