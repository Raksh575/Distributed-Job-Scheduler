import asyncio
import httpx

API_URL = "http://127.0.0.1:8000"

async def test_auth_flow():
    async with httpx.AsyncClient() as client:
        # Try to login
        print("Logging in...")
        login_data = {
            "username": "nithin200511@gmail.com",
            "password": "Password123!"  # Or whatever password Nithin created. Wait, let's look at the seed user if this fails, or Nithin's password.
        }
        # Wait, the password Nithin created was "Pymapass@111"! The previous prompt user request had:
        # "Pymapass@111 -> password"
        # So his password is "Pymapass@111"!
        login_data["password"] = "Pymapass@111"
        
        response = await client.post(
            f"{API_URL}/api/v1/auth/token",
            data={
                "username": login_data["username"],
                "password": login_data["password"]
            }
        )
        print("Login status:", response.status_code)
        if response.status_code != 200:
            print("Login response:", response.text)
            return
            
        token_data = response.json()
        access_token = token_data["access_token"]
        print("Access token received successfully.")
        
        # Call /users/me
        print("Calling /users/me...")
        headers = {"Authorization": f"Bearer {access_token}"}
        response_me = await client.get(f"{API_URL}/api/v1/users/me", headers=headers)
        print("Me status:", response_me.status_code)
        print("Me response:", response_me.json() if response_me.status_code == 200 else response_me.text)

if __name__ == "__main__":
    asyncio.run(test_auth_flow())
