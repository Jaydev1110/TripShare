from app.models.auth import UserResponse
from uuid import uuid4

MOCK_USER_ID = "b1cc7526-53e5-443d-9f47-9bc615dc35e5"

async def get_mock_current_user() -> UserResponse:
    return UserResponse(
        id=MOCK_USER_ID,
        email="mock@example.com",
        username="mockuser",
        metadata={}
    )
