import asyncio
import httpx
import uuid
from typing import Dict, Any

API_URL = "http://localhost:8000/api/v1"

async def test_api_flow():
    print("Starting API E2E Flow Audit...")
    
    unique_suffix = str(uuid.uuid4())[:8]
    email = f"test_{unique_suffix}@example.com"
    password = "Pymapass@111"
    
    headers = {"Content-Type": "application/json"}
    
    async with httpx.AsyncClient(base_url=API_URL, headers=headers) as client:
        # 1. Register
        print(f"1. Registering user: {email}")
        res = await client.post("/auth/register", json={
            "email": email,
            "password": password,
            "full_name": "Test User"
        })
        if res.status_code != 201:
            print(f"[FAIL] Registration failed: {res.status_code} {res.text}")
            return
        print("[OK] Registration successful.")
        
        # 2. Login
        print("2. Logging in...")
        res = await client.post("/auth/token", data={
            "username": email,
            "password": password
        }, headers={"Content-Type": "application/x-www-form-urlencoded"})
        
        if res.status_code != 200:
            print(f"[FAIL] Login failed: {res.status_code} {res.text}")
            return
        
        tokens = res.json()
        token = tokens["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}
        client.headers.update(auth_headers)
        print("[OK] Login successful.")
        
        # 3. Create Org
        print("3. Creating Organization...")
        res = await client.post("/organizations", json={
            "name": f"Test Org {unique_suffix}",
            "slug": f"test-org-{unique_suffix}",
            "description": "A test organization"
        })
        if res.status_code != 201:
            print(f"[FAIL] Create Org failed: {res.status_code} {res.text}")
            return
            
        org = res.json()
        org_id = org["id"]
        print(f"[OK] Organization created: {org_id}")
        
        # 3.5 Re-login to get updated token with new org roles
        print("3.5 Re-fetching token to include new org role...")
        res = await client.post("/auth/token", data={
            "username": email,
            "password": password
        }, headers={"Content-Type": "application/x-www-form-urlencoded"})
        if res.status_code == 200:
            tokens = res.json()
            token = tokens["access_token"]
            auth_headers = {"Authorization": f"Bearer {token}"}
            client.headers.update(auth_headers)
        else:
            print(f"[FAIL] Token re-fetch failed: {res.status_code} {res.text}")
            return
        
        # 4. List Orgs (via users/me/organizations)
        print("4. Listing Organizations...")
        res = await client.get("/users/me/organizations")
        if res.status_code != 200:
            print(f"[FAIL] List Orgs failed: {res.status_code} {res.text}")
        else:
            print("[OK] List Orgs successful.")
            
        # 5. Create Project
        print("5. Creating Project...")
        res = await client.post(f"/organizations/{org_id}/projects", json={
            "name": f"Test Project {unique_suffix}",
            "slug": f"test-proj-{unique_suffix}"
        })
        if res.status_code not in (200, 201):
            print(f"[FAIL] Create Project failed: {res.status_code} {res.text}")
            return
            
        project = res.json()
        project_id = project["id"]
        print(f"[OK] Project created: {project_id}")
        
        # 6. Create Queue
        print("6. Creating Queue...")
        res = await client.post(f"/organizations/{org_id}/projects/{project_id}/queues", json={
            "name": f"test-queue-{unique_suffix}",
            "priority": 1,
            "concurrency_limit": 10
        })
        if res.status_code not in (200, 201):
            print(f"[FAIL] Create Queue failed: {res.status_code} {res.text}")
            return
            
        queue = res.json()
        queue_id = queue["id"]
        print(f"[OK] Queue created: {queue_id}")
        
        # 7. Submit Job
        print("7. Submitting Job...")
        res = await client.post(f"/organizations/{org_id}/queues/{queue_id}/jobs", json={
            "name": "Test Job 1",
            "payload": {"key": "value"},
            "priority": 5,
            "max_retries": 3
        })
        if res.status_code not in (200, 201, 202):
            print(f"[FAIL] Submit Job failed: {res.status_code} {res.text}")
            # we continue even if job fails
        else:
            job = res.json()
            print(f"[OK] Job submitted: {job['id']}")
            
        # 8. Dashboard metrics
        print("8. Fetching Dashboard Metrics...")
        res = await client.get(f"/organizations/{org_id}/dashboard-metrics")
        if res.status_code != 200:
            print(f"[FAIL] Dashboard Metrics failed: {res.status_code} {res.text}")
        else:
            print("[OK] Dashboard Metrics successful.")
            
    print("API E2E Flow Audit Complete.")

if __name__ == "__main__":
    asyncio.run(test_api_flow())
