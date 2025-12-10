from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database.supabase_client import supabase
from app.models.auth import UserSignup, UserLogin, TokenResponse, UserResponse
from gotrue.errors import AuthApiError

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

@router.post("/signup", response_model=UserResponse)
async def signup(user_data: UserSignup):
    try:
        # Sign up with Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {
                    "username": user_data.username
                }
            }
        })
        
        if not auth_response.user:
             raise HTTPException(status_code=400, detail="Signup failed")

        user_id = auth_response.user.id
        
        # Insert into 'users' table
        try:
            supabase.table("users").insert({
                "id": user_id,
                "username": user_data.username,
                "email": user_data.email
            }).execute()
        except Exception as db_error:
            # Log error but don't fail the request since auth user is created
            print(f"Database insertion error: {str(db_error)}")

        return UserResponse(
            id=user_id,
            email=user_data.email,
            username=user_data.username,
            metadata=auth_response.user.user_metadata or {}
        )

    except AuthApiError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        
        if not response.session:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        return TokenResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user_id=response.user.id
        )
    except AuthApiError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_current_user_dep(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserResponse:
    token = credentials.credentials
    try:
        user_response = supabase.auth.get_user(token)
        user = user_response.user
        
        if not user:
             raise HTTPException(status_code=401, detail="Invalid token")
             
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.user_metadata.get("username"),
            metadata=user.user_metadata or {}
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

@router.get("/me", response_model=UserResponse)
async def get_current_user(user: UserResponse = Depends(get_current_user_dep)):
    return user
