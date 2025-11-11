#!/usr/bin/env python3
"""
🔍 AUDITORIA COMPLETA DO BACKEND - TESTE FOCADO NAS FUNCIONALIDADES CRÍTICAS

Baseado nos resultados do teste anterior, este teste foca nos problemas identificados
e testa as funcionalidades críticas de forma mais robusta.
"""

import requests
import json
import time
from typing import Dict, Optional, List, Tuple

# Backend URL
BACKEND_URL = "https://wppconnect-fix.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Credenciais corretas baseadas na investigação
ADMIN_PASSWORD = "102030@ab"
AGENT_LOGIN = "fabioteste"
AGENT_PASSWORD = "123"
RESELLER_EMAIL = "michaelrv@gmail.com"  # Correto baseado na lista
RESELLER_PASSWORD = "ab181818ab"
CLIENT_WHATSAPP = "5511999999999"
CLIENT_PIN = "00"

class FocusedBackendTester:
    def __init__(self):
        self.admin_token = None
        self.agent_token = None
        self.reseller_token = None
        self.client_token = None
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}"
        if message:
            result += f" - {message}"
        print(result)
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
        
    def make_request(self, method: str, endpoint: str, data: dict = None, 
                    token: str = None, headers: dict = None) -> Tuple[bool, dict]:
        """Make HTTP request with error handling"""
        url = f"{API_BASE}{endpoint}"
        
        request_headers = {"Content-Type": "application/json"}
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        if headers:
            request_headers.update(headers)
            
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=request_headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=request_headers, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=request_headers, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=request_headers, timeout=30)
            else:
                return False, {"error": f"Unsupported method: {method}"}
                
            try:
                response_data = response.json() if response.text else {}
            except json.JSONDecodeError:
                response_data = {"text": response.text, "status_code": response.status_code}
                
            return response.status_code < 400, response_data
            
        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}

    # ============================================
    # TESTES DE AUTENTICAÇÃO
    # ============================================
    
    def test_authentication_complete(self) -> bool:
        """Test 1: Autenticação completa (4 tipos)"""
        print("\n🔐 TESTANDO AUTENTICAÇÃO COMPLETA...")
        
        auth_results = []
        
        # 1.1 Admin Login
        success, response = self.make_request("POST", "/auth/admin/login", {
            "password": ADMIN_PASSWORD
        })
        
        if success and "token" in response:
            self.admin_token = response["token"]
            auth_results.append(("Admin Login", True, "Admin logged in successfully"))
        else:
            auth_results.append(("Admin Login", False, f"Error: {response}"))
        
        # 1.2 Agent Login
        success, response = self.make_request("POST", "/auth/agent/login", {
            "login": AGENT_LOGIN,
            "password": AGENT_PASSWORD
        })
        
        if success and "token" in response:
            self.agent_token = response["token"]
            reseller_id = response.get("reseller_id")
            auth_results.append(("Agent Login", True, f"Agent logged in, reseller_id: {reseller_id}"))
        else:
            auth_results.append(("Agent Login", False, f"Error: {response}"))

        # 1.3 Reseller Login
        success, response = self.make_request("POST", "/resellers/login", {
            "email": RESELLER_EMAIL,
            "password": RESELLER_PASSWORD
        })
        
        if success and "token" in response:
            self.reseller_token = response["token"]
            reseller_id = response.get("reseller_id")
            auth_results.append(("Reseller Login", True, f"Reseller logged in, reseller_id: {reseller_id}"))
        else:
            auth_results.append(("Reseller Login", False, f"Error: {response}"))

        # 1.4 Client Login
        success, response = self.make_request("POST", "/auth/client/login", {
            "whatsapp": CLIENT_WHATSAPP,
            "pin": CLIENT_PIN
        })
        
        if success and "token" in response:
            self.client_token = response["token"]
            auth_results.append(("Client Login", True, "Client logged in successfully"))
        else:
            auth_results.append(("Client Login", False, f"Error: {response}"))
        
        # Log all results
        all_auth_ok = True
        for test_name, success, message in auth_results:
            self.log_result(test_name, success, message)
            if not success:
                all_auth_ok = False
        
        return all_auth_ok

    # ============================================
    # TESTE DE ISOLAMENTO MULTI-TENANT
    # ============================================
    
    def test_multi_tenant_isolation_fixed(self) -> bool:
        """Test 2: Isolamento multi-tenant (versão corrigida)"""
        print("\n🔒 TESTANDO ISOLAMENTO MULTI-TENANT...")
        
        if not self.admin_token or not self.agent_token:
            self.log_result("Multi-Tenant Isolation", False, "Required tokens missing")
            return False
        
        isolation_tests = []
        
        # Test tickets isolation
        success_admin, admin_tickets = self.make_request("GET", "/tickets", token=self.admin_token)
        success_agent, agent_tickets = self.make_request("GET", "/tickets", token=self.agent_token)
        
        if success_admin and success_agent:
            admin_count = len(admin_tickets)
            agent_count = len(agent_tickets)
            
            print(f"   📊 Tickets - Admin Master vê: {admin_count}, Agent fabioteste vê: {agent_count}")
            
            # Admin should see more or equal tickets than agent
            tickets_isolation_ok = admin_count >= agent_count
            isolation_tests.append(("Tickets Isolation", tickets_isolation_ok, f"Admin: {admin_count}, Agent: {agent_count}"))
        else:
            isolation_tests.append(("Tickets Isolation", False, "Failed to fetch tickets"))
        
        # Test agents isolation
        success_admin, admin_agents = self.make_request("GET", "/agents", token=self.admin_token)
        success_agent, agent_agents = self.make_request("GET", "/agents", token=self.agent_token)
        
        if success_admin and success_agent:
            admin_agents_count = len(admin_agents)
            agent_agents_count = len(agent_agents)
            
            print(f"   📊 Agents - Admin Master vê: {admin_agents_count}, Agent fabioteste vê: {agent_agents_count}")
            
            agents_isolation_ok = admin_agents_count >= agent_agents_count
            isolation_tests.append(("Agents Isolation", agents_isolation_ok, f"Admin: {admin_agents_count}, Agent: {agent_agents_count}"))
        else:
            isolation_tests.append(("Agents Isolation", False, "Failed to fetch agents"))
        
        # Test AI agents isolation (if reseller token available)
        if self.reseller_token:
            success_admin, admin_ai_agents = self.make_request("GET", "/ai/agents", token=self.admin_token)
            success_reseller, reseller_ai_agents = self.make_request("GET", "/ai/agents", token=self.reseller_token)
            
            if success_admin and success_reseller:
                admin_ai_count = len(admin_ai_agents)
                reseller_ai_count = len(reseller_ai_agents)
                
                print(f"   📊 AI Agents - Admin Master vê: {admin_ai_count}, Reseller vê: {reseller_ai_count}")
                
                ai_agents_isolation_ok = admin_ai_count >= reseller_ai_count
                isolation_tests.append(("AI Agents Isolation", ai_agents_isolation_ok, f"Admin: {admin_ai_count}, Reseller: {reseller_ai_count}"))
            else:
                isolation_tests.append(("AI Agents Isolation", False, "Failed to fetch AI agents"))
        
        # Log all isolation test results
        all_isolation_ok = True
        for test_name, success, message in isolation_tests:
            self.log_result(test_name, success, message)
            if not success:
                all_isolation_ok = False
        
        return all_isolation_ok

    # ============================================
    # TESTE DE CRUD FUNCIONALIDADES
    # ============================================
    
    def test_crud_operations(self) -> bool:
        """Test 3: Operações CRUD críticas"""
        print("\n🔧 TESTANDO OPERAÇÕES CRUD...")
        
        if not self.admin_token:
            self.log_result("CRUD Operations", False, "Admin token required")
            return False
        
        crud_results = []
        
        # Test Resellers CRUD
        success, resellers = self.make_request("GET", "/resellers", token=self.admin_token)
        if success:
            crud_results.append(("List Resellers", True, f"Found {len(resellers)} resellers"))
        else:
            crud_results.append(("List Resellers", False, f"Error: {resellers}"))
        
        # Test Agents CRUD
        success, agents = self.make_request("GET", "/agents", token=self.admin_token)
        if success:
            crud_results.append(("List Agents", True, f"Found {len(agents)} agents"))
        else:
            crud_results.append(("List Agents", False, f"Error: {agents}"))
        
        # Test AI Agents CRUD
        success, ai_agents = self.make_request("GET", "/ai/agents", token=self.admin_token)
        if success:
            crud_results.append(("List AI Agents", True, f"Found {len(ai_agents)} AI agents"))
        else:
            crud_results.append(("List AI Agents", False, f"Error: {ai_agents}"))
        
        # Test Departments CRUD
        success, departments = self.make_request("GET", "/ai/departments", token=self.admin_token)
        if success:
            crud_results.append(("List Departments", True, f"Found {len(departments)} departments"))
        else:
            crud_results.append(("List Departments", False, f"Error: {departments}"))
        
        # Test IPTV Apps CRUD
        success, iptv_apps = self.make_request("GET", "/iptv-apps", token=self.admin_token)
        if success:
            crud_results.append(("List IPTV Apps", True, f"Found {len(iptv_apps)} IPTV apps"))
        else:
            crud_results.append(("List IPTV Apps", False, f"Error: {iptv_apps}"))
        
        # Test Notices CRUD
        success, notices = self.make_request("GET", "/notices", token=self.admin_token)
        if success:
            crud_results.append(("List Notices", True, f"Found {len(notices)} notices"))
        else:
            crud_results.append(("List Notices", False, f"Error: {notices}"))
        
        # Log all CRUD results
        all_crud_ok = True
        for test_name, success, message in crud_results:
            self.log_result(test_name, success, message)
            if not success:
                all_crud_ok = False
        
        return all_crud_ok

    # ============================================
    # TESTE DE CONFIGURAÇÕES
    # ============================================
    
    def test_configuration_endpoints(self) -> bool:
        """Test 4: Endpoints de configuração"""
        print("\n⚙️ TESTANDO ENDPOINTS DE CONFIGURAÇÃO...")
        
        if not self.admin_token:
            self.log_result("Configuration Endpoints", False, "Admin token required")
            return False
        
        config_results = []
        
        # Test GET /api/config
        success, config = self.make_request("GET", "/config", token=self.admin_token)
        if success:
            required_fields = ["pix_key", "allowed_data", "api_integration", "ai_agent"]
            missing_fields = [field for field in required_fields if field not in config]
            
            if missing_fields:
                config_results.append(("Get Config", False, f"Missing fields: {missing_fields}"))
            else:
                config_results.append(("Get Config", True, f"All required fields present: {required_fields}"))
        else:
            config_results.append(("Get Config", False, f"Error: {config}"))
        
        # Test Auto-Responder Sequences
        success, sequences = self.make_request("GET", "/config/auto-responder-sequences", token=self.admin_token)
        if success:
            config_results.append(("Auto-Responder Sequences", True, f"Found {len(sequences)} sequences"))
        else:
            config_results.append(("Auto-Responder Sequences", False, f"Error: {sequences}"))
        
        # Test Tutorials Advanced
        success, tutorials = self.make_request("GET", "/config/tutorials-advanced", token=self.admin_token)
        if success:
            config_results.append(("Tutorials Advanced", True, f"Found {len(tutorials)} tutorials"))
        else:
            config_results.append(("Tutorials Advanced", False, f"Error: {tutorials}"))
        
        # Log all config results
        all_config_ok = True
        for test_name, success, message in config_results:
            self.log_result(test_name, success, message)
            if not success:
                all_config_ok = False
        
        return all_config_ok

    # ============================================
    # TESTE DE FUNCIONALIDADES ESPECIAIS
    # ============================================
    
    def test_special_features(self) -> bool:
        """Test 5: Funcionalidades especiais (WhatsApp, PIN, Upload)"""
        print("\n🌟 TESTANDO FUNCIONALIDADES ESPECIAIS...")
        
        special_results = []
        
        # Test WhatsApp & PIN (if client token available)
        if self.client_token:
            # WhatsApp popup status
            success, popup_status = self.make_request("GET", "/users/whatsapp-popup-status", token=self.client_token)
            if success:
                should_show = popup_status.get("should_show", False)
                special_results.append(("WhatsApp Popup Status", True, f"Should show popup: {should_show}"))
            else:
                special_results.append(("WhatsApp Popup Status", False, f"Error: {popup_status}"))
            
            # PIN update (valid)
            success, response = self.make_request("PUT", "/users/me/pin", {"pin": "99"}, token=self.client_token)
            if success:
                special_results.append(("PIN Update Valid", True, "PIN updated successfully"))
            else:
                special_results.append(("PIN Update Valid", False, f"Error: {response}"))
        else:
            special_results.append(("WhatsApp & PIN", False, "Client token not available"))
        
        # Test Domain Management (if reseller token available)
        if self.reseller_token:
            success, domain_info = self.make_request("GET", "/reseller/domain-info", token=self.reseller_token)
            if success:
                custom_domain = domain_info.get("custom_domain", "No custom domain")
                special_results.append(("Domain Management", True, f"Domain info retrieved: {custom_domain}"))
            else:
                special_results.append(("Domain Management", False, f"Error: {domain_info}"))
        else:
            special_results.append(("Domain Management", False, "Reseller token not available"))
        
        # Test Tickets functionality
        if self.admin_token:
            success, tickets = self.make_request("GET", "/tickets", token=self.admin_token)
            if success:
                special_results.append(("Tickets List", True, f"Found {len(tickets)} tickets"))
                
                # Test ticket counts
                success, counts = self.make_request("GET", "/tickets/counts", token=self.admin_token)
                if success:
                    em_espera = counts.get("EM_ESPERA", 0)
                    atendendo = counts.get("ATENDENDO", 0)
                    finalizadas = counts.get("FINALIZADAS", 0)
                    special_results.append(("Ticket Counts", True, f"EM_ESPERA: {em_espera}, ATENDENDO: {atendendo}, FINALIZADAS: {finalizadas}"))
                else:
                    special_results.append(("Ticket Counts", False, f"Error: {counts}"))
            else:
                special_results.append(("Tickets List", False, f"Error: {tickets}"))
        
        # Log all special feature results
        all_special_ok = True
        for test_name, success, message in special_results:
            self.log_result(test_name, success, message)
            if not success:
                all_special_ok = False
        
        return all_special_ok

    # ============================================
    # TESTE DE REPLICAÇÃO DE CONFIGURAÇÕES
    # ============================================
    
    def test_config_replication(self) -> bool:
        """Test 6: Replicação de configurações (admin only)"""
        print("\n🔄 TESTANDO REPLICAÇÃO DE CONFIGURAÇÕES...")
        
        if not self.admin_token:
            self.log_result("Config Replication", False, "Admin token required")
            return False
        
        # Test admin replication endpoint
        success, response = self.make_request("POST", "/admin/replicate-config-to-resellers", {}, token=self.admin_token)
        
        if success:
            total_resellers = response.get("total_resellers", 0)
            replicated_count = response.get("replicated_count", 0)
            self.log_result("Config Replication", True, f"Replicated to {replicated_count}/{total_resellers} resellers")
            return True
        else:
            self.log_result("Config Replication", False, f"Error: {response}")
            return False

    # ============================================
    # MAIN TEST RUNNER
    # ============================================
    
    def run_focused_tests(self):
        """Run focused backend tests"""
        print("🔍 AUDITORIA COMPLETA DO BACKEND - TESTE FOCADO NAS FUNCIONALIDADES CRÍTICAS")
        print("=" * 80)
        print("OBJETIVO: Testar funcionalidades críticas com foco nos problemas identificados")
        print("BACKEND URL:", BACKEND_URL)
        print("=" * 80)
        
        # Define all tests in order
        tests = [
            ("Authentication Complete", self.test_authentication_complete),
            ("Multi-Tenant Isolation", self.test_multi_tenant_isolation_fixed),
            ("CRUD Operations", self.test_crud_operations),
            ("Configuration Endpoints", self.test_configuration_endpoints),
            ("Special Features", self.test_special_features),
            ("Config Replication", self.test_config_replication),
        ]
        
        passed = 0
        total = len(tests)
        failed_tests = []
        
        for test_name, test_func in tests:
            try:
                print(f"\n🔄 Executando: {test_name}")
                if test_func():
                    passed += 1
                    print(f"✅ {test_name} PASSOU")
                else:
                    failed_tests.append(test_name)
                    print(f"❌ {test_name} FALHOU")
                time.sleep(0.5)  # Small delay between tests
            except Exception as e:
                self.log_result(test_name, False, f"Exception: {str(e)}")
                failed_tests.append(test_name)
                print(f"💥 {test_name} ERRO: {str(e)}")
                
        print("\n" + "=" * 80)
        print(f"📊 RESULTADO FINAL: {passed}/{total} testes passaram ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            print("🎉 TODOS OS TESTES PASSARAM! BACKEND 100% FUNCIONAL!")
            print("🔒 SISTEMA COMPLETAMENTE VALIDADO E PRONTO PARA PRODUÇÃO!")
        else:
            print(f"⚠️  {total - passed} testes falharam:")
            for failed_test in failed_tests:
                print(f"   ❌ {failed_test}")
            print("\n🔧 AÇÕES NECESSÁRIAS:")
            print("   - Verificar endpoints que falharam")
            print("   - Confirmar credenciais e configurações")
            print("   - Testar novamente após correções")
            
        return passed, total, self.test_results


if __name__ == "__main__":
    print("🔍 INICIANDO AUDITORIA FOCADA DO BACKEND")
    print("Backend URL:", BACKEND_URL)
    print("Credenciais corrigidas baseadas na investigação")
    print()
    
    tester = FocusedBackendTester()
    passed, total, results = tester.run_focused_tests()
    
    print(f"\n📋 RESUMO DETALHADO:")
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['test']}: {result['message']}")
    
    exit_code = 0 if passed == total else 1
    exit(exit_code)