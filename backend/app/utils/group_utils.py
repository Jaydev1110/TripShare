import random
import string
from uuid import UUID
from app.database.supabase_client import supabase

def generate_group_code(length: int = 6) -> str:
    """
    Generates a unique random code for a group.
    Ensures uniqueness by checking against the database.
    """
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choices(chars, k=length))
        # Check if code exists
        response = supabase.table("groups").select("id").eq("code", code).execute()
        if not response.data:
            return code

def can_manage_group(user_id: UUID, group_id: UUID) -> bool:
    """
    Checks if a user is the owner of a group.
    """
    response = supabase.table("groups").select("owner_user_id").eq("id", str(group_id)).single().execute()
    if response.data:
        return response.data["owner_user_id"] == str(user_id)
    return False
