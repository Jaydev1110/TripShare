from datetime import datetime
from typing import Dict, Union

def get_current_utc_time() -> datetime:
    """Returns current UTC time."""
    return datetime.utcnow()

def is_group_expired(group: Union[Dict, object]) -> bool:
    """
    Checks if a group is expired based on its expires_at field.
    Handles both dictionary and object (Pydantic model) input.
    """
    expires_at = None
    
    if isinstance(group, dict):
        expires_at = group.get("expires_at")
    elif hasattr(group, "expires_at"):
        expires_at = group.expires_at
        
    if not expires_at:
        return False
        
    if isinstance(expires_at, str):
        try:
            expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        except ValueError:
            # Fallback for simple string if isoformat fails or other format
            return False 
            
    # Ensure comparison is offset-naive or offset-aware consistent
    # Assuming Supabase returns offset-naive UTC or we stripping it to be safe if mixing
    # But usually simpler to use utcnow()
    
    now = datetime.utcnow()
    
    # If expires_at has tzinfo (e.g. from ISO string), make now aware or expires_at naive
    if expires_at.tzinfo is not None:
        expires_at = expires_at.replace(tzinfo=None)
        
    return now > expires_at
