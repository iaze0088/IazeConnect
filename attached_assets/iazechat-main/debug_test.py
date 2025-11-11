#!/usr/bin/env python3
"""
Debug test to understand the 500 errors
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://suporte.help/api"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "102030@ab"

async def debug_test():
    async with aiohttp.ClientSession() as session:
        # 1. Login admin
        print("🔑 Testing admin login...")
        async with session.post(f"{BACKEND_URL}/auth/admin/login", json={"password": ADMIN_PASSWORD}) as response:
            if response.status == 200:
                data = await response.json()
                token = data["token"]
                print(f"✅ Login successful, token: {token[:50]}...")
            else:
                print(f"❌ Login failed: {response.status}")
                return
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Test resellers endpoint with detailed error handling
        print("\n🏢 Testing resellers endpoint...")
        try:
            async with session.post(f"{BACKEND_URL}/resellers", 
                                  json={"name": "Test", "email": "test@test.com", "password": "123"}, 
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
        
        # 3. Test departments endpoint
        print("\n🏛️ Testing departments endpoint...")
        try:
            async with session.post(f"{BACKEND_URL}/ai/departments", 
                                  json={"name": "Test Dept", "description": "Test"}, 
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
        
        # 4. Test notices endpoint
        print("\n📢 Testing notices endpoint...")
        try:
            async with session.post(f"{BACKEND_URL}/notices", 
                                  json={"title": "Test", "message": "Test message", "type": "info"}, 
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
    asyncio.run(debug_test())