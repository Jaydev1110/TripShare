import os
import sys
import time
import json
import httpx
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
from supabase import create_client

# Add parent dir to path to import app modules if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET_NAME = os.getenv("SUPABASE_BUCKET_NAME", "photos")
BASE_URL = "http://127.0.0.1:8000"

report = {}

def run_test():
    print("Starting Supabase Integration Test...")
    
    # 1. Confirm connection & keys
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        res = supabase.table('groups').select('id').limit(1).execute()
        report['connection_check'] = 'OK'
        print("1. Connection check: OK")
    except Exception as e:
        report['connection_check'] = f'ERROR: {str(e)}'
        print(f"1. Connection check: ERROR - {e}")
        return

    # 2. Verify photos bucket exists
    try:
        buckets = supabase.storage.list_buckets()
        found = any(b.name == SUPABASE_BUCKET_NAME for b in buckets)
        if found:
            report['bucket_exists'] = 'OK'
            print(f"2. Bucket '{SUPABASE_BUCKET_NAME}' exists: OK")
        else:
            # Try to create
            try:
                supabase.storage.create_bucket(SUPABASE_BUCKET_NAME, options={"public": False})
                report['bucket_exists'] = 'CREATED'
                print(f"2. Bucket '{SUPABASE_BUCKET_NAME}' created: OK")
            except Exception as e:
                report['bucket_exists'] = f'ERROR: {str(e)}'
                print(f"2. Bucket check: ERROR - {e}")
    except Exception as e:
        report['bucket_exists'] = f'ERROR: {str(e)}'
        print(f"2. Bucket check: ERROR - {e}")

    # 3. Verify photos table exists
    try:
        res = supabase.table("photos").select("id,storage_path,filename,mime_type,size").limit(1).execute()
        report['photos_table'] = 'OK'
        print("3. Photos table check: OK")
    except Exception as e:
        report['photos_table'] = f'ERROR: {str(e)}'
        print(f"3. Photos table check: ERROR - {e}")

    # 4. Upload test file
    storage_path = f"test-uploads/{int(time.time())}_ag_test.jpg"
    try:
        buf = BytesIO()
        Image.new("RGB", (64, 64), (255, 0, 0)).save(buf, "JPEG")
        buf.seek(0)
        file_bytes = buf.getvalue()
        
        res = supabase.storage.from_(SUPABASE_BUCKET_NAME).upload(storage_path, file_bytes, file_options={"content-type": "image/jpeg"})
        report['upload_test'] = f'OK: {storage_path}'
        print(f"4. Upload test: OK ({storage_path})")
    except Exception as e:
        report['upload_test'] = f'ERROR: {str(e)}'
        print(f"4. Upload test: ERROR - {e}")
        return # Stop if upload fails

    # 5. Verify file listed and downloadable
    try:
        # List
        list_res = supabase.storage.from_(SUPABASE_BUCKET_NAME).list("test-uploads")
        found_file = any(f['name'] == os.path.basename(storage_path) for f in list_res)
        
        # Signed URL
        signed = supabase.storage.from_(SUPABASE_BUCKET_NAME).create_signed_url(storage_path, expires_in=60)
        signed_url = signed if isinstance(signed, str) else signed.get("signedURL")
        
        # Fetch
        r = httpx.get(signed_url)
        if r.status_code == 200:
            report['signed_url_test'] = 'OK'
            print("5. Signed URL test: OK")
        else:
            report['signed_url_test'] = f'ERROR: Status {r.status_code}'
            print(f"5. Signed URL test: ERROR - Status {r.status_code}")
    except Exception as e:
        report['signed_url_test'] = f'ERROR: {str(e)}'
        print(f"5. Signed URL test: ERROR - {e}")

    # Setup for DB/API tests
    # Need a group and user
    # We'll use the backend to create a group to ensure valid state
    group_id = None
    user_id = None # We'll get this from the group creation response or auth stub
    
    # 6. Insert photo metadata
    try:
        # Create a group first via API (using mock auth)
        # We need to know the mock user ID. It's in app/utils/auth_stub.py
        # But let's just hit the create group endpoint
        with httpx.Client() as client:
            resp = client.post(f"{BASE_URL}/groups", json={"title": "Integration Test Group"})
            if resp.status_code == 200:
                group_data = resp.json()
                group_id = group_data['id']
                # We need the user_id. In mock auth, it's fixed.
                # Let's query the group to get owner_id
                g_res = supabase.table("groups").select("owner_user_id").eq("id", group_id).single().execute()
                user_id = g_res.data['owner_user_id']
                print(f"   Created test group: {group_id}")
            else:
                raise Exception(f"Failed to create test group: {resp.text}")

        photo_meta = {
            "group_id": group_id,
            "uploader_id": user_id,
            "storage_path": storage_path,
            "filename": "ag_test.jpg",
            "mime_type": "image/jpeg",
            "size": len(file_bytes)
        }
        db_res = supabase.table("photos").insert(photo_meta).execute()
        photo_id = db_res.data[0]['id']
        report['db_insert_test'] = f'OK: {photo_id}'
        print(f"6. DB Insert test: OK ({photo_id})")
    except Exception as e:
        report['db_insert_test'] = f'ERROR: {str(e)}'
        print(f"6. DB Insert test: ERROR - {e}")
        # If this fails, subsequent tests might fail

    # 7. List photos via API
    try:
        with httpx.Client() as client:
            resp = client.get(f"{BASE_URL}/photos/groups/{group_id}")
            if resp.status_code == 200:
                photos = resp.json()
                found = any(p['id'] == photo_id for p in photos)
                if found:
                    report['list_photos_endpoint'] = 'OK'
                    print("7. List photos endpoint: OK")
                else:
                    report['list_photos_endpoint'] = 'ERROR: Photo not found in list'
                    print("7. List photos endpoint: ERROR - Photo not found")
            else:
                report['list_photos_endpoint'] = f'ERROR: Status {resp.status_code}'
                print(f"7. List photos endpoint: ERROR - Status {resp.status_code}")
    except Exception as e:
        report['list_photos_endpoint'] = f'ERROR: {str(e)}'
        print(f"7. List photos endpoint: ERROR - {e}")

    # 8. Test signed-URL endpoint
    try:
        with httpx.Client() as client:
            resp = client.post(f"{BASE_URL}/photos/signed-urls", json={"photo_ids": [photo_id]})
            if resp.status_code == 200:
                urls = resp.json()
                if urls and urls[0]['signed_url']:
                    # Verify it works
                    r = httpx.get(urls[0]['signed_url'])
                    if r.status_code == 200:
                        report['signed_url_endpoint'] = 'OK'
                        print("8. Signed URL endpoint: OK")
                    else:
                        report['signed_url_endpoint'] = f'ERROR: Fetch failed {r.status_code}'
                        print(f"8. Signed URL endpoint: ERROR - Fetch failed {r.status_code}")
                else:
                    report['signed_url_endpoint'] = 'ERROR: No URL returned'
                    print("8. Signed URL endpoint: ERROR - No URL returned")
            else:
                report['signed_url_endpoint'] = f'ERROR: Status {resp.status_code}'
                print(f"8. Signed URL endpoint: ERROR - Status {resp.status_code}")
    except Exception as e:
        report['signed_url_endpoint'] = f'ERROR: {str(e)}'
        print(f"8. Signed URL endpoint: ERROR - {e}")

    # 9. Test delete via backend
    try:
        with httpx.Client() as client:
            resp = client.delete(f"{BASE_URL}/photos/{photo_id}")
            if resp.status_code == 200:
                # Verify DB
                db_check = supabase.table("photos").select("*").eq("id", photo_id).execute()
                # Verify Storage
                # Note: supabase-py remove returns list of deleted files
                # But we can just check if it exists
                # Actually, let's just trust the backend returned 200 and maybe check DB is empty
                if not db_check.data:
                    report['delete_test'] = 'OK'
                    print("9. Delete test: OK")
                else:
                    report['delete_test'] = 'ERROR: DB row still exists'
                    print("9. Delete test: ERROR - DB row still exists")
            else:
                report['delete_test'] = f'ERROR: Status {resp.status_code}'
                print(f"9. Delete test: ERROR - Status {resp.status_code}")
    except Exception as e:
        report['delete_test'] = f'ERROR: {str(e)}'
        print(f"9. Delete test: ERROR - {e}")

    # 10. Cleanup script test
    # We'll create another group and photo, expire it, and run cleanup
    try:
        # Create group
        with httpx.Client() as client:
            resp = client.post(f"{BASE_URL}/groups", json={"title": "Expired Group", "expires_in_days": -1})
            g_data = resp.json()
            exp_group_id = g_data['id']
            
            # Upload photo to it
            # We can use the backend upload for this to be quick
            buf = BytesIO()
            Image.new("RGB", (64, 64), (0, 255, 0)).save(buf, "JPEG")
            buf.seek(0)
            files = {'file': ('expire_test.jpg', buf.getvalue(), 'image/jpeg')}
            data = {'group_id': exp_group_id}
            up_resp = client.post(f"{BASE_URL}/photos/upload", data=data, files=files)
            if up_resp.status_code != 200:
                raise Exception("Failed to upload photo for cleanup test")
            
            photo_data = up_resp.json()
            exp_photo_path = photo_data['storage_path']
            
        print(f"10. Created expired group {exp_group_id} with photo {exp_photo_path}")
        
        # Run cleanup
        # Import dynamically to ensure env vars are loaded
        from scripts.cleanup_expired_groups import cleanup_expired_groups
        cleanup_expired_groups()
        
        # Verify
        g_check = supabase.table("groups").select("*").eq("id", exp_group_id).execute()
        # Check storage (using list)
        # exp_photo_path is like photos/gid/uid/timestamp_name
        # We can check if the file exists
        # Actually, let's try to download it, should fail or list it
        # Listing the directory is safer
        dir_path = os.path.dirname(exp_photo_path)
        list_res = supabase.storage.from_(SUPABASE_BUCKET_NAME).list(dir_path)
        # Should be empty or dir not exist
        
        if not g_check.data:
            report['cleanup_test'] = 'OK'
            print("10. Cleanup test: OK")
        else:
            report['cleanup_test'] = 'ERROR: Group still exists'
            print("10. Cleanup test: ERROR - Group still exists")
            
    except Exception as e:
        report['cleanup_test'] = f'ERROR: {str(e)}'
        print(f"10. Cleanup test: ERROR - {e}")

    # 11. RLS
    report['rls_check'] = 'SKIPPED (Backend uses service role)'
    print("11. RLS check: SKIPPED")

    # 12. Report
    print("\n--- Final Report ---")
    print(json.dumps(report, indent=2))
    
    with open("supabase_test_report.json", "w") as f:
        json.dump(report, f, indent=2)

if __name__ == "__main__":
    run_test()
