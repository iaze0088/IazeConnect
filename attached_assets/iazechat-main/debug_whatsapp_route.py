#!/usr/bin/env python3
"""
Debug WhatsApp route access
"""

import asyncio
import httpx
import json

async def debug_route():
    client = httpx.AsyncClient(timeout=30.0)
    
    try:
        # Login
        print("🔐 Admin Login...")
        response = await client.post(
            "https://suporte.help/api/auth/admin/login",
            json={"email": "admin@admin.com", "password": "102030@ab"}
        )
        
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            return
        
        token = response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login successful")
        
        # Test list connections first
        print(f"\n📋 Testing list connections...")
        response = await client.get(
            "https://suporte.help/api/whatsapp/connections",
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            connections = response.json()
            print(f"✅ Found {len(connections)} connections")
            for conn in connections:
                print(f"   - ID: {conn.get('id')}")
                print(f"     Name: {conn.get('name')}")
                print(f"     Status: {conn.get('status')}")
                print(f"     Reseller ID: {conn.get('reseller_id')}")
        else:
            print(f"❌ List failed: {response.text}")
        
    finally:
        await client.aclose()

if __name__ == "__main__":
    asyncio.run(debug_route())