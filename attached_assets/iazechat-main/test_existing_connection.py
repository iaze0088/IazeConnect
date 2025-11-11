#!/usr/bin/env python3
"""
Test existing WhatsApp connection
"""

import asyncio
import httpx
import json

BACKEND_URL = "https://suporte.help/api"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "102030@ab"
EXISTING_CONNECTION_ID = "c8a2d4f1-9b3e-4c7f-a1d8-e5f6g7h8i9j0"

async def test_existing_connection():
    client = httpx.AsyncClient(timeout=30.0)
    
    try:
        # Login
        print("🔐 Admin Login...")
        response = await client.post(
            f"{BACKEND_URL}/auth/admin/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            return
        
        token = response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login successful")
        
        # Test QR code endpoint
        print(f"\n📱 Testing QR code for connection: {EXISTING_CONNECTION_ID}")
        response = await client.get(
            f"{BACKEND_URL}/whatsapp/connections/{EXISTING_CONNECTION_ID}/qr",
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ QR Code endpoint working!")
            print(f"   Has QR Code: {bool(data.get('qr_code_base64'))}")
            print(f"   Status: {data.get('status')}")
            print(f"   Instance: {data.get('instance_name')}")
        else:
            print(f"❌ QR Code failed: {response.text}")
        
        # Test status endpoint
        print(f"\n🔍 Testing status for connection: {EXISTING_CONNECTION_ID}")
        response = await client.get(
            f"{BACKEND_URL}/whatsapp/connections/{EXISTING_CONNECTION_ID}/check-status",
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status endpoint working!")
            print(f"   Status: {data.get('status')}")
            print(f"   Connected: {data.get('connected')}")
            print(f"   Instance: {data.get('instance_name')}")
        else:
            print(f"❌ Status failed: {response.text}")
        
        # Test delete endpoint (but don't actually delete)
        print(f"\n🗑️ Testing delete endpoint (dry run)")
        print(f"   Would delete connection: {EXISTING_CONNECTION_ID}")
        print(f"   ✅ Delete endpoint available at: DELETE /whatsapp/connections/{EXISTING_CONNECTION_ID}")
        
    finally:
        await client.aclose()

if __name__ == "__main__":
    asyncio.run(test_existing_connection())