#!/usr/bin/env python3
"""
🎯 TESTE ESPECÍFICO CONFORME REVIEW REQUEST - ENDPOINT /api/tickets PARA ATENDENTE FABIO123

CONTEXTO DO REVIEW REQUEST:
- Atendente: fabio123 (ID: 6254a141-af9e-4be0-a77a-016030482db7)
- Reseller ID: 49376e6f-4122-4fcf-88ab-97965c472711
- Departamento: WHATSAPP 1 (ID: d525463d-0691-4525-aee1-5a74fc0a69a0)
- Ticket existe no banco: "WhatsApp de Fabio Silva" com 6 mensagens
- O atendente está vinculado ao departamento WHATSAPP 1

TESTE:
1. Fazer login como atendente fabio123 / 102030ab
2. Chamar GET /api/tickets
3. Verificar se o ticket "WhatsApp de Fabio Silva" aparece
4. Se não aparecer, verificar o JSON retornado e identificar o problema
5. Testar também GET /api/tickets?status=open

OBJETIVO: Identificar por que o endpoint /api/tickets não está retornando os tickets do WhatsApp para o atendente
"""

import requests
import json
import os
from typing import Dict, Optional, List
import time

# Backend URL - usar a URL do ambiente
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://wppconnect-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Credenciais do review request (corrigidas após debug)
FABIO_LOGIN = "fabio123"
FABIO_PASSWORD = "fabio123"  # Senha correta encontrada via debug
EXPECTED_AGENT_ID = "6254a141-af9e-4be0-a77a-016030482db7"
EXPECTED_RESELLER_ID = "49376e6f-4122-4fcf-88ab-97965c472711"
EXPECTED_DEPARTMENT_ID = "d525463d-0691-4525-aee1-5a74fc0a69a0"

class FabioTicketsTest:
    def __init__(self):
        self.fabio_token = None
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
                    token: str = None, headers: dict = None, params: dict = None) -> tuple[bool, dict]:
        """Make HTTP request with error handling"""
        url = f"{API_BASE}{endpoint}"
        
        request_headers = {"Content-Type": "application/json"}
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        if headers:
            request_headers.update(headers)
            
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=request_headers, params=params, timeout=30)
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
                response_data = {"raw_response": response.text}
                
            return response.status_code < 400, response_data
            
        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}
    
    def test_fabio_login(self) -> bool:
        """Test 1: Login como atendente fabio123 / 102030ab"""
        print(f"\n🔐 TESTE 1: Login do atendente fabio123")
        print(f"   Credenciais: {FABIO_LOGIN} / {FABIO_PASSWORD}")
        
        success, response = self.make_request("POST", "/auth/agent/login", {
            "login": FABIO_LOGIN,
            "password": FABIO_PASSWORD
        })
        
        if success and "token" in response:
            self.fabio_token = response["token"]
            user_data = response.get("user_data", {})
            reseller_id = response.get("reseller_id")
            
            print(f"   ✅ Login realizado com sucesso!")
            print(f"   📋 Agent ID: {user_data.get('id', 'N/A')}")
            print(f"   📋 Agent Name: {user_data.get('name', 'N/A')}")
            print(f"   📋 Reseller ID: {reseller_id}")
            print(f"   📋 Token: {self.fabio_token[:50]}...")
            
            # Verificar se os IDs batem com o esperado
            agent_id = user_data.get('id')
            if agent_id == EXPECTED_AGENT_ID:
                print(f"   ✅ Agent ID confere: {agent_id}")
            else:
                print(f"   ⚠️  Agent ID diferente do esperado:")
                print(f"      Esperado: {EXPECTED_AGENT_ID}")
                print(f"      Recebido: {agent_id}")
            
            if reseller_id == EXPECTED_RESELLER_ID:
                print(f"   ✅ Reseller ID confere: {reseller_id}")
            else:
                print(f"   ⚠️  Reseller ID diferente do esperado:")
                print(f"      Esperado: {EXPECTED_RESELLER_ID}")
                print(f"      Recebido: {reseller_id}")
            
            self.log_result("Login fabio123", True, f"Agent ID: {agent_id}, Reseller ID: {reseller_id}")
            return True
        else:
            print(f"   ❌ Erro no login: {response}")
            self.log_result("Login fabio123", False, f"Error: {response}")
            return False
    
    def test_get_tickets_basic(self) -> bool:
        """Test 2: GET /api/tickets (sem filtros)"""
        print(f"\n📊 TESTE 2: GET /api/tickets (sem filtros)")
        
        if not self.fabio_token:
            print("   ❌ Token não disponível - faça login primeiro")
            self.log_result("GET /api/tickets", False, "No token available")
            return False
        
        success, tickets = self.make_request("GET", "/tickets", token=self.fabio_token)
        
        if not success:
            print(f"   ❌ Erro na requisição: {tickets}")
            self.log_result("GET /api/tickets", False, f"Request error: {tickets}")
            return False
        
        print(f"   ✅ Requisição realizada com sucesso!")
        print(f"   📊 Total de tickets retornados: {len(tickets)}")
        
        if len(tickets) == 0:
            print(f"   ⚠️  NENHUM TICKET RETORNADO!")
            print(f"   💡 Isso pode indicar problema de filtro multi-tenant ou departamento")
            self.log_result("GET /api/tickets", False, "No tickets returned - possible filtering issue")
            return False
        
        # Analisar tickets retornados
        print(f"\n   📋 ANÁLISE DOS TICKETS RETORNADOS:")
        fabio_silva_found = False
        
        for i, ticket in enumerate(tickets):
            client_name = ticket.get('client_name', 'N/A')
            ticket_id = ticket.get('id', 'N/A')
            department_id = ticket.get('department_id', 'N/A')
            reseller_id = ticket.get('reseller_id', 'N/A')
            status = ticket.get('status', 'N/A')
            
            print(f"   [{i+1}] Ticket ID: {ticket_id}")
            print(f"       Cliente: {client_name}")
            print(f"       Departamento: {department_id}")
            print(f"       Reseller: {reseller_id}")
            print(f"       Status: {status}")
            
            # Verificar se é o ticket do Fabio Silva
            if "fabio silva" in client_name.lower() or "whatsapp de fabio silva" in client_name.lower():
                fabio_silva_found = True
                print(f"       🎯 ENCONTRADO: Ticket do Fabio Silva!")
            
            print()
        
        if fabio_silva_found:
            print(f"   ✅ Ticket 'WhatsApp de Fabio Silva' ENCONTRADO!")
            self.log_result("GET /api/tickets", True, f"Found {len(tickets)} tickets, including Fabio Silva ticket")
            return True
        else:
            print(f"   ❌ Ticket 'WhatsApp de Fabio Silva' NÃO ENCONTRADO!")
            print(f"   💡 Possíveis causas:")
            print(f"      - Filtro de departamento não está funcionando")
            print(f"      - Atendente não tem acesso ao departamento WHATSAPP 1")
            print(f"      - Ticket não existe ou está em outro departamento")
            print(f"      - Problema de isolamento multi-tenant")
            self.log_result("GET /api/tickets", False, f"Fabio Silva ticket not found among {len(tickets)} tickets")
            return False
    
    def test_get_tickets_status_open(self) -> bool:
        """Test 3: GET /api/tickets?status=open"""
        print(f"\n📊 TESTE 3: GET /api/tickets?status=open")
        
        if not self.fabio_token:
            print("   ❌ Token não disponível - faça login primeiro")
            self.log_result("GET /api/tickets?status=open", False, "No token available")
            return False
        
        success, tickets = self.make_request("GET", "/tickets", token=self.fabio_token, params={"status": "open"})
        
        if not success:
            print(f"   ❌ Erro na requisição: {tickets}")
            self.log_result("GET /api/tickets?status=open", False, f"Request error: {tickets}")
            return False
        
        print(f"   ✅ Requisição realizada com sucesso!")
        print(f"   📊 Total de tickets com status 'open': {len(tickets)}")
        
        # Analisar tickets retornados
        if len(tickets) > 0:
            print(f"\n   📋 TICKETS COM STATUS 'OPEN':")
            fabio_silva_found = False
            
            for i, ticket in enumerate(tickets):
                client_name = ticket.get('client_name', 'N/A')
                ticket_id = ticket.get('id', 'N/A')
                status = ticket.get('status', 'N/A')
                
                print(f"   [{i+1}] {client_name} (ID: {ticket_id}, Status: {status})")
                
                if "fabio silva" in client_name.lower():
                    fabio_silva_found = True
                    print(f"       🎯 ENCONTRADO: Ticket do Fabio Silva com status open!")
            
            if fabio_silva_found:
                self.log_result("GET /api/tickets?status=open", True, f"Found Fabio Silva ticket among {len(tickets)} open tickets")
                return True
            else:
                print(f"   ⚠️  Ticket do Fabio Silva não está com status 'open'")
                self.log_result("GET /api/tickets?status=open", False, f"Fabio Silva ticket not in open status")
                return False
        else:
            print(f"   ⚠️  Nenhum ticket com status 'open' encontrado")
            self.log_result("GET /api/tickets?status=open", False, "No open tickets found")
            return False
    
    def test_get_tickets_all_statuses(self) -> bool:
        """Test 4: Testar todos os status possíveis"""
        print(f"\n📊 TESTE 4: Testando todos os status de tickets")
        
        if not self.fabio_token:
            print("   ❌ Token não disponível")
            return False
        
        statuses = ["EM_ESPERA", "ATENDENDO", "FINALIZADAS", "open", "closed"]
        total_found = 0
        fabio_found_in_status = None
        
        for status in statuses:
            print(f"\n   🔍 Testando status: {status}")
            success, tickets = self.make_request("GET", "/tickets", token=self.fabio_token, params={"status": status})
            
            if success:
                count = len(tickets)
                total_found += count
                print(f"      📊 {count} tickets com status '{status}'")
                
                # Verificar se Fabio Silva está neste status
                for ticket in tickets:
                    client_name = ticket.get('client_name', '')
                    if "fabio silva" in client_name.lower():
                        fabio_found_in_status = status
                        print(f"      🎯 Fabio Silva encontrado com status: {status}")
                        break
            else:
                print(f"      ❌ Erro ao buscar status {status}: {tickets}")
        
        print(f"\n   📊 RESUMO:")
        print(f"      Total de tickets encontrados: {total_found}")
        if fabio_found_in_status:
            print(f"      ✅ Fabio Silva encontrado com status: {fabio_found_in_status}")
            self.log_result("Test all statuses", True, f"Fabio Silva found with status: {fabio_found_in_status}")
            return True
        else:
            print(f"      ❌ Fabio Silva não encontrado em nenhum status")
            self.log_result("Test all statuses", False, "Fabio Silva not found in any status")
            return False
    
    def test_agent_departments_access(self) -> bool:
        """Test 5: Verificar departamentos do agente"""
        print(f"\n🏢 TESTE 5: Verificando departamentos do agente fabio123")
        
        if not self.fabio_token:
            print("   ❌ Token não disponível")
            return False
        
        # Buscar informações do agente atual
        success, agent_info = self.make_request("GET", "/agents/me", token=self.fabio_token)
        
        if not success:
            print(f"   ❌ Erro ao buscar informações do agente: {agent_info}")
            self.log_result("Agent departments", False, f"Error getting agent info: {agent_info}")
            return False
        
        print(f"   ✅ Informações do agente obtidas:")
        print(f"      ID: {agent_info.get('id', 'N/A')}")
        print(f"      Nome: {agent_info.get('name', 'N/A')}")
        print(f"      Login: {agent_info.get('login', 'N/A')}")
        
        department_ids = agent_info.get('department_ids', [])
        print(f"      Departamentos: {department_ids}")
        
        # Verificar se tem acesso ao departamento WHATSAPP 1
        if EXPECTED_DEPARTMENT_ID in department_ids:
            print(f"   ✅ Agente TEM acesso ao departamento WHATSAPP 1: {EXPECTED_DEPARTMENT_ID}")
            self.log_result("Agent departments", True, f"Agent has access to WHATSAPP 1 department")
            return True
        elif len(department_ids) == 0:
            print(f"   ⚠️  Agente não tem departamentos específicos (pode ter acesso a todos)")
            print(f"   💡 Isso pode significar que ele tem acesso a todos os departamentos")
            self.log_result("Agent departments", True, f"Agent has no specific departments (may access all)")
            return True
        else:
            print(f"   ❌ Agente NÃO tem acesso ao departamento WHATSAPP 1")
            print(f"      Esperado: {EXPECTED_DEPARTMENT_ID}")
            print(f"      Atual: {department_ids}")
            print(f"   💡 Esta pode ser a causa do problema!")
            self.log_result("Agent departments", False, f"Agent doesn't have access to WHATSAPP 1 department")
            return False
    
    def test_department_exists(self) -> bool:
        """Test 6: Verificar se o departamento WHATSAPP 1 existe"""
        print(f"\n🏢 TESTE 6: Verificando se departamento WHATSAPP 1 existe")
        
        if not self.fabio_token:
            print("   ❌ Token não disponível")
            return False
        
        # Buscar todos os departamentos
        success, departments = self.make_request("GET", "/ai/departments", token=self.fabio_token)
        
        if not success:
            print(f"   ❌ Erro ao buscar departamentos: {departments}")
            self.log_result("Department exists", False, f"Error getting departments: {departments}")
            return False
        
        print(f"   ✅ Departamentos obtidos: {len(departments)} encontrados")
        
        whatsapp1_found = False
        for dept in departments:
            dept_id = dept.get('id', 'N/A')
            dept_name = dept.get('name', 'N/A')
            print(f"      - {dept_name} (ID: {dept_id})")
            
            if dept_id == EXPECTED_DEPARTMENT_ID:
                whatsapp1_found = True
                print(f"        🎯 ENCONTRADO: Departamento WHATSAPP 1!")
        
        if whatsapp1_found:
            print(f"   ✅ Departamento WHATSAPP 1 existe: {EXPECTED_DEPARTMENT_ID}")
            self.log_result("Department exists", True, f"WHATSAPP 1 department found")
            return True
        else:
            print(f"   ❌ Departamento WHATSAPP 1 NÃO encontrado!")
            print(f"      Esperado ID: {EXPECTED_DEPARTMENT_ID}")
            print(f"   💡 Esta pode ser a causa do problema!")
            self.log_result("Department exists", False, f"WHATSAPP 1 department not found")
            return False
    
    def test_ticket_exists_in_database(self) -> bool:
        """Test 7: Verificar se o ticket existe no banco (via admin)"""
        print(f"\n💾 TESTE 7: Verificando se ticket existe no banco (login admin)")
        
        # Fazer login como admin para ver todos os tickets
        admin_success, admin_response = self.make_request("POST", "/auth/admin/login", {
            "password": "102030@ab"
        })
        
        if not admin_success or "token" not in admin_response:
            print(f"   ❌ Erro no login admin: {admin_response}")
            self.log_result("Ticket exists in DB", False, f"Admin login failed: {admin_response}")
            return False
        
        admin_token = admin_response["token"]
        print(f"   ✅ Login admin realizado com sucesso")
        
        # Buscar todos os tickets como admin
        success, all_tickets = self.make_request("GET", "/tickets", token=admin_token)
        
        if not success:
            print(f"   ❌ Erro ao buscar tickets como admin: {all_tickets}")
            self.log_result("Ticket exists in DB", False, f"Error getting tickets as admin: {all_tickets}")
            return False
        
        print(f"   ✅ Admin vê {len(all_tickets)} tickets no total")
        
        # Procurar pelo ticket do Fabio Silva
        fabio_ticket = None
        for ticket in all_tickets:
            client_name = ticket.get('client_name', '')
            if "fabio silva" in client_name.lower() or "whatsapp de fabio silva" in client_name.lower():
                fabio_ticket = ticket
                break
        
        if fabio_ticket:
            print(f"   ✅ Ticket do Fabio Silva ENCONTRADO no banco!")
            print(f"      ID: {fabio_ticket.get('id', 'N/A')}")
            print(f"      Cliente: {fabio_ticket.get('client_name', 'N/A')}")
            print(f"      Departamento: {fabio_ticket.get('department_id', 'N/A')}")
            print(f"      Reseller: {fabio_ticket.get('reseller_id', 'N/A')}")
            print(f"      Status: {fabio_ticket.get('status', 'N/A')}")
            
            # Verificar se está no departamento correto
            if fabio_ticket.get('department_id') == EXPECTED_DEPARTMENT_ID:
                print(f"   ✅ Ticket está no departamento WHATSAPP 1 correto")
            else:
                print(f"   ⚠️  Ticket está em departamento diferente:")
                print(f"      Esperado: {EXPECTED_DEPARTMENT_ID}")
                print(f"      Atual: {fabio_ticket.get('department_id')}")
            
            # Verificar se está na revenda correta
            if fabio_ticket.get('reseller_id') == EXPECTED_RESELLER_ID:
                print(f"   ✅ Ticket está na revenda correta")
            else:
                print(f"   ⚠️  Ticket está em revenda diferente:")
                print(f"      Esperado: {EXPECTED_RESELLER_ID}")
                print(f"      Atual: {fabio_ticket.get('reseller_id')}")
            
            self.log_result("Ticket exists in DB", True, f"Fabio Silva ticket found in database")
            return True
        else:
            print(f"   ❌ Ticket do Fabio Silva NÃO encontrado no banco!")
            print(f"   💡 O ticket pode não existir ou ter nome diferente")
            
            # Mostrar alguns tickets para debug
            print(f"\n   📋 Primeiros 5 tickets no banco:")
            for i, ticket in enumerate(all_tickets[:5]):
                print(f"      [{i+1}] {ticket.get('client_name', 'N/A')} (ID: {ticket.get('id', 'N/A')})")
            
            self.log_result("Ticket exists in DB", False, f"Fabio Silva ticket not found in database")
            return False
    
    def run_all_tests(self):
        """Executar todos os testes conforme review request"""
        print("🎯 TESTE ESPECÍFICO CONFORME REVIEW REQUEST - ENDPOINT /api/tickets PARA ATENDENTE FABIO123")
        print("=" * 90)
        print(f"BACKEND URL: {BACKEND_URL}")
        print(f"CREDENCIAIS: {FABIO_LOGIN} / {FABIO_PASSWORD}")
        print(f"AGENT ID ESPERADO: {EXPECTED_AGENT_ID}")
        print(f"RESELLER ID ESPERADO: {EXPECTED_RESELLER_ID}")
        print(f"DEPARTAMENTO ESPERADO: {EXPECTED_DEPARTMENT_ID}")
        print("=" * 90)
        
        tests = [
            self.test_fabio_login,
            self.test_get_tickets_basic,
            self.test_get_tickets_status_open,
            self.test_get_tickets_all_statuses,
            self.test_agent_departments_access,
            self.test_department_exists,
            self.test_ticket_exists_in_database,
        ]
        
        passed = 0
        total = len(tests)
        failed_tests = []
        
        for test in tests:
            try:
                print(f"\n" + "="*50)
                if test():
                    passed += 1
                else:
                    failed_tests.append(test.__name__)
                time.sleep(1)  # Delay between tests
            except Exception as e:
                self.log_result(test.__name__, False, f"Exception: {str(e)}")
                failed_tests.append(test.__name__)
                print(f"💥 {test.__name__} ERRO: {str(e)}")
        
        print("\n" + "=" * 90)
        print(f"📊 RESULTADO FINAL: {passed}/{total} testes passaram ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            print("🎉 TODOS OS TESTES PASSARAM!")
            print("✅ O endpoint /api/tickets está funcionando corretamente para fabio123")
            print("✅ O ticket 'WhatsApp de Fabio Silva' está sendo retornado")
        else:
            print(f"⚠️  {total - passed} testes falharam:")
            for failed_test in failed_tests:
                print(f"   ❌ {failed_test}")
            
            print(f"\n🔧 DIAGNÓSTICO DO PROBLEMA:")
            print(f"   Com base nos testes executados, as possíveis causas são:")
            
            # Analisar resultados para dar diagnóstico
            login_ok = any(r["test"] == "test_fabio_login" and r["success"] for r in self.test_results)
            tickets_found = any(r["test"] == "test_get_tickets_basic" and r["success"] for r in self.test_results)
            dept_access = any(r["test"] == "test_agent_departments_access" and r["success"] for r in self.test_results)
            dept_exists = any(r["test"] == "test_department_exists" and r["success"] for r in self.test_results)
            ticket_in_db = any(r["test"] == "test_ticket_exists_in_database" and r["success"] for r in self.test_results)
            
            if not login_ok:
                print(f"   1. ❌ PROBLEMA DE AUTENTICAÇÃO: Credenciais fabio123/102030ab incorretas")
            elif not ticket_in_db:
                print(f"   1. ❌ TICKET NÃO EXISTE: O ticket 'WhatsApp de Fabio Silva' não foi encontrado no banco")
            elif not dept_exists:
                print(f"   2. ❌ DEPARTAMENTO NÃO EXISTE: O departamento WHATSAPP 1 não foi encontrado")
            elif not dept_access:
                print(f"   3. ❌ SEM ACESSO AO DEPARTAMENTO: O agente fabio123 não tem acesso ao departamento WHATSAPP 1")
            elif not tickets_found:
                print(f"   4. ❌ FILTRO DE DEPARTAMENTO: O filtro de tickets por departamento não está funcionando")
            else:
                print(f"   5. ❌ PROBLEMA DESCONHECIDO: Todos os componentes parecem estar corretos")
            
            print(f"\n💡 AÇÕES RECOMENDADAS:")
            if not login_ok:
                print(f"   - Verificar se o agente fabio123 existe no banco")
                print(f"   - Verificar se a senha está correta")
            elif not ticket_in_db:
                print(f"   - Criar o ticket 'WhatsApp de Fabio Silva' no banco")
                print(f"   - Verificar se o nome do cliente está correto")
            elif not dept_exists:
                print(f"   - Criar o departamento WHATSAPP 1 com ID: {EXPECTED_DEPARTMENT_ID}")
            elif not dept_access:
                print(f"   - Adicionar o agente fabio123 ao departamento WHATSAPP 1")
                print(f"   - Verificar a tabela de vinculação agente-departamento")
            else:
                print(f"   - Verificar o código de filtro de tickets por departamento")
                print(f"   - Verificar se o isolamento multi-tenant está funcionando")
        
        return passed, total, self.test_results


if __name__ == "__main__":
    print("🎯 INICIANDO TESTE ESPECÍFICO DO REVIEW REQUEST")
    print("Testando endpoint /api/tickets para atendente fabio123")
    print()
    
    tester = FabioTicketsTest()
    passed, total, results = tester.run_all_tests()
    
    print(f"\n📋 RESUMO DETALHADO DOS TESTES:")
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['test']}: {result['message']}")
    
    exit_code = 0 if passed == total else 1
    exit(exit_code)