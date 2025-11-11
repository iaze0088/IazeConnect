#!/usr/bin/env python3
"""
TESTE ABRANGENTE: Verificar funcionalidades principais do sistema

CONTEXTO:
- Usuário reportou que "opções dentro do dashboard não estão funcionando corretamente"
- URL: https://wppconnect-fix.preview.emergentagent.com
- Preciso testar as principais funcionalidades do sistema

TESTES SOLICITADOS:

1. **Login Admin**:
   - POST /api/auth/admin/login
   - Body: {"email": "admin@admin.com", "password": "102030@ab"}
   - Salvar token para usar nos próximos testes

2. **Config - Buscar configuração**:
   - GET /api/config
   - Header: Authorization: Bearer {token}
   - Verificar se retorna config

3. **Config - Salvar configuração**:
   - POST /api/config
   - Header: Authorization: Bearer {token}
   - Body: Testar salvar uma config simples
   - Verificar se retorna 200 OK

4. **Agentes - Listar**:
   - GET /api/agents
   - Header: Authorization: Bearer {token}
   - Verificar se retorna lista

5. **Agentes - Criar**:
   - POST /api/agents
   - Header: Authorization: Bearer {token}
   - Body: {
       "name": "Teste Agent",
       "login": "testagent",
       "password": "123456",
       "email": "test@test.com"
     }
   - Verificar se cria com sucesso

6. **Revendas - Listar**:
   - GET /api/resellers
   - Header: Authorization: Bearer {token}
   - Verificar se retorna lista

7. **Departamentos - Listar**:
   - GET /api/ai/departments
   - Header: Authorization: Bearer {token}
   - Verificar se retorna lista

8. **AI Agents - Listar**:
   - GET /api/ai/agents
   - Header: Authorization: Bearer {token}
   - Verificar se retorna lista

9. **Backup - Listar**:
   - GET /api/admin/backup/list
   - Header: Authorization: Bearer {token}
   - Verificar se retorna lista de backups

10. **Office Sync - Search**:
    - POST /api/office-sync/search-clients
    - Header: Authorization: Bearer {token}
    - Body: {}
    - Verificar se retorna clientes sincronizados

OBJETIVO: Identificar quais endpoints estão falhando e qual é o erro exato.
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

# Configurações do teste
BACKEND_URL = "http://localhost:8001"  # Using localhost for testing due to external URL timeout
API_BASE = f"{BACKEND_URL}/api"

# Credenciais conforme review request
ADMIN_EMAIL = "admin@admin.com"  # Nota: O sistema usa apenas password, não email
ADMIN_PASSWORD = "102030@ab"

class DashboardFunctionalityTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.test_results = []
        self.created_test_data = []  # Para cleanup
        
    async def setup_session(self):
        """Configurar sessão HTTP"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        
    async def cleanup_session(self):
        """Limpar sessão HTTP"""
        if self.session:
            await self.session.close()
            
    def log_result(self, test_name: str, success: bool, message: str = "", details: dict = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}"
        if message:
            result += f" - {message}"
        print(result)
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {}
        })
        
    async def make_request(self, method: str, endpoint: str, data: dict = None, 
                          token: str = None, headers: dict = None) -> Tuple[bool, dict, int]:
        """Make HTTP request with error handling"""
        url = f"{API_BASE}{endpoint}"
        
        request_headers = {"Content-Type": "application/json"}
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        if headers:
            request_headers.update(headers)
            
        try:
            if method.upper() == "GET":
                async with self.session.get(url, headers=request_headers) as response:
                    status = response.status
                    try:
                        data_response = await response.json()
                    except:
                        data_response = {"text": await response.text()}
                    return status < 400, data_response, status
                    
            elif method.upper() == "POST":
                async with self.session.post(url, json=data, headers=request_headers) as response:
                    status = response.status
                    try:
                        data_response = await response.json()
                    except:
                        data_response = {"text": await response.text()}
                    return status < 400, data_response, status
                    
            elif method.upper() == "PUT":
                async with self.session.put(url, json=data, headers=request_headers) as response:
                    status = response.status
                    try:
                        data_response = await response.json()
                    except:
                        data_response = {"text": await response.text()}
                    return status < 400, data_response, status
                    
            else:
                return False, {"error": f"Unsupported method: {method}"}, 400
                
        except Exception as e:
            return False, {"error": str(e)}, 500
    
    async def test_1_admin_login(self) -> bool:
        """Teste 1: Login Admin"""
        print("\n🔐 TESTE 1: Login Admin")
        print("=" * 60)
        
        # Nota: O sistema usa apenas password, não email no login admin
        login_data = {"password": ADMIN_PASSWORD}
        
        success, response, status = await self.make_request("POST", "/auth/admin/login", login_data)
        
        print(f"📊 Status: {status}")
        print(f"📄 Response: {json.dumps(response, indent=2)}")
        
        if success and "token" in response:
            self.admin_token = response["token"]
            user_data = response.get("user_data", {})
            self.log_result(
                "Admin Login", 
                True, 
                f"Login successful, user_type: {response.get('user_type')}", 
                {"token": self.admin_token[:50] + "...", "user_data": user_data}
            )
            print(f"✅ Token obtido: {self.admin_token[:50]}...")
            return True
        else:
            self.log_result(
                "Admin Login", 
                False, 
                f"Status {status}: {response.get('detail', response)}"
            )
            return False
    
    async def test_2_config_get(self) -> bool:
        """Teste 2: Config - Buscar configuração"""
        print("\n⚙️ TESTE 2: Config - Buscar configuração")
        print("=" * 60)
        
        if not self.admin_token:
            self.log_result("Config Get", False, "Admin token required")
            return False
        
        success, response, status = await self.make_request("GET", "/config", token=self.admin_token)
        
        print(f"📊 Status: {status}")
        print(f"📄 Response keys: {list(response.keys()) if isinstance(response, dict) else 'Not dict'}")
        
        if success:
            # Verificar se tem campos esperados de config
            expected_fields = ["quick_blocks", "auto_reply", "apps"]
            has_expected = any(field in response for field in expected_fields)
            
            if has_expected:
                self.log_result(
                    "Config Get", 
                    True, 
                    f"Config retrieved with {len(response)} fields",
                    {"fields": list(response.keys())[:10]}  # Primeiros 10 campos
                )
                return True
            else:
                self.log_result(
                    "Config Get", 
                    False, 
                    f"Config missing expected fields. Got: {list(response.keys())[:5]}"
                )
                return False
        else:
            self.log_result(
                "Config Get", 
                False, 
                f"Status {status}: {response.get('detail', response)}"
            )
            return False
    
    async def test_3_config_save(self) -> bool:
        """Teste 3: Config - Salvar configuração"""
        print("\n💾 TESTE 3: Config - Salvar configuração")
        print("=" * 60)
        
        if not self.admin_token:
            self.log_result("Config Save", False, "Admin token required")
            return False
        
        # Testar salvar uma config simples
        test_config = {
            "quick_blocks": [
                {"text": "Teste config save", "active": True}
            ],
            "auto_reply": {
                "enabled": True,
                "message": "Teste auto reply"
            }
        }
        
        success, response, status = await self.make_request("PUT", "/config", test_config, token=self.admin_token)
        
        print(f"📊 Status: {status}")
        print(f"📄 Response: {json.dumps(response, indent=2)}")
        
        if success and status == 200:
            self.log_result(
                "Config Save", 
                True, 
                "Config saved successfully",
                {"status": status, "response": response}
            )
            return True
        else:
            self.log_result(
                "Config Save", 
                False, 
                f"Status {status}: {response.get('detail', response)}"
            )
            return False
    
    async def test_4_agents_list(self) -> bool:
        """Teste 4: Agentes - Listar"""
        print("\n👥 TESTE 4: Agentes - Listar")
        print("=" * 60)
        
        if not self.admin_token:
            self.log_result("Agents List", False, "Admin token required")
            return False
        
        success, response, status = await self.make_request("GET", "/agents", token=self.admin_token)
        
        print(f"📊 Status: {status}")
        print(f"📄 Response: {len(response) if isinstance(response, list) else 'Not list'} agents")
        
        if success and isinstance(response, list):
            self.log_result(
                "Agents List", 
                True, 
                f"Retrieved {len(response)} agents",
                {"count": len(response), "sample": response[:2] if response else []}
            )
            return True
        else:
            self.log_result(
                "Agents List", 
                False, 
                f"Status {status}: {response.get('detail', response) if isinstance(response, dict) else response}"
            )
            return False
    
    async def test_5_agents_create(self) -> bool:
        """Teste 5: Agentes - Criar"""
        print("\n➕ TESTE 5: Agentes - Criar")
        print("=" * 60)
        
        if not self.admin_token:
            self.log_result("Agents Create", False, "Admin token required")
            return False
        
        # Dados do agente de teste conforme review request
        agent_data = {
            "name": "Teste Agent",
            "login": "testagent",
            "password": "123456",
            "email": "test@test.com"
        }
        
        success, response, status = await self.make_request("POST", "/agents", agent_data, token=self.admin_token)
        
        print(f"📊 Status: {status}")
        print(f"📄 Response: {json.dumps(response, indent=2)}")
        
        if success and response.get("ok"):
            agent_id = response.get("id")
            if agent_id:
                self.created_test_data.append(("agent", agent_id))
            self.log_result(
                "Agents Create", 
                True, 
                f"Agent created successfully, ID: {agent_id}",
                {"agent_id": agent_id, "response": response}
            )
            return True
        else:
            self.log_result(
                "Agents Create", 
                False, 
                f"Status {status}: {response.get('detail', response)}"
            )
            return False
    
    async def test_6_resellers_list(self) -> bool:
        """Teste 6: Revendas - Listar"""
        print("\n🏢 TESTE 6: Revendas - Listar")
        print("=" * 60)
        
        if not self.admin_token:
            self.log_result("Resellers List", False, "Admin token required")
            return False
        
        success, response, status = await self.make_request("GET", "/resellers", token=self.admin_token)
        
        print(f"📊 Status: {status}")
        print(f"📄 Response: {len(response) if isinstance(response, list) else 'Not list'} resellers")
        
        if success and isinstance(response, list):
            self.log_result(
                "Resellers List", 
                True, 
                f"Retrieved {len(response)} resellers",
                {"count": len(response), "sample": response[:2] if response else []}
            )
            return True
        else:
            self.log_result(
                "Resellers List", 
                False, 
                f"Status {status}: {response.get('detail', response) if isinstance(response, dict) else response}"
            )
            return False
    
    async def test_7_departments_list(self) -> bool:
        """Teste 7: Departamentos - Listar"""
        print("\n🏛️ TESTE 7: Departamentos - Listar")
        print("=" * 60)
        
        if not self.admin_token:
            self.log_result("Departments List", False, "Admin token required")
            return False
        
        success, response, status = await self.make_request("GET", "/ai/departments", token=self.admin_token)
        
        print(f"📊 Status: {status}")
        print(f"📄 Response: {len(response) if isinstance(response, list) else 'Not list'} departments")
        
        if success and isinstance(response, list):
            self.log_result(
                "Departments List", 
                True, 
                f"Retrieved {len(response)} departments",
                {"count": len(response), "sample": response[:2] if response else []}
            )
            return True
        else:
            self.log_result(
                "Departments List", 
                False, 
                f"Status {status}: {response.get('detail', response) if isinstance(response, dict) else response}"
            )
            return False
    
    async def test_8_ai_agents_list(self) -> bool:
        """Teste 8: AI Agents - Listar"""
        print("\n🤖 TESTE 8: AI Agents - Listar")
        print("=" * 60)
        
        if not self.admin_token:
            self.log_result("AI Agents List", False, "Admin token required")
            return False
        
        success, response, status = await self.make_request("GET", "/ai/agents", token=self.admin_token)
        
        print(f"📊 Status: {status}")
        print(f"📄 Response: {len(response) if isinstance(response, list) else 'Not list'} AI agents")
        
        if success and isinstance(response, list):
            self.log_result(
                "AI Agents List", 
                True, 
                f"Retrieved {len(response)} AI agents",
                {"count": len(response), "sample": response[:2] if response else []}
            )
            return True
        else:
            self.log_result(
                "AI Agents List", 
                False, 
                f"Status {status}: {response.get('detail', response) if isinstance(response, dict) else response}"
            )
            return False
    
    async def test_9_backup_list(self) -> bool:
        """Teste 9: Backup - Listar"""
        print("\n💾 TESTE 9: Backup - Listar")
        print("=" * 60)
        
        if not self.admin_token:
            self.log_result("Backup List", False, "Admin token required")
            return False
        
        success, response, status = await self.make_request("GET", "/admin/backup/list", token=self.admin_token)
        
        print(f"📊 Status: {status}")
        print(f"📄 Response: {json.dumps(response, indent=2) if isinstance(response, dict) else response}")
        
        if success:
            # Backup pode retornar dict com lista ou lista direta
            if isinstance(response, dict) and "backups" in response:
                backup_count = len(response["backups"])
            elif isinstance(response, list):
                backup_count = len(response)
            else:
                backup_count = "unknown"
            
            self.log_result(
                "Backup List", 
                True, 
                f"Retrieved backup list, count: {backup_count}",
                {"response": response}
            )
            return True
        else:
            self.log_result(
                "Backup List", 
                False, 
                f"Status {status}: {response.get('detail', response) if isinstance(response, dict) else response}"
            )
            return False
    
    async def test_10_office_sync_search(self) -> bool:
        """Teste 10: Office Sync - Search"""
        print("\n🔍 TESTE 10: Office Sync - Search")
        print("=" * 60)
        
        if not self.admin_token:
            self.log_result("Office Sync Search", False, "Admin token required")
            return False
        
        # Body vazio conforme review request
        search_data = {}
        
        success, response, status = await self.make_request("POST", "/office-sync/search-clients", search_data, token=self.admin_token)
        
        print(f"📊 Status: {status}")
        print(f"📄 Response: {json.dumps(response, indent=2) if isinstance(response, dict) else response}")
        
        if success:
            # Office sync pode retornar diferentes estruturas
            if isinstance(response, dict):
                if "clients" in response:
                    client_count = len(response["clients"])
                elif "results" in response:
                    client_count = len(response["results"])
                else:
                    client_count = "unknown structure"
            elif isinstance(response, list):
                client_count = len(response)
            else:
                client_count = "unknown"
            
            self.log_result(
                "Office Sync Search", 
                True, 
                f"Search completed, clients: {client_count}",
                {"response": response}
            )
            return True
        else:
            self.log_result(
                "Office Sync Search", 
                False, 
                f"Status {status}: {response.get('detail', response) if isinstance(response, dict) else response}"
            )
            return False
    
    async def cleanup_test_data(self):
        """Limpar dados de teste criados"""
        if not self.created_test_data or not self.admin_token:
            return
        
        print("\n🧹 Limpando dados de teste...")
        
        for data_type, data_id in self.created_test_data:
            if data_type == "agent":
                success, response, status = await self.make_request("DELETE", f"/agents/{data_id}", token=self.admin_token)
                if success:
                    print(f"✅ Agent {data_id} removido")
                else:
                    print(f"❌ Falha ao remover agent {data_id}: {response}")
    
    async def run_all_tests(self):
        """Executar todos os testes"""
        print("🚀 TESTE ABRANGENTE: Verificar funcionalidades principais do sistema")
        print("=" * 80)
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print(f"🔑 Admin Password: {ADMIN_PASSWORD}")
        print("=" * 80)
        
        try:
            await self.setup_session()
            
            # Lista de testes na ordem especificada
            tests = [
                self.test_1_admin_login,
                self.test_2_config_get,
                self.test_3_config_save,
                self.test_4_agents_list,
                self.test_5_agents_create,
                self.test_6_resellers_list,
                self.test_7_departments_list,
                self.test_8_ai_agents_list,
                self.test_9_backup_list,
                self.test_10_office_sync_search,
            ]
            
            passed = 0
            total = len(tests)
            failed_tests = []
            
            for test in tests:
                try:
                    print(f"\n🔄 Executando: {test.__name__}")
                    if await test():
                        passed += 1
                        print(f"✅ {test.__name__} PASSOU")
                    else:
                        failed_tests.append(test.__name__)
                        print(f"❌ {test.__name__} FALHOU")
                    
                    # Pequena pausa entre testes
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    self.log_result(test.__name__, False, f"Exception: {str(e)}")
                    failed_tests.append(test.__name__)
                    print(f"💥 {test.__name__} ERRO: {str(e)}")
            
            # Cleanup
            await self.cleanup_test_data()
            
            # Resumo final
            print("\n" + "=" * 80)
            print("📊 RESUMO FINAL DOS TESTES")
            print("=" * 80)
            
            print(f"📈 Total de testes: {total}")
            print(f"✅ Testes passaram: {passed}")
            print(f"❌ Testes falharam: {total - passed}")
            print(f"📊 Taxa de sucesso: {(passed/total)*100:.1f}%")
            
            print("\n📋 DETALHES DOS TESTES:")
            for i, result in enumerate(self.test_results, 1):
                status_icon = "✅" if result["success"] else "❌"
                print(f"{i:2d}. {status_icon} {result['test']}")
                if result["message"]:
                    print(f"     {result['message']}")
                if not result["success"] and result["details"]:
                    print(f"     Details: {result['details']}")
            
            # Análise específica dos endpoints que falharam
            if failed_tests:
                print("\n🔍 ANÁLISE DOS ENDPOINTS QUE FALHARAM:")
                for failed_test in failed_tests:
                    # Encontrar resultado do teste
                    test_result = next((r for r in self.test_results if failed_test in r["test"]), None)
                    if test_result:
                        print(f"\n❌ {failed_test}:")
                        print(f"   Erro: {test_result['message']}")
                        if test_result['details']:
                            print(f"   Detalhes: {test_result['details']}")
            
            # Conclusão
            if passed == total:
                print("\n🎉 RESULTADO FINAL: TODAS AS FUNCIONALIDADES DO DASHBOARD ESTÃO FUNCIONANDO!")
                print("✅ Nenhum problema detectado nas opções do dashboard")
            else:
                print(f"\n⚠️ RESULTADO FINAL: {total - passed} PROBLEMAS DETECTADOS NO DASHBOARD")
                print("🔧 Endpoints com falha precisam ser investigados:")
                for failed_test in failed_tests:
                    print(f"   - {failed_test}")
            
            return passed == total
            
        except Exception as e:
            print(f"💥 ERRO CRÍTICO durante execução dos testes: {e}")
            return False
        finally:
            await self.cleanup_session()

async def main():
    """Função principal"""
    tester = DashboardFunctionalityTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎯 CONCLUSÃO: Todas as funcionalidades do dashboard estão funcionando corretamente!")
        exit(0)
    else:
        print("\n⚠️ CONCLUSÃO: Problemas detectados em algumas funcionalidades do dashboard!")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())