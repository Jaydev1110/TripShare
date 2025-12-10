import os
import sys
from datetime import datetime

# Add backend directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.supabase_client import supabase

def cleanup_expired_groups():
    print(f"Starting cleanup at {datetime.now()}")
    try:
        # Find expired groups
        now = datetime.utcnow().isoformat()
        response = supabase.table("groups").select("id").lt("expires_at", now).execute()
        
        expired_groups = response.data
        print(f"Found {len(expired_groups)} expired groups")
        
        for group in expired_groups:
            group_id = group["id"]
            print(f"Deleting group {group_id}")
            
            # Delete photos from storage bucket
            try:
                # Get all photos for this group
                photos_response = supabase.table("photos").select("storage_path").eq("group_id", group_id).execute()
                if photos_response.data:
                    paths = [p["storage_path"] for p in photos_response.data]
                    # Also try to delete thumbs
                    thumb_paths = [f"photos/{group_id}/thumbs/{os.path.basename(p)}" for p in paths]
                    
                    all_paths = paths + thumb_paths
                    
                    # Batch delete (Supabase limits might apply, but for now simple list)
                    supabase.storage.from_("photos").remove(all_paths)
                    print(f"Deleted {len(paths)} photos for group {group_id}")
            except Exception as e:
                print(f"Error deleting photos for group {group_id}: {e}")

            # Delete group (cascading should handle members/photos DB rows)
            supabase.table("groups").delete().eq("id", group_id).execute()
            
        print("Cleanup completed")
    except Exception as e:
        print(f"Error during cleanup: {str(e)}")

if __name__ == "__main__":
    cleanup_expired_groups()
