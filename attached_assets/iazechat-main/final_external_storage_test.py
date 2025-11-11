#!/usr/bin/env python3
"""
🧪 TESTE FINAL: Verificação completa do External Storage
"""

import asyncio
import aiohttp
import json
import os
from pathlib import Path

BACKEND_URL = "https://wppconnect-fix.preview.emergentagent.com"
ADMIN_PASSWORD = "102030@ab"

async def quick_test():
    """Teste rápido para confirmar external storage"""
    print("🧪 TESTE FINAL: EXTERNAL STORAGE VALIDATION")
    print("=" * 50)
    
    # Login
    async with aiohttp.ClientSession() as session:
        # Admin login
        async with session.post(
            f"{BACKEND_URL}/api/auth/admin/login",
            json={"password": ADMIN_PASSWORD}
        ) as response:
            if response.status != 200:
                print("❌ Login failed")
                return
            data = await response.json()
            token = data["token"]
            print("✅ Admin login successful")
        
        # Test upload
        test_content = "Final test for external storage validation"
        data = aiohttp.FormData()
        data.add_field('file', 
                      test_content.encode(),
                      filename="final_test.txt",
                      content_type="text/plain")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        async with session.post(
            f"{BACKEND_URL}/api/upload",
            data=data,
            headers=headers
        ) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Upload successful:")
                print(f"   External: {result.get('external')}")
                print(f"   URL: {result.get('url')}")
                print(f"   Filename: {result.get('filename')}")
                
                # Verify no local files
                uploads_dir = Path("/data/uploads")
                if uploads_dir.exists():
                    recent_files = []
                    import time
                    current_time = time.time()
                    for file_path in uploads_dir.glob("*"):
                        if file_path.is_file():
                            file_age = current_time - file_path.stat().st_mtime
                            if file_age < 60:  # 1 minute
                                recent_files.append(file_path.name)
                    
                    if recent_files:
                        print(f"⚠️ Recent local files found: {recent_files}")
                    else:
                        print("✅ No recent local files (external storage working)")
                
                # Test download
                async with session.get(result.get('url')) as dl_response:
                    if dl_response.status == 200:
                        content = await dl_response.text()
                        if content == test_content:
                            print("✅ Download verification successful")
                        else:
                            print("❌ Download content mismatch")
                    else:
                        print(f"❌ Download failed: {dl_response.status}")
            else:
                print(f"❌ Upload failed: {response.status}")

if __name__ == "__main__":
    asyncio.run(quick_test())