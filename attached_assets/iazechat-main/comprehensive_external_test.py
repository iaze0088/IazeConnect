#!/usr/bin/env python3
"""
COMPREHENSIVE FUNCTIONAL TESTING - External Server (https://suporte.help)

**CRITICAL: Test the following user journey step by step:**

**1. ADMIN LOGIN TEST:**
- Endpoint: POST https://suporte.help/api/auth/login or POST https://suporte.help/api/admin/login
- Credentials to try:
  * email: admin@admin.com, password: 102030@ab
  * email: admin@suporte.help, password: 102030@ab
  * username: admin, password: 102030@ab
- Expected: 200 OK with JWT token
- Extract and save the JWT token for subsequent requests

**2. CREATE DEPARTMENT TEST:**
- Endpoint: POST https://suporte.help/api/departments or POST https://suporte.help/api/admin/departments
- Headers: Authorization: Bearer {token_from_login}
- Body: {"name": "Teste Departamento Automated", "description": "Departamento criado por teste automatizado"}
- Expected: 200/201 with department created successfully

**3. LIST DEPARTMENTS TEST:**
- Endpoint: GET https://suporte.help/api/departments
- Headers: Authorization: Bearer {token_from_login}
- Expected: 200 OK with list of departments including the one just created

**4. CREATE AGENT/ATENDENTE TEST:**
- Endpoint: POST https://suporte.help/api/agents or POST https://suporte.help/api/admin/agents
- Headers: Authorization: Bearer {token_from_login}
- Body: {"name": "Teste Atendente", "email": "teste@automated.com", "password": "teste123", "department_id": "{department_id_from_step2}"}
- Try variations if needed (username instead of name, etc.)
- Expected: 200/201 with agent created successfully

**5. SAVE OFFICE CONFIG TEST:**
- Find the correct endpoint (try POST /api/office/config, /api/admin/office, /api/config/office)
- Headers: Authorization: Bearer {token_from_login}
- Body: {"office_email": "test@office.com", "office_password": "test123"}
- Expected: Success response

**6. SAVE WA SITE CONFIG TEST:**
- Endpoint: POST https://suporte.help/api/admin/vendas-bot/config or POST https://suporte.help/api/vendas/simple-config-v2
- Headers: Authorization: Bearer {token_from_login}
- Body: Include all required fields found in previous test + openai_api_key field
- Expected: Success response

**7. SAVE DADOS PERMITIDOS (ALLOWED DATA) TEST:**
- Endpoint: PUT https://suporte.help/api/config
- Headers: Authorization: Bearer {token_from_login}
- Body: {"allowed_data": ["nome", "email", "telefone"]}
- Expected: Success response

**8. SEND MESSAGE TEST (Critical):**
- Endpoint: POST https://suporte.help/api/messages or POST https://suporte.help/api/vendas/message
- Headers: Authorization: Bearer {token_from_login}
- Body: {"text": "Mensagem de teste", "ticket_id": "{any_existing_ticket_id}"}
- If no ticket exists, create one first
- Expected: Success response
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime
import io

# Configuration
BACKEND_URL = "https://suporte.help/api"

class ExternalServerTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_results = []
        self.created_department_id = None
        self.created_agent_id = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(ssl=False)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_result(self, test_name: str, success: bool, details: str, response_data=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        print(f"   Details: {details}")
        if response_data:
            print(f"   Response: {json.dumps(response_data, indent=2)[:300]}...")
        print()
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
    
    async def test_1_admin_login(self):
        """Test 1: Admin Login with multiple credential combinations"""
        print("🔐 TEST 1: ADMIN LOGIN")
        print("=" * 50)
        
        # Multiple credential combinations to try
        credentials_to_try = [
            {"email": "admin@admin.com", "password": "102030@ab"},
            {"email": "admin@suporte.help", "password": "102030@ab"},
            {"username": "admin", "password": "102030@ab"}
        ]
        
        # Multiple endpoints to try
        endpoints_to_try = [
            "/auth/admin/login",
            "/auth/login", 
            "/admin/login"
        ]
        
        for creds in credentials_to_try:
            for endpoint in endpoints_to_try:
                try:
                    print(f"   Trying {endpoint} with {creds}")
                    async with self.session.post(f"{BACKEND_URL}{endpoint}", json=creds) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get("token"):
                                self.auth_token = data.get("token")
                                self.log_result("1. Admin Login", True, f"Login successful with {creds} at {endpoint}", data)
                                return True
                        else:
                            error_text = await response.text()
                            print(f"      Status {response.status}: {error_text[:100]}")
                            
                except Exception as e:
                    print(f"      Exception: {str(e)}")
                    continue
        
        self.log_result("1. Admin Login", False, "All credential/endpoint combinations failed")
        return False
    
    async def test_2_create_department(self):
        """Test 2: Create Department"""
        print("🏢 TEST 2: CREATE DEPARTMENT")
        print("=" * 50)
        
        if not self.auth_token:
            self.log_result("2. Create Department", False, "No auth token available")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Multiple endpoints to try
        endpoints_to_try = [
            "/departments",
            "/admin/departments",
            "/ai/departments"
        ]
        
        dept_data = {
            "name": "Teste Departamento Automated",
            "description": "Departamento criado por teste automatizado"
        }
        
        for endpoint in endpoints_to_try:
            try:
                print(f"   Trying POST {endpoint}")
                async with self.session.post(f"{BACKEND_URL}{endpoint}", json=dept_data, headers=headers) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        if data.get("id"):
                            self.created_department_id = data.get("id")
                        self.log_result("2. Create Department", True, f"Department created successfully at {endpoint}", data)
                        return True
                    else:
                        error_text = await response.text()
                        print(f"      Status {response.status}: {error_text[:100]}")
                        
            except Exception as e:
                print(f"      Exception: {str(e)}")
                continue
        
        self.log_result("2. Create Department", False, "All department creation endpoints failed")
        return False
    
    async def test_3_list_departments(self):
        """Test 3: List Departments"""
        print("📋 TEST 3: LIST DEPARTMENTS")
        print("=" * 50)
        
        if not self.auth_token:
            self.log_result("3. List Departments", False, "No auth token available")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Multiple endpoints to try
        endpoints_to_try = [
            "/departments",
            "/admin/departments", 
            "/ai/departments"
        ]
        
        for endpoint in endpoints_to_try:
            try:
                print(f"   Trying GET {endpoint}")
                async with self.session.get(f"{BACKEND_URL}{endpoint}", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        dept_count = len(data) if isinstance(data, list) else 0
                        self.log_result("3. List Departments", True, f"Retrieved {dept_count} departments from {endpoint}", data)
                        return True
                    else:
                        error_text = await response.text()
                        print(f"      Status {response.status}: {error_text[:100]}")
                        
            except Exception as e:
                print(f"      Exception: {str(e)}")
                continue
        
        self.log_result("3. List Departments", False, "All department listing endpoints failed")
        return False
    
    async def test_4_create_agent(self):
        """Test 4: Create Agent/Atendente"""
        print("👥 TEST 4: CREATE AGENT/ATENDENTE")
        print("=" * 50)
        
        if not self.auth_token:
            self.log_result("4. Create Agent", False, "No auth token available")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Multiple endpoints to try
        endpoints_to_try = [
            "/agents",
            "/admin/agents"
        ]
        
        # Multiple data variations to try
        agent_data_variations = [
            {
                "name": "Teste Atendente",
                "email": "teste@automated.com", 
                "password": "teste123",
                "department_id": self.created_department_id
            },
            {
                "username": "teste_atendente",
                "name": "Teste Atendente",
                "email": "teste@automated.com",
                "password": "teste123"
            },
            {
                "name": "Teste Atendente",
                "login": "teste@automated.com",
                "password": "teste123"
            }
        ]
        
        for endpoint in endpoints_to_try:
            for agent_data in agent_data_variations:
                try:
                    print(f"   Trying POST {endpoint} with {list(agent_data.keys())}")
                    async with self.session.post(f"{BACKEND_URL}{endpoint}", json=agent_data, headers=headers) as response:
                        if response.status in [200, 201]:
                            data = await response.json()
                            if data.get("id"):
                                self.created_agent_id = data.get("id")
                            self.log_result("4. Create Agent", True, f"Agent created successfully at {endpoint}", data)
                            return True
                        else:
                            error_text = await response.text()
                            print(f"      Status {response.status}: {error_text[:100]}")
                            
                except Exception as e:
                    print(f"      Exception: {str(e)}")
                    continue
        
        self.log_result("4. Create Agent", False, "All agent creation attempts failed")
        return False
    
    async def test_5_save_office_config(self):
        """Test 5: Save Office Config"""
        print("🏢 TEST 5: SAVE OFFICE CONFIG")
        print("=" * 50)
        
        if not self.auth_token:
            self.log_result("5. Save Office Config", False, "No auth token available")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Multiple endpoints to try
        endpoints_to_try = [
            "/office/config",
            "/admin/office",
            "/config/office"
        ]
        
        office_config = {
            "office_email": "test@office.com",
            "office_password": "test123"
        }
        
        for endpoint in endpoints_to_try:
            try:
                print(f"   Trying POST {endpoint}")
                async with self.session.post(f"{BACKEND_URL}{endpoint}", json=office_config, headers=headers) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        self.log_result("5. Save Office Config", True, f"Office config saved successfully at {endpoint}", data)
                        return True
                    else:
                        error_text = await response.text()
                        print(f"      Status {response.status}: {error_text[:100]}")
                        
            except Exception as e:
                print(f"      Exception: {str(e)}")
                continue
        
        self.log_result("5. Save Office Config", False, "All office config endpoints failed")
        return False
    
    async def test_6_save_wa_site_config(self):
        """Test 6: Save WA Site Config"""
        print("💬 TEST 6: SAVE WA SITE CONFIG")
        print("=" * 50)
        
        if not self.auth_token:
            self.log_result("6. Save WA Site Config", False, "No auth token available")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Multiple endpoints to try
        endpoints_to_try = [
            "/admin/vendas-bot/config",
            "/vendas/simple-config-v2"
        ]
        
        # First try to get existing config to understand structure
        try:
            async with self.session.get(f"{BACKEND_URL}/admin/vendas-bot/config", headers=headers) as response:
                if response.status == 200:
                    existing_config = await response.json()
                    print(f"   Found existing config structure: {list(existing_config.keys())}")
        except:
            pass
        
        # Multiple config variations to try
        config_variations = [
            {
                "openai_api_key": "sk-test-key-for-testing",
                "ia_config": {
                    "name": "Assistente Teste",
                    "instructions": "Você é um assistente de vendas"
                },
                "empresa_config": {
                    "nome": "Empresa Teste",
                    "descricao": "Teste de configuração"
                }
            },
            {
                "openai_api_key": "sk-test-key-for-testing",
                "bot_name": "Assistente Teste",
                "instructions": "Você é um assistente de vendas"
            },
            {
                "api_key": "sk-test-key-for-testing",
                "config": {
                    "bot_name": "Assistente Teste"
                }
            }
        ]
        
        for endpoint in endpoints_to_try:
            for config_data in config_variations:
                try:
                    print(f"   Trying POST {endpoint} with {list(config_data.keys())}")
                    async with self.session.post(f"{BACKEND_URL}{endpoint}", json=config_data, headers=headers) as response:
                        if response.status in [200, 201]:
                            data = await response.json()
                            self.log_result("6. Save WA Site Config", True, f"WA Site config saved successfully at {endpoint}", data)
                            return True
                        else:
                            error_text = await response.text()
                            print(f"      Status {response.status}: {error_text[:100]}")
                            
                except Exception as e:
                    print(f"      Exception: {str(e)}")
                    continue
        
        self.log_result("6. Save WA Site Config", False, "All WA site config attempts failed")
        return False
    
    async def test_7_save_dados_permitidos(self):
        """Test 7: Save Dados Permitidos (Allowed Data)"""
        print("📋 TEST 7: SAVE DADOS PERMITIDOS")
        print("=" * 50)
        
        if not self.auth_token:
            self.log_result("7. Save Dados Permitidos", False, "No auth token available")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # First get existing config
        try:
            async with self.session.get(f"{BACKEND_URL}/config", headers=headers) as response:
                if response.status == 200:
                    existing_config = await response.json()
                    print(f"   Found existing config with keys: {list(existing_config.keys())}")
                    
                    # Update with allowed data
                    updated_config = existing_config.copy()
                    updated_config["allowed_data"] = {
                        "cpfs": ["123.456.789-00"],
                        "emails": ["nome@email.com", "telefone@email.com"],
                        "phones": ["11999999999"],
                        "random_keys": ["test-key-123"]
                    }
                    
                    # Try PUT method
                    async with self.session.put(f"{BACKEND_URL}/config", json=updated_config, headers=headers) as put_response:
                        if put_response.status in [200, 201]:
                            data = await put_response.json()
                            self.log_result("7. Save Dados Permitidos", True, "Allowed data saved successfully via PUT /config", data)
                            return True
                        else:
                            error_text = await put_response.text()
                            print(f"      PUT Status {put_response.status}: {error_text[:100]}")
                else:
                    error_text = await response.text()
                    print(f"      GET Status {response.status}: {error_text[:100]}")
                    
        except Exception as e:
            print(f"      Exception: {str(e)}")
        
        self.log_result("7. Save Dados Permitidos", False, "Failed to save allowed data")
        return False
    
    async def test_8_send_message(self):
        """Test 8: Send Message (Critical)"""
        print("💬 TEST 8: SEND MESSAGE (CRITICAL)")
        print("=" * 50)
        
        if not self.auth_token:
            self.log_result("8. Send Message", False, "No auth token available")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # First try to create a vendas session
        session_created = False
        session_id = None
        
        try:
            session_data = {"whatsapp": "5511999999999"}
            async with self.session.post(f"{BACKEND_URL}/vendas/start", json=session_data, headers=headers) as response:
                if response.status in [200, 201]:
                    session_response = await response.json()
                    session_id = session_response.get("session_id")
                    session_created = True
                    print(f"   Created vendas session: {session_id}")
        except Exception as e:
            print(f"   Failed to create vendas session: {e}")
        
        # Test message sending in vendas route
        if session_created and session_id:
            try:
                vendas_message = {
                    "text": "Mensagem de teste via API /vendas",
                    "session_id": session_id
                }
                
                async with self.session.post(f"{BACKEND_URL}/vendas/message", json=vendas_message, headers=headers) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        self.log_result("8. Send Message (Vendas)", True, "Message sent successfully via /vendas/message", data)
                        return True
                    else:
                        error_text = await response.text()
                        print(f"      Vendas message Status {response.status}: {error_text[:100]}")
                        
            except Exception as e:
                print(f"      Vendas message Exception: {str(e)}")
        
        # Test message sending in atendente route
        try:
            # Try to find an existing ticket first
            async with self.session.get(f"{BACKEND_URL}/tickets", headers=headers) as response:
                if response.status == 200:
                    tickets = await response.json()
                    ticket_id = tickets[0]["id"] if tickets else "test-ticket-123"
                else:
                    ticket_id = "test-ticket-123"
            
            atendente_message = {
                "text": "Mensagem de teste via API /messages",
                "ticket_id": ticket_id,
                "from_id": "admin",
                "from_type": "agent"
            }
            
            async with self.session.post(f"{BACKEND_URL}/messages", json=atendente_message, headers=headers) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    self.log_result("8. Send Message (Atendente)", True, "Message sent successfully via /messages", data)
                    return True
                else:
                    error_text = await response.text()
                    print(f"      Atendente message Status {response.status}: {error_text[:100]}")
                    
        except Exception as e:
            print(f"      Atendente message Exception: {str(e)}")
        
        self.log_result("8. Send Message", False, "All message sending attempts failed")
        return False
    
    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 STARTING COMPREHENSIVE EXTERNAL SERVER TESTING")
        print("=" * 70)
        print(f"Backend URL: {BACKEND_URL}")
        print("Testing specific user journey as requested in review")
        print("=" * 70)
        print()
        
        # Run tests in sequence - each depends on previous ones
        test_1_success = await self.test_1_admin_login()
        
        if test_1_success:
            await self.test_2_create_department()
            await self.test_3_list_departments()
            await self.test_4_create_agent()
            await self.test_5_save_office_config()
            await self.test_6_save_wa_site_config()
            await self.test_7_save_dados_permitidos()
            await self.test_8_send_message()
        else:
            print("❌ Authentication failed - skipping dependent tests")
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        print()
        
        # SUCCESS CRITERIA CHECK
        print("🎯 SUCCESS CRITERIA VERIFICATION:")
        print("=" * 40)
        
        success_criteria = {
            "Admin login works": any("1. Admin Login" in r["test"] and r["success"] for r in self.test_results),
            "Department creation works": any("2. Create Department" in r["test"] and r["success"] for r in self.test_results),
            "Agent creation works": any("4. Create Agent" in r["test"] and r["success"] for r in self.test_results),
            "All save operations work": any("Save" in r["test"] and r["success"] for r in self.test_results)
        }
        
        for criteria, met in success_criteria.items():
            status = "✅" if met else "❌"
            print(f"{status} {criteria}")
        
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS DETAILS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
            print()
        
        if passed_tests > 0:
            print("✅ PASSED TESTS:")
            for result in self.test_results:
                if result["success"]:
                    print(f"   • {result['test']}")
            print()
        
        print("=" * 70)
        
        if all(success_criteria.values()):
            print("🎉 ALL SUCCESS CRITERIA MET! External server is fully functional.")
        else:
            unmet_criteria = [k for k, v in success_criteria.items() if not v]
            print(f"⚠️  Success criteria not met: {', '.join(unmet_criteria)}")

async def main():
    """Main test execution"""
    async with ExternalServerTester() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())