import httpx
import sys
from PIL import Image
from io import BytesIO

BASE_URL = "http://127.0.0.1:8000"

def create_test_image():
    img = Image.new('RGB', (100, 100), color = 'red')
    buf = BytesIO()
    img.save(buf, format='JPEG')
    buf.seek(0)
    return buf.getvalue()

def test_flow():
    print("Testing Phase 3: Photo Upload...")
    
    headers = {} # Mock auth doesn't check headers
    
    with httpx.Client(timeout=30.0) as client:
        # 1. Create Group
        print("Creating group...")
        create_resp = client.post(f"{BASE_URL}/groups", json={"title": "Photo Test Group"}, headers=headers)
        if create_resp.status_code != 200:
            print(f"Create group failed: {create_resp.text}")
            return
        group_id = create_resp.json()["id"]
        print(f"Group created: {group_id}")
        
        # 2. Upload Photo
        print("Uploading photo...")
        img_bytes = create_test_image()
        files = {'file': ('test.jpg', img_bytes, 'image/jpeg')}
        data = {'group_id': group_id}
        
        upload_resp = client.post(f"{BASE_URL}/photos/upload", data=data, files=files, headers=headers)
        if upload_resp.status_code != 200:
            print(f"Upload failed: {upload_resp.text}")
            return
            
        photo_data = upload_resp.json()
        photo_id = photo_data["id"]
        print(f"Photo uploaded: {photo_data}")
        
        # 3. List Photos
        print("Listing photos...")
        list_resp = client.get(f"{BASE_URL}/photos/groups/{group_id}", headers=headers)
        print(f"Photos list: {list_resp.json()}")
        
        # 4. Get Signed URL
        print("Getting signed URL...")
        signed_resp = client.post(f"{BASE_URL}/photos/signed-urls", json={"photo_ids": [photo_id]}, headers=headers)
        print(f"Signed URLs: {signed_resp.json()}")
        
        # 5. Delete Photo
        print("Deleting photo...")
        delete_resp = client.delete(f"{BASE_URL}/photos/{photo_id}", headers=headers)
        print(f"Delete result: {delete_resp.json()}")
        
        # 6. Cleanup Group
        print("Deleting group...")
        client.delete(f"{BASE_URL}/groups/{group_id}", headers=headers)

if __name__ == "__main__":
    test_flow()
