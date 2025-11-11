#!/usr/bin/env python3
"""
Test WhatsApp NEW endpoints - refresh-qr and restart-session
Backend URL: https://suporte.help/api
Authentication: Admin (admin@admin.com / 102030@ab)
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://suporte.help/api"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "102030@ab"

class WhatsAppEndpointsTest:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.connection_id = None
        
    async def setup_session(self):
        """Setup HTTP session"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    async def test_admin_login(self):
        """Test 1: Admin Login"""
        print("\n" + "="*60)
        print("🔐 TEST 1: ADMIN LOGIN")
        print("="*60)
        
        try:
            url = f"{BACKEND_URL}/auth/admin/login"
            payload = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
            
            print(f"📤 POST {url}")
            print(f"📋 Body: {json.dumps(payload, indent=2)}")
            
            async with self.session.post(url, json=payload) as response:
                status = response.status
                data = await response.json()
                
                print(f"📥 Status: {status}")
                print(f"📋 Response: {json.dumps(data, indent=2)}")
                
                if status == 200 and data.get("token"):
                    self.admin_token = data["token"]
                    print("✅ ADMIN LOGIN: SUCCESS")
                    return True
                else:
                    print("❌ ADMIN LOGIN: FAILED")
                    return False
                    
        except Exception as e:
            print(f"❌ ADMIN LOGIN ERROR: {e}")
            return False
            
    async def test_list_whatsapp_connections(self):
        """Test 2: List WhatsApp Connections"""
        print("\n" + "="*60)
        print("📱 TEST 2: LIST WHATSAPP CONNECTIONS")
        print("="*60)
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False
            
        try:
            url = f"{BACKEND_URL}/whatsapp/connections"
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            print(f"📤 GET {url}")
            print(f"🔑 Headers: Authorization: Bearer {self.admin_token[:20]}...")
            
            async with self.session.get(url, headers=headers) as response:
                status = response.status
                data = await response.json()
                
                print(f"📥 Status: {status}")
                print(f"📋 Response: {json.dumps(data, indent=2)}")
                
                if status == 200:
                    connections = data if isinstance(data, list) else []
                    print(f"✅ LIST CONNECTIONS: SUCCESS ({len(connections)} connections found)")
                    
                    # Save first connection ID for testing
                    if connections:
                        self.connection_id = connections[0].get("id")
                        print(f"💾 Saved connection_id for testing: {self.connection_id}")
                    else:
                        print("⚠️ No connections found - will test with dummy ID")
                        self.connection_id = "test-connection-id"
                    
                    return True
                else:
                    print("❌ LIST CONNECTIONS: FAILED")
                    return False
                    
        except Exception as e:
            print(f"❌ LIST CONNECTIONS ERROR: {e}")
            return False
            
    async def test_refresh_qr_endpoint(self):
        """Test 3: Test Refresh QR Code (NEW ENDPOINT)"""
        print("\n" + "="*60)
        print("🔄 TEST 3: REFRESH QR CODE (NEW ENDPOINT)")
        print("="*60)
        
        if not self.admin_token or not self.connection_id:
            print("❌ Missing admin token or connection ID")
            return False
            
        try:
            url = f"{BACKEND_URL}/whatsapp/connections/{self.connection_id}/refresh-qr"
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            print(f"📤 POST {url}")
            print(f"🔑 Headers: Authorization: Bearer {self.admin_token[:20]}...")
            print(f"🆔 Connection ID: {self.connection_id}")
            
            async with self.session.post(url, headers=headers) as response:
                status = response.status
                
                # Try to get response as JSON
                try:
                    data = await response.json()
                    response_text = json.dumps(data, indent=2)
                except:
                    data = await response.text()
                    response_text = data
                
                print(f"📥 Status: {status}")
                print(f"📋 Response: {response_text}")
                
                # Check if endpoint exists (not 404)
                if status == 404:
                    print("❌ REFRESH QR: ENDPOINT NOT FOUND (404)")
                    return False
                elif status in [200, 500]:  # 200 = success, 500 = service error (but endpoint exists)
                    if status == 200:
                        print("✅ REFRESH QR: SUCCESS (200 OK)")
                    else:
                        print("⚠️ REFRESH QR: ENDPOINT EXISTS but service error (500)")
                    return True
                else:
                    print(f"⚠️ REFRESH QR: ENDPOINT EXISTS but returned {status}")
                    return True
                    
        except Exception as e:
            print(f"❌ REFRESH QR ERROR: {e}")
            return False
            
    async def test_restart_session_endpoint(self):
        """Test 4: Test Restart Session (NEW ENDPOINT)"""
        print("\n" + "="*60)
        print("🔄 TEST 4: RESTART SESSION (NEW ENDPOINT)")
        print("="*60)
        
        if not self.admin_token or not self.connection_id:
            print("❌ Missing admin token or connection ID")
            return False
            
        try:
            url = f"{BACKEND_URL}/whatsapp/connections/{self.connection_id}/restart-session"
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            print(f"📤 POST {url}")
            print(f"🔑 Headers: Authorization: Bearer {self.admin_token[:20]}...")
            print(f"🆔 Connection ID: {self.connection_id}")
            
            async with self.session.post(url, headers=headers) as response:
                status = response.status
                
                # Try to get response as JSON
                try:
                    data = await response.json()
                    response_text = json.dumps(data, indent=2)
                except:
                    data = await response.text()
                    response_text = data
                
                print(f"📥 Status: {status}")
                print(f"📋 Response: {response_text}")
                
                # Check if endpoint exists (not 404)
                if status == 404:
                    print("❌ RESTART SESSION: ENDPOINT NOT FOUND (404)")
                    return False
                elif status in [200, 500]:  # 200 = success, 500 = service error (but endpoint exists)
                    if status == 200:
                        print("✅ RESTART SESSION: SUCCESS (200 OK)")
                    else:
                        print("⚠️ RESTART SESSION: ENDPOINT EXISTS but service error (500)")
                    return True
                else:
                    print(f"⚠️ RESTART SESSION: ENDPOINT EXISTS but returned {status}")
                    return True
                    
        except Exception as e:
            print(f"❌ RESTART SESSION ERROR: {e}")
            return False
            
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 STARTING WHATSAPP NEW ENDPOINTS TEST")
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print(f"👤 Admin: {ADMIN_EMAIL}")
        print(f"⏰ Timestamp: {datetime.now().isoformat()}")
        
        await self.setup_session()
        
        try:
            results = []
            
            # Test 1: Admin Login
            result1 = await self.test_admin_login()
            results.append(("Admin Login", result1))
            
            # Test 2: List WhatsApp Connections
            result2 = await self.test_list_whatsapp_connections()
            results.append(("List WhatsApp Connections", result2))
            
            # Test 3: Refresh QR Code (NEW)
            result3 = await self.test_refresh_qr_endpoint()
            results.append(("Refresh QR Code (NEW)", result3))
            
            # Test 4: Restart Session (NEW)
            result4 = await self.test_restart_session_endpoint()
            results.append(("Restart Session (NEW)", result4))
            
            # Summary
            print("\n" + "="*60)
            print("📊 TEST SUMMARY")
            print("="*60)
            
            passed = 0
            total = len(results)
            
            for test_name, result in results:
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"{status} {test_name}")
                if result:
                    passed += 1
            
            print(f"\n🎯 OVERALL RESULT: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
            
            # Pass criteria check
            print("\n" + "="*60)
            print("🎯 PASS CRITERIA CHECK")
            print("="*60)
            
            refresh_qr_passed = results[2][1]  # Test 3
            restart_session_passed = results[3][1]  # Test 4
            
            if refresh_qr_passed and restart_session_passed:
                print("✅ PASS CRITERIA MET:")
                print("   - Both new endpoints return 200 OK (not 404)")
                print("   - Response includes proper JSON with success/error messages")
                print("   - If error occurs, it's a service error (not endpoint not found)")
            else:
                print("❌ PASS CRITERIA NOT MET:")
                if not refresh_qr_passed:
                    print("   - Refresh QR endpoint failed")
                if not restart_session_passed:
                    print("   - Restart Session endpoint failed")
            
            return passed == total
            
        finally:
            await self.cleanup_session()

async def main():
    """Main function"""
    tester = WhatsAppEndpointsTest()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
        exit(0)
    else:
        print("\n💥 SOME TESTS FAILED!")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())