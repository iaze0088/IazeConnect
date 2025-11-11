#!/usr/bin/env python3
"""
WhatsApp WPPConnect Integration Test
Tests all WhatsApp endpoints according to review request
"""

import asyncio
import httpx
import json
import sys
from datetime import datetime

# Test Configuration
BACKEND_URL = "https://suporte.help/api"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "102030@ab"
WPPCONNECT_SERVICE_URL = "http://151.243.218.223:21465"
WPPCONNECT_SECRET = "THISISMYSECURETOKEN"

class WhatsAppWPPConnectTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.admin_token = None
        self.test_results = []
        
    async def log_test(self, test_name: str, success: bool, details: str, response_data=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": timestamp,
            "response_data": response_data
        }
        
        self.test_results.append(result)
        print(f"[{timestamp}] {status} {test_name}")
        print(f"         {details}")
        
        if response_data and not success:
            print(f"         Response: {json.dumps(response_data, indent=2)[:300]}")
        print()
    
    async def test_admin_login(self):
        """Test 1: Admin Login"""
        try:
            response = await self.client.post(
                f"{BACKEND_URL}/auth/admin/login",
                json={
                    "email": ADMIN_EMAIL,
                    "password": ADMIN_PASSWORD
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("token")
                
                await self.log_test(
                    "Admin Login",
                    True,
                    f"Login successful. Token received: {self.admin_token[:20]}...",
                    {"user_type": data.get("user_type"), "user_data": data.get("user_data")}
                )
                return True
            else:
                await self.log_test(
                    "Admin Login",
                    False,
                    f"Login failed with status {response.status_code}",
                    response.json() if response.content else None
                )
                return False
                
        except Exception as e:
            await self.log_test(
                "Admin Login",
                False,
                f"Exception occurred: {str(e)}"
            )
            return False
    
    async def test_list_whatsapp_connections(self):
        """Test 2: List WhatsApp Connections"""
        if not self.admin_token:
            await self.log_test(
                "List WhatsApp Connections",
                False,
                "No admin token available"
            )
            return False
        
        try:
            response = await self.client.get(
                f"{BACKEND_URL}/whatsapp/connections",
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                await self.log_test(
                    "List WhatsApp Connections",
                    True,
                    f"Successfully retrieved {len(data)} connections",
                    {"connections_count": len(data), "sample": data[:2] if data else []}
                )
                return True
            else:
                await self.log_test(
                    "List WhatsApp Connections",
                    False,
                    f"Failed with status {response.status_code}",
                    response.json() if response.content else None
                )
                return False
                
        except Exception as e:
            await self.log_test(
                "List WhatsApp Connections",
                False,
                f"Exception occurred: {str(e)}"
            )
            return False
    
    async def test_create_whatsapp_connection(self):
        """Test 3: Create WhatsApp Connection"""
        if not self.admin_token:
            await self.log_test(
                "Create WhatsApp Connection",
                False,
                "No admin token available"
            )
            return False
        
        try:
            test_connection_name = f"Test Connection {datetime.now().strftime('%H%M%S')}"
            
            response = await self.client.post(
                f"{BACKEND_URL}/whatsapp/connections",
                headers={"Authorization": f"Bearer {self.admin_token}"},
                json={"name": test_connection_name}
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                
                # Check if we got a QR code or error message
                has_qr = bool(data.get("qr_code_base64"))
                connection_id = data.get("id")
                status = data.get("status")
                
                await self.log_test(
                    "Create WhatsApp Connection",
                    True,
                    f"Connection created successfully. ID: {connection_id}, Status: {status}, Has QR: {has_qr}",
                    {
                        "connection_id": connection_id,
                        "name": data.get("name"),
                        "status": status,
                        "has_qr_code": has_qr,
                        "instance_name": data.get("instance_name")
                    }
                )
                return True
            else:
                error_data = response.json() if response.content else {}
                await self.log_test(
                    "Create WhatsApp Connection",
                    False,
                    f"Failed with status {response.status_code}. Error: {error_data.get('detail', 'Unknown error')}",
                    error_data
                )
                return False
                
        except Exception as e:
            await self.log_test(
                "Create WhatsApp Connection",
                False,
                f"Exception occurred: {str(e)}"
            )
            return False
    
    async def test_wppconnect_service_accessibility(self):
        """Test 4: Check WPPConnect Service Accessibility"""
        try:
            # Test basic connectivity to WPPConnect service
            test_session = f"test_session_{datetime.now().strftime('%H%M%S')}"
            url = f"{WPPCONNECT_SERVICE_URL}/api/{test_session}/{WPPCONNECT_SECRET}/generate-token"
            
            response = await self.client.post(url)
            
            if response.status_code in [200, 201]:
                data = response.json()
                await self.log_test(
                    "WPPConnect Service Accessibility",
                    True,
                    f"WPPConnect service is accessible. Token generation successful.",
                    {"status_code": response.status_code, "has_token": bool(data.get("token"))}
                )
                return True
            elif response.status_code == 404:
                await self.log_test(
                    "WPPConnect Service Accessibility",
                    False,
                    f"WPPConnect service returned 404 - endpoint not found or service not running",
                    {"status_code": response.status_code, "response": response.text[:200]}
                )
                return False
            else:
                await self.log_test(
                    "WPPConnect Service Accessibility",
                    False,
                    f"WPPConnect service returned status {response.status_code}",
                    {"status_code": response.status_code, "response": response.text[:200]}
                )
                return False
                
        except httpx.ConnectError as e:
            await self.log_test(
                "WPPConnect Service Accessibility",
                False,
                f"Cannot connect to WPPConnect service: {str(e)}"
            )
            return False
        except Exception as e:
            await self.log_test(
                "WPPConnect Service Accessibility",
                False,
                f"Exception occurred: {str(e)}"
            )
            return False
    
    async def test_whatsapp_routes_availability(self):
        """Test 5: Check if WhatsApp routes are loaded"""
        try:
            # Test the no-auth endpoint to verify routes are loaded
            response = await self.client.get(f"{BACKEND_URL}/whatsapp/test-no-auth")
            
            if response.status_code == 200:
                data = response.json()
                await self.log_test(
                    "WhatsApp Routes Availability",
                    True,
                    f"WhatsApp routes are loaded and accessible",
                    {
                        "status": data.get("status"),
                        "message": data.get("message"),
                        "routes_count": len(data.get("registered_routes", []))
                    }
                )
                return True
            else:
                await self.log_test(
                    "WhatsApp Routes Availability",
                    False,
                    f"WhatsApp routes test endpoint failed with status {response.status_code}",
                    response.json() if response.content else None
                )
                return False
                
        except Exception as e:
            await self.log_test(
                "WhatsApp Routes Availability",
                False,
                f"Exception occurred: {str(e)}"
            )
            return False
    
    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("🧪 WHATSAPP WPPCONNECT INTEGRATION TEST")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"WPPConnect Service: {WPPCONNECT_SERVICE_URL}")
        print(f"Admin Credentials: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        print("=" * 60)
        print()
        
        # Run tests in order
        tests = [
            self.test_admin_login,
            self.test_whatsapp_routes_availability,
            self.test_wppconnect_service_accessibility,
            self.test_list_whatsapp_connections,
            self.test_create_whatsapp_connection
        ]
        
        for test in tests:
            await test()
        
        # Summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        print()
        
        # Detailed results
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        print()
        print("=" * 60)
        
        if passed == total:
            print("🎉 ALL TESTS PASSED!")
        else:
            print("⚠️  SOME TESTS FAILED - Check details above")
        
        print("=" * 60)
        
        await self.client.aclose()
        return passed == total

async def main():
    """Main test function"""
    tester = WhatsAppWPPConnectTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())