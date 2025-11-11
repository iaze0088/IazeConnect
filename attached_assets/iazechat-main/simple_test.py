#!/usr/bin/env python3
"""
Simple test to check basic endpoints
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://suporte.help/api"
ADMIN_PASSWORD = "102030@ab"

async def simple_test():
    async with aiohttp.ClientSession() as session:
        # 1. Test health endpoint
        print("🏥 Testing health endpoint...")
        try:
            async with session.get(f"{BACKEND_URL}/health") as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check: {data}")
                else:
                    print(f"❌ Health check failed")
        except Exception as e:
            print(f"❌ Health check error: {e}")
        
        # 2. Login admin
        print("\n🔑 Testing admin login...")
        try:
            async with session.post(f"{BACKEND_URL}/auth/admin/login", json={"password": ADMIN_PASSWORD}) as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    token = data["token"]
                    print(f"✅ Login successful")
                    
                    # 3. Test config endpoint (should work)
                    print("\n⚙️ Testing config endpoint...")
                    headers = {"Authorization": f"Bearer {token}"}
                    async with session.get(f"{BACKEND_URL}/config", headers=headers) as config_response:
                        print(f"Config Status: {config_response.status}")
                        if config_response.status == 200:
                            config_data = await config_response.json()
                            print(f"✅ Config retrieved successfully")
                        else:
                            print(f"❌ Config failed")
                    
                    # 4. Test notices GET (should work)
                    print("\n📢 Testing notices GET...")
                    async with session.get(f"{BACKEND_URL}/notices", headers=headers) as notices_response:
                        print(f"Notices GET Status: {notices_response.status}")
                        if notices_response.status == 200:
                            notices_data = await notices_response.json()
                            print(f"✅ Notices GET successful: {len(notices_data)} notices")
                        else:
                            print(f"❌ Notices GET failed")
                    
                else:
                    print(f"❌ Login failed: {response.status}")
        except Exception as e:
            print(f"❌ Login error: {e}")

if __name__ == "__main__":
    asyncio.run(simple_test())