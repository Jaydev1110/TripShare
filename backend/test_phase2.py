import httpx
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_flow():
    print("Testing with MOCK AUTH...")
    
    # No login needed for mock auth, but we might need a dummy header if the dependency expected it
    # But our mock dependency doesn't take arguments, so it won't check headers.
    headers = {} 
    
    with httpx.Client() as client:
        # 2. Create Group
        print("Creating group...")
        create_resp = client.post(f"{BASE_URL}/groups", json={"title": "Test Group"}, headers=headers)
        if create_resp.status_code != 200:
            print(f"Create group failed: {create_resp.text}")
            return
            
        group_data = create_resp.json()
        group_id = group_data["id"]
        group_code = group_data["code"]
        print(f"Group created: {group_data}")
        
        # 3. Get Group Details
        print("Getting group details...")
        details_resp = client.get(f"{BASE_URL}/groups/{group_id}", headers=headers)
        print(f"Details: {details_resp.json()}")
        
        # 4. Get QR Code
        print("Getting QR code...")
        qr_resp = client.get(f"{BASE_URL}/groups/{group_id}/qr", headers=headers)
        if qr_resp.status_code == 200:
            print("QR code received (binary data).")
        else:
            print(f"Failed to get QR code: {qr_resp.status_code}")

        # 5. Join Group
        print("Joining group...")
        join_resp = client.post(f"{BASE_URL}/groups/join", json={"code": group_code}, headers=headers)
        print(f"Join result: {join_resp.json()}")
        
        # 6. List Members
        print("Listing members...")
        members_resp = client.get(f"{BASE_URL}/groups/{group_id}/members", headers=headers)
        print(f"Members: {members_resp.json()}")
        
        # 7. Delete Group
        print("Deleting group...")
        delete_resp = client.delete(f"{BASE_URL}/groups/{group_id}", headers=headers)
        print(f"Delete result: {delete_resp.json()}")

if __name__ == "__main__":
    test_flow()
