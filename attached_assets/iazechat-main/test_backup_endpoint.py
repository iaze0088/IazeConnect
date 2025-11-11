#!/usr/bin/env python3
"""
Test backup endpoint with correct path
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://suporte.help"  # No /api suffix
ADMIN_PASSWORD = "102030@ab"

async def test_backup():
    async with aiohttp.ClientSession() as session:
        # Login admin
        print("🔑 Testing admin login...")
        async with session.post(f"{BACKEND_URL}/api/auth/admin/login", json={"password": ADMIN_PASSWORD}) as response:
            if response.status == 200:
                data = await response.json()
                token = data["token"]
                print(f"✅ Login successful")
            else:
                print(f"❌ Login failed: {response.status}")
                return
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test backup endpoint with correct path
        print("\n💾 Testing backup endpoint...")
        try:
            # Try the full path as defined in backup_routes.py
            async with session.post(f"{BACKEND_URL}/api/admin/backup/create", 
                                  json={"backup_type": "database"}, 
                                  headers=headers) as response:
                print(f"Status: {response.status}")
                print(f"Content-Type: {response.headers.get('content-type')}")
                
                if response.headers.get('content-type', '').startswith('application/json'):
                    data = await response.json()
                    print(f"JSON Response: {json.dumps(data, indent=2)}")
                else:
                    text = await response.text()
                    print(f"Text Response: {text[:500]}...")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_backup())