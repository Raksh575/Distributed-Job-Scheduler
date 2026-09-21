import asyncio
import httpx
import json

async def audit_api():
    print("Fetching OpenAPI schema...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/openapi.json")
            response.raise_for_status()
            openapi = response.json()
        except Exception as e:
            print("Failed to fetch OpenAPI spec. Is the server running?")
            print(e)
            return

    paths = openapi.get("paths", {})
    total_endpoints = sum(len(methods) for methods in paths.values())
    print(f"Found {total_endpoints} endpoints across {len(paths)} paths.")
    
    # We will just print them out for now to see what we have
    for path, methods in paths.items():
        for method, details in methods.items():
            print(f"{method.upper()} {path} - {details.get('summary', 'No summary')}")
            
    print("\nAPI Audit Complete.")

if __name__ == "__main__":
    asyncio.run(audit_api())
