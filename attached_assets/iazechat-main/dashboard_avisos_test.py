#!/usr/bin/env python3
"""
🧪 TESTE SISTEMÁTICO - ABA 1: DASHBOARD (AVISOS)

CONTEXTO CRÍTICO:
- Usuário reporta que TODAS as funcionalidades das ABAs não funcionam
- Preciso testar ABA POR ABA, funcionalidade por funcionalidade
- URL Backend: Usar REACT_APP_BACKEND_URL do .env do frontend
- Admin: admin@admin.com / senha: 102030@ab

ABA 1 - DASHBOARD (AVISOS) - FUNCIONALIDADES A TESTAR:

1. LOGIN ADMIN (pré-requisito)
   - POST /api/auth/admin/login
   - Body: {"password": "102030@ab"}
   - Deve retornar token JWT válido

2. LISTAR AVISOS
   - GET /api/notices
   - Header: Authorization: Bearer {token}
   - Deve retornar lista de avisos

3. CRIAR NOVO AVISO
   - POST /api/notices
   - Header: Authorization: Bearer {token}
   - Body: {"title": "Teste Aviso 1", "message": "Mensagem de teste", "type": "info"}
   - Deve criar aviso e retornar success

4. EDITAR AVISO (se houver endpoint)
   - PUT /api/notices/{notice_id}
   - Testar atualização de título/mensagem

5. DELETAR AVISO
   - DELETE /api/notices/{notice_id}
   - Header: Authorization: Bearer {token}
   - Deve deletar aviso e retornar success

CRITÉRIOS DE SUCESSO:
✅ Todas as 5 funcionalidades devem funcionar sem erro
✅ Responses devem retornar status 200/201
✅ Dados devem ser persistidos no MongoDB
✅ Erros devem ser reportados com detalhes
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime
import os

# Configuration - Use localhost for testing (backend runs on port 8001)
BACKEND_URL = "http://localhost:8001/api"
ADMIN_PASSWORD = "102030@ab"

class DashboardAvisosTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_results = []
        self.created_notice_id = None
        
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
        """1. LOGIN ADMIN (pré-requisito)"""
        print("🔐 TESTE 1: LOGIN ADMIN")
        print("=" * 50)
        
        try:
            # Admin login with password only (as per review request)
            login_data = {
                "password": ADMIN_PASSWORD
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/admin/login", json=login_data) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        data = json.loads(response_text)
                        self.auth_token = data.get("token")
                        
                        if self.auth_token:
                            self.log_result("1. Admin Login", True, f"Login successful, token received (admin@admin.com)", {
                                "status": response.status,
                                "token_length": len(self.auth_token),
                                "user_type": data.get("user_type"),
                                "user_data": data.get("user_data")
                            })
                            return True
                        else:
                            self.log_result("1. Admin Login", False, "No token in response", data)
                            return False
                    except json.JSONDecodeError:
                        self.log_result("1. Admin Login", False, f"Invalid JSON response: {response_text}")
                        return False
                else:
                    self.log_result("1. Admin Login", False, f"Status {response.status}: {response_text}")
                    return False
                    
        except Exception as e:
            import traceback
            error_details = f"Exception: {str(e)}\nTraceback: {traceback.format_exc()}"
            self.log_result("1. Admin Login", False, error_details)
            return False
    
    async def test_2_listar_avisos(self):
        """2. LISTAR AVISOS"""
        print("📋 TESTE 2: LISTAR AVISOS")
        print("=" * 50)
        
        if not self.auth_token:
            self.log_result("2. Listar Avisos", False, "No auth token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            async with self.session.get(f"{BACKEND_URL}/notices", headers=headers) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        notices = json.loads(response_text)
                        self.log_result("2. Listar Avisos", True, f"Retrieved {len(notices)} avisos", {
                            "status": response.status,
                            "count": len(notices),
                            "notices": notices[:2] if notices else []  # Show first 2 notices
                        })
                        return True
                    except json.JSONDecodeError:
                        self.log_result("2. Listar Avisos", False, f"Invalid JSON response: {response_text}")
                        return False
                else:
                    self.log_result("2. Listar Avisos", False, f"Status {response.status}: {response_text}")
                    return False
        except Exception as e:
            self.log_result("2. Listar Avisos", False, f"Exception: {str(e)}")
            return False
    
    async def test_3_criar_aviso(self):
        """3. CRIAR NOVO AVISO"""
        print("➕ TESTE 3: CRIAR NOVO AVISO")
        print("=" * 50)
        
        if not self.auth_token:
            self.log_result("3. Criar Aviso", False, "No auth token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Create notice with real-looking data
        notice_data = {
            "title": "Manutenção Programada do Sistema",
            "message": "Informamos que haverá manutenção programada no sistema no dia 15/01/2025 das 02:00 às 04:00. Durante este período, alguns serviços podem ficar indisponíveis.",
            "type": "warning"
        }
        
        try:
            async with self.session.post(f"{BACKEND_URL}/notices", json=notice_data, headers=headers) as response:
                response_text = await response.text()
                
                if response.status in [200, 201]:
                    try:
                        data = json.loads(response_text)
                        # Try to extract notice ID for later tests
                        self.created_notice_id = data.get("id") or data.get("notice_id") or data.get("_id")
                        
                        self.log_result("3. Criar Aviso", True, "Aviso criado com sucesso", {
                            "status": response.status,
                            "notice_id": self.created_notice_id,
                            "response": data
                        })
                        return True
                    except json.JSONDecodeError:
                        self.log_result("3. Criar Aviso", False, f"Invalid JSON response: {response_text}")
                        return False
                else:
                    self.log_result("3. Criar Aviso", False, f"Status {response.status}: {response_text}")
                    return False
        except Exception as e:
            self.log_result("3. Criar Aviso", False, f"Exception: {str(e)}")
            return False
    
    async def test_4_editar_aviso(self):
        """4. EDITAR AVISO (se houver endpoint)"""
        print("✏️ TESTE 4: EDITAR AVISO")
        print("=" * 50)
        
        if not self.auth_token:
            self.log_result("4. Editar Aviso", False, "No auth token available")
            return False
        
        if not self.created_notice_id:
            self.log_result("4. Editar Aviso", False, "No notice ID available from creation test")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Updated notice data
        updated_notice_data = {
            "title": "Manutenção Programada do Sistema - ATUALIZADO",
            "message": "ATUALIZAÇÃO: A manutenção foi reagendada para o dia 16/01/2025 das 03:00 às 05:00. Pedimos desculpas pelo inconveniente.",
            "type": "info"
        }
        
        try:
            async with self.session.put(f"{BACKEND_URL}/notices/{self.created_notice_id}", json=updated_notice_data, headers=headers) as response:
                response_text = await response.text()
                
                if response.status in [200, 201]:
                    try:
                        data = json.loads(response_text)
                        self.log_result("4. Editar Aviso", True, "Aviso editado com sucesso", {
                            "status": response.status,
                            "notice_id": self.created_notice_id,
                            "response": data
                        })
                        return True
                    except json.JSONDecodeError:
                        self.log_result("4. Editar Aviso", False, f"Invalid JSON response: {response_text}")
                        return False
                else:
                    self.log_result("4. Editar Aviso", False, f"Status {response.status}: {response_text}")
                    return False
        except Exception as e:
            self.log_result("4. Editar Aviso", False, f"Exception: {str(e)}")
            return False
    
    async def test_5_deletar_aviso(self):
        """5. DELETAR AVISO"""
        print("🗑️ TESTE 5: DELETAR AVISO")
        print("=" * 50)
        
        if not self.auth_token:
            self.log_result("5. Deletar Aviso", False, "No auth token available")
            return False
        
        if not self.created_notice_id:
            self.log_result("5. Deletar Aviso", False, "No notice ID available from creation test")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            async with self.session.delete(f"{BACKEND_URL}/notices/{self.created_notice_id}", headers=headers) as response:
                response_text = await response.text()
                
                if response.status in [200, 204]:
                    try:
                        # DELETE might return empty response (204) or JSON (200)
                        data = json.loads(response_text) if response_text else {"deleted": True}
                        self.log_result("5. Deletar Aviso", True, "Aviso deletado com sucesso", {
                            "status": response.status,
                            "notice_id": self.created_notice_id,
                            "response": data
                        })
                        return True
                    except json.JSONDecodeError:
                        # If 204 No Content, it's still success
                        if response.status == 204:
                            self.log_result("5. Deletar Aviso", True, "Aviso deletado com sucesso (204 No Content)", {
                                "status": response.status,
                                "notice_id": self.created_notice_id
                            })
                            return True
                        else:
                            self.log_result("5. Deletar Aviso", False, f"Invalid JSON response: {response_text}")
                            return False
                else:
                    self.log_result("5. Deletar Aviso", False, f"Status {response.status}: {response_text}")
                    return False
        except Exception as e:
            self.log_result("5. Deletar Aviso", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all Dashboard (Avisos) tests"""
        print("🧪 TESTE SISTEMÁTICO - ABA 1: DASHBOARD (AVISOS)")
        print("=" * 70)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin Password: {ADMIN_PASSWORD}")
        print("=" * 70)
        print()
        
        # Test sequence - each test depends on previous ones
        test_1_success = await self.test_1_admin_login()
        
        if test_1_success:
            test_2_success = await self.test_2_listar_avisos()
            test_3_success = await self.test_3_criar_aviso()
            
            # Tests 4 and 5 depend on test 3 creating a notice
            if test_3_success:
                await self.test_4_editar_aviso()
                await self.test_5_deletar_aviso()
            else:
                self.log_result("4. Editar Aviso", False, "Skipped - notice creation failed")
                self.log_result("5. Deletar Aviso", False, "Skipped - notice creation failed")
        else:
            print("❌ Authentication failed - skipping all other tests")
            self.log_result("2. Listar Avisos", False, "Skipped - authentication failed")
            self.log_result("3. Criar Aviso", False, "Skipped - authentication failed")
            self.log_result("4. Editar Aviso", False, "Skipped - authentication failed")
            self.log_result("5. Deletar Aviso", False, "Skipped - authentication failed")
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 RESUMO DOS TESTES - ABA 1: DASHBOARD (AVISOS)")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total de Testes: {total_tests}")
        print(f"✅ Aprovados: {passed_tests}")
        print(f"❌ Falharam: {failed_tests}")
        print(f"Taxa de Sucesso: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        print()
        
        if failed_tests > 0:
            print("❌ TESTES QUE FALHARAM:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
            print()
        
        if passed_tests > 0:
            print("✅ TESTES QUE PASSARAM:")
            for result in self.test_results:
                if result["success"]:
                    print(f"   • {result['test']}")
            print()
        
        print("=" * 70)
        print("🎯 CRITÉRIOS DE SUCESSO:")
        print("   ✅ Todas as 5 funcionalidades devem funcionar sem erro")
        print("   ✅ Responses devem retornar status 200/201")
        print("   ✅ Dados devem ser persistidos no MongoDB")
        print("   ✅ Erros devem ser reportados com detalhes")
        print()
        
        if failed_tests == 0:
            print("🎉 TODOS OS TESTES PASSARAM! ABA 1 (DASHBOARD - AVISOS) ESTÁ FUNCIONANDO!")
            print("✅ Pode avançar para próxima ABA")
        else:
            print(f"⚠️ {failed_tests} funcionalidades ainda precisam de correção")
            print("❌ NÃO avançar para próxima ABA até resolver os problemas")
        
        print("=" * 70)

async def main():
    """Main test execution"""
    async with DashboardAvisosTester() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())