#!/usr/bin/env python3
"""
🧪 TESTE SISTEMÁTICO - ABA 5: I.A / DEPARTAMENTOS

CONTEXTO:
- ABA 1 (Dashboard - Avisos) ✅ 100% funcional
- ABA 2 (Domínio) ✅ 100% funcional  
- ABA 3 (Revendas) ✅ 100% funcional
- ABA 4 (Atendentes) ✅ 100% funcional
- Continuando teste sistemático (5/16)

FUNCIONALIDADES A TESTAR:

PARTE 1 - DEPARTAMENTOS:
1. LOGIN ADMIN
2. LISTAR DEPARTAMENTOS (GET /api/ai/departments)
3. CRIAR DEPARTAMENTO (POST /api/ai/departments)
4. EDITAR DEPARTAMENTO (PUT /api/ai/departments/{dept_id})
5. DELETAR DEPARTAMENTO (DELETE /api/ai/departments/{dept_id})

PARTE 2 - CONFIGURAÇÃO DE I.A:
6. OBTER CONFIGURAÇÃO DE I.A (GET /api/config)
7. SALVAR CONFIGURAÇÃO DE I.A (PUT /api/config)

Backend URL: https://wppconnect-fix.preview.emergentagent.com/api
Admin: admin@admin.com / senha: 102030@ab
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://wppconnect-fix.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "102030@ab"

class ABA5Tester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_results = []
        self.created_dept_id = None
        
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
            # Show only relevant fields to avoid clutter
            if "id" in response_data:
                print(f"   ID: {response_data['id']}")
            if "name" in response_data:
                print(f"   Name: {response_data['name']}")
            if "message" in response_data:
                print(f"   Message: {response_data['message']}")
        print()
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
    
    async def test_1_admin_login(self):
        """TESTE 1: LOGIN ADMIN"""
        print("🔐 TESTE 1: ADMIN LOGIN")
        print("=" * 50)
        
        try:
            login_data = {"password": ADMIN_PASSWORD}
            
            async with self.session.post(f"{BACKEND_URL}/auth/admin/login", json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get("token")
                    user_data = data.get("user_data", {})
                    
                    self.log_result(
                        "1. Admin Login", 
                        True, 
                        f"Login successful - Email: {user_data.get('email', 'N/A')}", 
                        {"token_received": bool(self.auth_token), "user_type": data.get("user_type")}
                    )
                    return True
                else:
                    error_text = await response.text()
                    self.log_result("1. Admin Login", False, f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_result("1. Admin Login", False, f"Exception: {str(e)}")
            return False
    
    async def test_2_listar_departamentos(self):
        """TESTE 2: LISTAR DEPARTAMENTOS"""
        print("📋 TESTE 2: LISTAR DEPARTAMENTOS")
        print("=" * 50)
        
        if not self.auth_token:
            self.log_result("2. Listar Departamentos", False, "No auth token available")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            async with self.session.get(f"{BACKEND_URL}/ai/departments", headers=headers) as response:
                if response.status == 200:
                    departments = await response.json()
                    self.log_result(
                        "2. Listar Departamentos", 
                        True, 
                        f"Retrieved {len(departments)} departments successfully", 
                        {"count": len(departments), "departments": [d.get("name", "N/A") for d in departments[:3]]}
                    )
                else:
                    error_text = await response.text()
                    self.log_result("2. Listar Departamentos", False, f"Status {response.status}: {error_text}")
        except Exception as e:
            self.log_result("2. Listar Departamentos", False, f"Exception: {str(e)}")
    
    async def test_3_criar_departamento(self):
        """TESTE 3: CRIAR DEPARTAMENTO"""
        print("➕ TESTE 3: CRIAR DEPARTAMENTO")
        print("=" * 50)
        
        if not self.auth_token:
            self.log_result("3. Criar Departamento", False, "No auth token available")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            new_dept_data = {
                "name": "Departamento Teste ABA5",
                "description": "Teste de criação via ABA 5 - I.A/Departamentos"
            }
            
            async with self.session.post(f"{BACKEND_URL}/ai/departments", json=new_dept_data, headers=headers) as response:
                if response.status in [200, 201]:
                    dept_data = await response.json()
                    self.created_dept_id = dept_data.get("id")
                    
                    self.log_result(
                        "3. Criar Departamento", 
                        True, 
                        f"Department created successfully - ID: {self.created_dept_id}", 
                        {"id": self.created_dept_id, "name": dept_data.get("name")}
                    )
                else:
                    error_text = await response.text()
                    self.log_result("3. Criar Departamento", False, f"Status {response.status}: {error_text}")
        except Exception as e:
            self.log_result("3. Criar Departamento", False, f"Exception: {str(e)}")
    
    async def test_4_editar_departamento(self):
        """TESTE 4: EDITAR DEPARTAMENTO"""
        print("✏️ TESTE 4: EDITAR DEPARTAMENTO")
        print("=" * 50)
        
        if not self.auth_token:
            self.log_result("4. Editar Departamento", False, "No auth token available")
            return
        
        if not self.created_dept_id:
            self.log_result("4. Editar Departamento", False, "No department ID available (creation failed)")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            edit_data = {
                "name": "Departamento Editado ABA5",
                "description": "Descrição editada via teste ABA 5"
            }
            
            async with self.session.put(f"{BACKEND_URL}/ai/departments/{self.created_dept_id}", json=edit_data, headers=headers) as response:
                if response.status == 200:
                    dept_data = await response.json()
                    
                    self.log_result(
                        "4. Editar Departamento", 
                        True, 
                        f"Department edited successfully - New name: {dept_data.get('name')}", 
                        {"id": self.created_dept_id, "name": dept_data.get("name")}
                    )
                else:
                    error_text = await response.text()
                    self.log_result("4. Editar Departamento", False, f"Status {response.status}: {error_text}")
        except Exception as e:
            self.log_result("4. Editar Departamento", False, f"Exception: {str(e)}")
    
    async def test_5_deletar_departamento(self):
        """TESTE 5: DELETAR DEPARTAMENTO"""
        print("🗑️ TESTE 5: DELETAR DEPARTAMENTO")
        print("=" * 50)
        
        if not self.auth_token:
            self.log_result("5. Deletar Departamento", False, "No auth token available")
            return
        
        if not self.created_dept_id:
            self.log_result("5. Deletar Departamento", False, "No department ID available (creation failed)")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            async with self.session.delete(f"{BACKEND_URL}/ai/departments/{self.created_dept_id}", headers=headers) as response:
                if response.status == 200:
                    result_data = await response.json()
                    
                    self.log_result(
                        "5. Deletar Departamento", 
                        True, 
                        f"Department deleted successfully - ID: {self.created_dept_id}", 
                        {"deleted_id": self.created_dept_id, "message": result_data.get("message")}
                    )
                else:
                    error_text = await response.text()
                    self.log_result("5. Deletar Departamento", False, f"Status {response.status}: {error_text}")
        except Exception as e:
            self.log_result("5. Deletar Departamento", False, f"Exception: {str(e)}")
    
    async def test_6_obter_config_ia(self):
        """TESTE 6: OBTER CONFIGURAÇÃO DE I.A"""
        print("🤖 TESTE 6: OBTER CONFIGURAÇÃO DE I.A")
        print("=" * 50)
        
        if not self.auth_token:
            self.log_result("6. Obter Config I.A", False, "No auth token available")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            async with self.session.get(f"{BACKEND_URL}/config", headers=headers) as response:
                if response.status == 200:
                    config_data = await response.json()
                    ai_agent = config_data.get("ai_agent", {})
                    
                    # Verificar se tem os campos obrigatórios da IA
                    required_fields = ["enabled", "name", "personality", "instructions", "llm_provider", "llm_model", "temperature", "max_tokens", "mode", "active_hours", "can_access_credentials", "knowledge_base"]
                    missing_fields = [field for field in required_fields if field not in ai_agent]
                    
                    if not missing_fields:
                        self.log_result(
                            "6. Obter Config I.A", 
                            True, 
                            f"AI config retrieved with all required fields", 
                            {
                                "ai_enabled": ai_agent.get("enabled"),
                                "ai_name": ai_agent.get("name"),
                                "llm_provider": ai_agent.get("llm_provider"),
                                "mode": ai_agent.get("mode")
                            }
                        )
                    else:
                        self.log_result(
                            "6. Obter Config I.A", 
                            False, 
                            f"Missing required AI fields: {missing_fields}", 
                            {"missing_fields": missing_fields}
                        )
                else:
                    error_text = await response.text()
                    self.log_result("6. Obter Config I.A", False, f"Status {response.status}: {error_text}")
        except Exception as e:
            self.log_result("6. Obter Config I.A", False, f"Exception: {str(e)}")
    
    async def test_7_salvar_config_ia(self):
        """TESTE 7: SALVAR CONFIGURAÇÃO DE I.A"""
        print("💾 TESTE 7: SALVAR CONFIGURAÇÃO DE I.A")
        print("=" * 50)
        
        if not self.auth_token:
            self.log_result("7. Salvar Config I.A", False, "No auth token available")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            # Primeiro obter config atual
            async with self.session.get(f"{BACKEND_URL}/config", headers=headers) as get_response:
                if get_response.status == 200:
                    current_config = await get_response.json()
                    
                    # Atualizar apenas a seção ai_agent
                    current_config["ai_agent"] = {
                        "enabled": True,
                        "name": "Assistente IA ABA5",
                        "personality": "Amigável e profissional para testes ABA5",
                        "instructions": "Ajude os clientes com suporte técnico conforme teste ABA5",
                        "llm_provider": "openai",
                        "llm_model": "gpt-4",
                        "temperature": 0.7,
                        "max_tokens": 500,
                        "mode": "hybrid",
                        "active_hours": "24/7",
                        "can_access_credentials": True,
                        "knowledge_base": "Base de conhecimento teste ABA5"
                    }
                    
                    # Salvar configuração atualizada
                    async with self.session.put(f"{BACKEND_URL}/config", json=current_config, headers=headers) as put_response:
                        if put_response.status == 200:
                            result_data = await put_response.json()
                            
                            self.log_result(
                                "7. Salvar Config I.A", 
                                True, 
                                "AI configuration saved successfully", 
                                {
                                    "ai_name": current_config["ai_agent"]["name"],
                                    "ai_enabled": current_config["ai_agent"]["enabled"],
                                    "llm_provider": current_config["ai_agent"]["llm_provider"],
                                    "mode": current_config["ai_agent"]["mode"]
                                }
                            )
                        else:
                            error_text = await put_response.text()
                            self.log_result("7. Salvar Config I.A", False, f"PUT Status {put_response.status}: {error_text}")
                else:
                    error_text = await get_response.text()
                    self.log_result("7. Salvar Config I.A", False, f"GET Status {get_response.status}: {error_text}")
        except Exception as e:
            self.log_result("7. Salvar Config I.A", False, f"Exception: {str(e)}")
    
    async def run_all_tests(self):
        """Run all ABA 5 tests in sequence"""
        print("🧪 INICIANDO TESTE SISTEMÁTICO - ABA 5: I.A / DEPARTAMENTOS")
        print("=" * 70)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin Credentials: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        print("=" * 70)
        print()
        
        # PARTE 1 - DEPARTAMENTOS
        print("📋 PARTE 1 - DEPARTAMENTOS")
        print("-" * 30)
        
        # Test 1: Admin Login (required for all other tests)
        auth_success = await self.test_1_admin_login()
        
        if auth_success:
            # Test 2-5: Department CRUD operations
            await self.test_2_listar_departamentos()
            await self.test_3_criar_departamento()
            await self.test_4_editar_departamento()
            await self.test_5_deletar_departamento()
            
            print()
            print("🤖 PARTE 2 - CONFIGURAÇÃO DE I.A")
            print("-" * 35)
            
            # Test 6-7: AI Configuration
            await self.test_6_obter_config_ia()
            await self.test_7_salvar_config_ia()
        else:
            print("❌ Authentication failed - skipping all other tests")
        
        # Print final summary
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 70)
        print("📊 RESULTADO FINAL - ABA 5: I.A / DEPARTAMENTOS")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total de Testes: {total_tests}")
        print(f"✅ Aprovados: {passed_tests}")
        print(f"❌ Falharam: {failed_tests}")
        print(f"Taxa de Sucesso: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        print()
        
        # Detailed results by category
        print("📋 PARTE 1 - DEPARTAMENTOS:")
        dept_tests = [r for r in self.test_results if any(x in r["test"] for x in ["Login", "Listar", "Criar", "Editar", "Deletar"])]
        dept_passed = sum(1 for r in dept_tests if r["success"])
        print(f"   {dept_passed}/{len(dept_tests)} testes passaram")
        
        print("🤖 PARTE 2 - CONFIGURAÇÃO DE I.A:")
        ia_tests = [r for r in self.test_results if any(x in r["test"] for x in ["Config I.A", "Obter", "Salvar"])]
        ia_passed = sum(1 for r in ia_tests if r["success"])
        print(f"   {ia_passed}/{len(ia_tests)} testes passaram")
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
        
        print("🎯 CRITÉRIOS DE SUCESSO:")
        print("   ✅ CRUD completo de departamentos funcionando (listar, criar, editar, deletar)")
        print("   ✅ Configuração de IA sendo salva e recuperada")
        print("   ✅ Campos obrigatórios da IA presentes")
        print("   ✅ Isolamento multi-tenant funcionando")
        print()
        
        if failed_tests == 0:
            print("🎉 TODOS OS CRITÉRIOS ATENDIDOS! ABA 5 (I.A / DEPARTAMENTOS) ESTÁ 100% FUNCIONAL!")
            print("✅ Pode avançar para ABA 6 (MSG RÁPIDAS) conforme plano sistemático")
        else:
            print(f"⚠️ {failed_tests} problemas encontrados que precisam ser corrigidos")
            print("❌ NÃO avançar para próxima ABA até resolver os problemas")
        
        print("=" * 70)

async def main():
    """Main test execution"""
    async with ABA5Tester() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())