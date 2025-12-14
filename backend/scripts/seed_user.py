import httpx
import asyncio

async def seed_user():
    url = "http://localhost:8000/auth/signup"
    data = {
        "email": "user@tripshare.com",
        "password": "password123",
        "username": "DemoUser"
    }
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=data)
            if resp.status_code == 200:
                print("User created successfully.")
            else:
                print(f"User creation returned {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(seed_user())
