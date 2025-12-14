import pytest
import uuid
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.main import app
from app.database.supabase_client import supabase

client = TestClient(app)

# Helper to mock auth
def get_auth_headers(user_id):
    return {"Authorization": f"Bearer {user_id}"} 

# Assuming mock auth uses the ID passed in header or a fixed test user
# My stub uses: 
# async def get_mock_current_user(authorization: str = Header(...)):
#     user_id = authorization.replace("Bearer ", "")
#     ...

@pytest.fixture
def test_user():
    return str(uuid.uuid4())

def test_group_expiry_lifecycle(test_user):
    # 1. Create a group
    response = client.post(
        "/groups",
        json={"title": "Expiry Test Group", "expires_in_days": 1}, # Normal 1 day
        headers=get_auth_headers(test_user)
    )
    assert response.status_code == 200
    group_id = response.json()["id"]
    group_code = response.json()["code"]

    # 2. Manually expire the group in DB (set expiry to 1 hour ago)
    past_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    supabase.table("groups").update({"expires_at": past_time}).eq("id", group_id).execute()

    # 3. New user tries to join -> Should Fail
    new_user = str(uuid.uuid4())
    join_res = client.post(
        "/groups/join",
        json={"code": group_code},
        headers=get_auth_headers(new_user)
    )
    # The error message I added was "Group has expired" (410)
    assert join_res.status_code == 410, f"Expected 410, got {join_res.status_code}: {join_res.text}"

    # 4. Upload photo -> Should Fail
    # User is owner, so they are member.
    # We need a valid file
    with open("test_image.jpg", "wb") as f:
        f.write(b"fake image data") # Minimal mock
    
    with open("test_image.jpg", "rb") as f:
        upload_res = client.post(
            "/photos/upload",
            data={"group_id": group_id},
            files={"file": ("test_image.jpg", f, "image/jpeg")},
            headers=get_auth_headers(test_user)
        )
    assert upload_res.status_code == 403
    assert "expired" in upload_res.text.lower()

    # 5. Extend Group (Owner)
    extend_res = client.post(
        f"/groups/{group_id}/extend",
        json={"extend_days": 3},
        headers=get_auth_headers(test_user)
    )
    assert extend_res.status_code == 200
    new_expiry = extend_res.json()["new_expires_at"]
    # Should be in future now
    new_expiry_dt = datetime.fromisoformat(new_expiry)
    if new_expiry_dt.tzinfo:
        new_expiry_dt = new_expiry_dt.replace(tzinfo=None)
    assert new_expiry_dt > datetime.utcnow()

    # 6. Upload photo again -> Should Success
    # Need to rewind file or re-open
    with open("test_image.jpg", "rb") as f:
        upload_res_2 = client.post(
            "/photos/upload",
            data={"group_id": group_id},
            files={"file": ("test_image.jpg", f, "image/jpeg")},
            headers=get_auth_headers(test_user)
        )
    assert upload_res_2.status_code == 200

    # Clean up
    # (Optional, Supabase might persist)
    supabase.table("groups").delete().eq("id", group_id).execute()
