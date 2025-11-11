#!/usr/bin/env python3
"""
🧪 TESTE SISTEMÁTICO - ABA 8: AVISOS
Verificando se é duplicata da ABA 1 ou tem diferenças

FUNCIONALIDADES A TESTAR:
1. Login Admin - POST /api/auth/admin/login
2. Listar Avisos - GET /api/notices
3. Criar Aviso - POST /api/notices
4. Editar Aviso - PUT /api/notices/{notice_id}
5. Deletar Aviso - DELETE /api/notices/{notice_id}

Admin: admin@admin.com / 102030@ab
Backend: http://localhost:8001/api (mas usando REACT_APP_BACKEND_URL do .env)
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime

# Usar URL do backend do .env
BACKEND_URL = "https://wppconnect-fix.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "102030@ab"

class ABA8AvisosTester:
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
        if response_data and isinstance(response_data, dict):
            # Mostrar apenas campos relevantes para não poluir output
            if "token" in response_data:
                print(f"   Token: {response_data['token'][:50]}...")
            elif "id" in response_data:
                print(f"   ID: {response_data['id']}")
            elif isinstance(response_data, list):
                print(f"   Count: {len(response_data)} items")
            else:
                print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
        print()
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
    
    async def test_1_admin_login(self):
        """Teste 1: Login Admin"""
        print("🔐 TESTE 1: ADMIN LOGIN")
        print("=" * 50)
        
        try:
            login_data = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/admin/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get("token")
                    self.log_result("1. Admin Login", True, f"Login successful with {ADMIN_EMAIL}", {
                        "token": data.get("token", "")[:50] + "...",
                        "user_type": data.get("user_type"),
                        "user_data": data.get("user_data", {})
                    })
                    return True
                else:
                    error_text = await response.text()
                    self.log_result("1. Admin Login", False, f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_result("1. Admin Login", False, f"Exception: {str(e)}")
            return False
    
    async def test_2_listar_avisos(self):
        """Teste 2: Listar Avisos"""
        print("📋 TESTE 2: LISTAR AVISOS")
        print("=" * 50)
        
        if not self.auth_token:
            self.log_result("2. Listar Avisos", False, "No auth token available")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            async with self.session.get(f"{BACKEND_URL}/notices", headers=headers) as response:
                if response.status == 200:
                    notices = await response.json()
                    self.log_result("2. Listar Avisos", True, f"Retrieved {len(notices)} avisos", {
                        "count": len(notices),
                        "sample": notices[:2] if notices else []
                    })
                    return True
                else:
                    error_text = await response.text()
                    self.log_result("2. Listar Avisos", False, f"Status {response.status}: {error_text}")
                    return False
        except Exception as e:
            self.log_result("2. Listar Avisos", False, f"Exception: {str(e)}")
            return False
    
    async def test_3_criar_aviso(self):
        """Teste 3: Criar Aviso"""
        print("➕ TESTE 3: CRIAR AVISO")
        print("=" * 50)
        
        if not self.auth_token:
            self.log_result("3. Criar Aviso", False, "No auth token available")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            # Dados do aviso de teste
            aviso_data = {
                "title": "🧪 Teste ABA 8 - Sistema de Avisos",
                "message": "Este é um aviso de teste criado automaticamente para verificar se ABA 8 (Avisos) é igual à ABA 1 (Dashboard - Avisos). Teste realizado em " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "type": "info"
            }
            
            async with self.session.post(f"{BACKEND_URL}/notices", json=aviso_data, headers=headers) as response:
                if response.status in [200, 201]:
                    notice_data = await response.json()
                    self.created_notice_id = notice_data.get("id") or notice_data.get("notice_id")
                    self.log_result("3. Criar Aviso", True, "Aviso created successfully", {
                        "id": self.created_notice_id,
                        "title": notice_data.get("title"),
                        "type": notice_data.get("type")
                    })
                    return True
                else:
                    error_text = await response.text()
                    self.log_result("3. Criar Aviso", False, f"Status {response.status}: {error_text}")
                    return False
        except Exception as e:
            self.log_result("3. Criar Aviso", False, f"Exception: {str(e)}")
            return False
    
    async def test_4_editar_aviso(self):
        """Teste 4: Editar Aviso"""
        print("✏️ TESTE 4: EDITAR AVISO")
        print("=" * 50)
        
        if not self.auth_token:
            self.log_result("4. Editar Aviso", False, "No auth token available")
            return
        
        if not self.created_notice_id:
            self.log_result("4. Editar Aviso", False, "No notice ID available (create test failed)")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            # Dados atualizados do aviso
            updated_data = {
                "title": "🧪 Teste ABA 8 - Aviso EDITADO",
                "message": "Este aviso foi EDITADO com sucesso via PUT /api/notices/{notice_id}. Teste de edição realizado em " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "type": "success"
            }
            
            async with self.session.put(f"{BACKEND_URL}/notices/{self.created_notice_id}", json=updated_data, headers=headers) as response:
                if response.status == 200:
                    updated_notice = await response.json()
                    self.log_result("4. Editar Aviso", True, "Aviso updated successfully", {
                        "id": self.created_notice_id,
                        "new_title": updated_notice.get("title"),
                        "new_type": updated_notice.get("type")
                    })
                    return True
                else:
                    error_text = await response.text()
                    self.log_result("4. Editar Aviso", False, f"Status {response.status}: {error_text}")
                    return False
        except Exception as e:
            self.log_result("4. Editar Aviso", False, f"Exception: {str(e)}")
            return False
    
    async def test_5_deletar_aviso(self):
        """Teste 5: Deletar Aviso"""
        print("🗑️ TESTE 5: DELETAR AVISO")
        print("=" * 50)
        
        if not self.auth_token:
            self.log_result("5. Deletar Aviso", False, "No auth token available")
            return
        
        if not self.created_notice_id:
            self.log_result("5. Deletar Aviso", False, "No notice ID available (create test failed)")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            async with self.session.delete(f"{BACKEND_URL}/notices/{self.created_notice_id}", headers=headers) as response:
                if response.status == 200:
                    delete_response = await response.json()
                    self.log_result("5. Deletar Aviso", True, "Aviso deleted successfully", {
                        "deleted_id": self.created_notice_id,
                        "response": delete_response
                    })
                    return True
                else:
                    error_text = await response.text()
                    self.log_result("5. Deletar Aviso", False, f"Status {response.status}: {error_text}")
                    return False
        except Exception as e:
            self.log_result("5. Deletar Aviso", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all ABA 8 tests"""
        print("🧪 TESTE SISTEMÁTICO - ABA 8: AVISOS")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin Credentials: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        print("=" * 60)
        print()
        
        # Executar testes em sequência
        auth_success = await self.test_1_admin_login()
        
        if auth_success:
            await self.test_2_listar_avisos()
            await self.test_3_criar_aviso()
            await self.test_4_editar_aviso()
            await self.test_5_deletar_aviso()
        else:
            print("❌ Authentication failed - skipping other tests")
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 ABA 8 (AVISOS) - RESULTADO FINAL")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        print()
        
        if failed_tests > 0:
            print("❌ TESTES FALHARAM:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
            print()
        
        if passed_tests > 0:
            print("✅ TESTES PASSARAM:")
            for result in self.test_results:
                if result["success"]:
                    print(f"   • {result['test']}")
            print()
        
        print("=" * 60)
        
        # Conclusão sobre ABA 8 vs ABA 1
        if failed_tests == 0:
            print("🎉 CONCLUSÃO: ABA 8 (AVISOS) ESTÁ 100% FUNCIONAL!")
            print("✅ Confirmado: ABA 8 usa os mesmos endpoints da ABA 1 (Dashboard - Avisos)")
            print("✅ Todas as 5 funcionalidades funcionam perfeitamente:")
            print("   1. ✅ Login Admin")
            print("   2. ✅ Listar Avisos")
            print("   3. ✅ Criar Aviso")
            print("   4. ✅ Editar Aviso")
            print("   5. ✅ Deletar Aviso")
            print()
            print("🎯 RECOMENDAÇÃO: Pode avançar para ABA 9 (Auto-Responder)")
        else:
            print(f"⚠️ PROBLEMAS ENCONTRADOS: {failed_tests} funcionalidades com erro")
            print("🔧 Necessário corrigir antes de avançar para próxima ABA")

async def main():
    """Main test execution"""
    async with ABA8AvisosTester() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())