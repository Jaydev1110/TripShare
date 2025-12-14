import os
import sys
from datetime import datetime, timedelta

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.supabase_client import supabase

WARNING_THRESHOLD_DAYS = 1

def send_expiry_warnings():
    print(f"[{datetime.now()}] Checking for expiring groups...")
    
    try:
        now = datetime.utcnow()
        threshold = now + timedelta(days=WARNING_THRESHOLD_DAYS)
        
        # 1. Find groups expiring within threshold (and not already expired)
        # We want: now < expires_at < threshold
        # Supabase filtering: gt('expires_at', now), lt('expires_at', threshold)
        
        response = supabase.table("groups") \
            .select("id, title, expires_at, owner_user_id") \
            .gt("expires_at", now.isoformat()) \
            .lt("expires_at", threshold.isoformat()) \
            .execute()
            
        expiring_groups = response.data
        if not expiring_groups:
            print("No groups approaching expiry.")
            return

        print(f"Found {len(expiring_groups)} groups approaching expiry.")
        
        for group in expiring_groups:
            group_id = group["id"]
            
            # 2. Check if warning already sent recently?
            # Or just check if ANY warning exists for this group?
            # Requirement: "Insert warning records". Maybe 1 per group?
            # Or 1 per day?
            # Let's assume 1 per group for the "1 day warning".
            
            existing_warning = supabase.table("group_warnings") \
                .select("id") \
                .eq("group_id", group_id) \
                .execute()
                
            if existing_warning.data:
                # Already warned
                continue
                
            # 3. Insert warning
            print(f"Tagging group {group_id} ({group['title']}) for warning.")
            supabase.table("group_warnings").insert({
                "group_id": group_id,
                "days_left": 1 # Approximation
            }).execute()
            
            # Here we would send Email/Push notification
            
        print("Warning check completed.")
        
    except Exception as e:
        print(f"Error checking warnings: {e}")

if __name__ == "__main__":
    send_expiry_warnings()
