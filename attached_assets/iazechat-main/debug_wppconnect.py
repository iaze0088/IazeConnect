#!/usr/bin/env python3
"""
Debug WPPConnect Service
"""

import asyncio
import sys
import os
sys.path.append('/app/backend')

from whatsapp_service_wppconnect_v2 import wppconnect_service

async def test_wppconnect():
    print("🔧 Testing WPPConnect Service")
    print("=" * 50)
    
    # Test session creation
    session_name = "debug_test_session"
    
    print(f"Creating session: {session_name}")
    result = await wppconnect_service.create_session(session_name)
    
    print(f"Result: {result}")
    
    if result.get("success"):
        print("✅ Session created successfully!")
        print(f"Token: {result.get('token')}")
        print(f"QR Code available: {bool(result.get('qr_code'))}")
    else:
        print("❌ Session creation failed!")
        print(f"Error: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(test_wppconnect())