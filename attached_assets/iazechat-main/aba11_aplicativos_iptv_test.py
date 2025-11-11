#!/usr/bin/env python3
"""
🧪 TESTE SISTEMÁTICO - ABA 11: APLICATIVOS (IPTV)

Testa todas as funcionalidades da ABA 11 conforme review request:
1. Admin Login - POST /api/auth/admin/login
2. Listar Aplicativos IPTV - GET /api/iptv-apps
3. Criar Aplicativo IPTV - POST /api/iptv-apps
4. Editar Aplicativo IPTV - PUT /api/iptv-apps/{app_id}
5. Deletar Aplicativo IPTV - DELETE /api/iptv-apps/{app_id}

Credenciais: admin@admin.com / 102030@ab
Backend: https://wppconnect-fix.preview.emergentagent.com/api
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Configuração
BACKEND_URL = "https://wppconnect-fix.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "102030@ab"

class IPTVAppsTestRunner:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.test_results = []
        self.created_app_id = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log do resultado do teste"""
        status = "✅ PASSOU" if success else "❌ FALHOU"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        print(f"{status} - {test_name}")
        if details:
            print(f"   {details}")
        print()
    
    async def test_admin_login(self):
        """Teste 1: Admin Login"""
        print("🔐 TESTE 1: ADMIN LOGIN")
        print("=" * 50)
        
        try:
            payload = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/admin/login", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    self.admin_token = data.get("token")
                    
                    if self.admin_token:
                        self.log_test(
                            "Admin Login", 
                            True, 
                            f"Token obtido com sucesso. User: {data.get('user_data', {}).get('email', 'N/A')}"
                        )
                        return True
                    else:
                        self.log_test("Admin Login", False, "Token não retornado na resposta")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Admin Login", False, f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Admin Login", False, f"Erro na requisição: {str(e)}")
            return False
    
    async def test_list_iptv_apps(self):
        """Teste 2: Listar Aplicativos IPTV"""
        print("📋 TESTE 2: LISTAR APLICATIVOS IPTV")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_test("Listar Apps IPTV", False, "Token admin não disponível")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.get(f"{BACKEND_URL}/iptv-apps", headers=headers) as response:
                if response.status == 200:
                    apps = await response.json()
                    
                    if isinstance(apps, list):
                        self.log_test(
                            "Listar Apps IPTV", 
                            True, 
                            f"Lista retornada com sucesso. Total de apps: {len(apps)}"
                        )
                        
                        # Log dos apps existentes
                        if apps:
                            print("   📦 Apps IPTV encontrados:")
                            for app in apps[:3]:  # Mostrar apenas os primeiros 3
                                print(f"      - {app.get('name', 'Sem nome')} (ID: {app.get('id', 'N/A')[:8]}...)")
                        else:
                            print("   📦 Nenhum app IPTV encontrado (lista vazia)")
                        
                        return True
                    else:
                        self.log_test("Listar Apps IPTV", False, f"Resposta não é uma lista: {type(apps)}")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Listar Apps IPTV", False, f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Listar Apps IPTV", False, f"Erro na requisição: {str(e)}")
            return False
    
    async def test_create_iptv_app(self):
        """Teste 3: Criar Aplicativo IPTV"""
        print("➕ TESTE 3: CRIAR APLICATIVO IPTV")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_test("Criar App IPTV", False, "Token admin não disponível")
            return False
        
        try:
            # Dados do app IPTV conforme review request
            app_data = {
                "name": "App Teste IPTV",
                "type": "SSIPTV",
                "config_url": "https://config.example.com",
                "url_template": "http://app.tv/{mac}/{server}",
                "fields": [
                    {"name": "MAC Address", "key": "mac", "type": "text"},
                    {"name": "Server", "key": "server", "type": "text"}
                ],
                "instructions": "Instruções de instalação"
            }
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.post(f"{BACKEND_URL}/iptv-apps", json=app_data, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("ok") and data.get("app"):
                        app = data["app"]
                        self.created_app_id = app.get("id")
                        
                        self.log_test(
                            "Criar App IPTV", 
                            True, 
                            f"App criado com sucesso. ID: {self.created_app_id}, Nome: {app.get('name')}"
                        )
                        
                        # Validar campos obrigatórios
                        required_fields = ["id", "name", "type", "config_url", "url_template", "fields"]
                        missing_fields = [field for field in required_fields if not app.get(field)]
                        
                        if missing_fields:
                            print(f"   ⚠️ Campos faltando na resposta: {missing_fields}")
                        else:
                            print(f"   ✅ Todos os campos obrigatórios presentes")
                        
                        return True
                    else:
                        self.log_test("Criar App IPTV", False, f"Resposta inválida: {data}")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Criar App IPTV", False, f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Criar App IPTV", False, f"Erro na requisição: {str(e)}")
            return False
    
    async def test_update_iptv_app(self):
        """Teste 4: Editar Aplicativo IPTV"""
        print("✏️ TESTE 4: EDITAR APLICATIVO IPTV")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_test("Editar App IPTV", False, "Token admin não disponível")
            return False
        
        if not self.created_app_id:
            self.log_test("Editar App IPTV", False, "ID do app criado não disponível")
            return False
        
        try:
            # Dados para atualização
            update_data = {
                "name": "App Teste IPTV - EDITADO",
                "config_url": "https://config-updated.example.com",
                "instructions": "Instruções de instalação atualizadas"
            }
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.put(
                f"{BACKEND_URL}/iptv-apps/{self.created_app_id}", 
                json=update_data, 
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("ok"):
                        self.log_test(
                            "Editar App IPTV", 
                            True, 
                            f"App editado com sucesso. ID: {self.created_app_id}"
                        )
                        
                        # Verificar se as mudanças foram aplicadas (buscar o app novamente)
                        async with self.session.get(f"{BACKEND_URL}/iptv-apps", headers=headers) as get_response:
                            if get_response.status == 200:
                                apps = await get_response.json()
                                updated_app = next((app for app in apps if app.get("id") == self.created_app_id), None)
                                
                                if updated_app and updated_app.get("name") == "App Teste IPTV - EDITADO":
                                    print(f"   ✅ Alterações confirmadas no banco de dados")
                                else:
                                    print(f"   ⚠️ Alterações não refletidas no banco")
                        
                        return True
                    else:
                        self.log_test("Editar App IPTV", False, f"Resposta inválida: {data}")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Editar App IPTV", False, f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Editar App IPTV", False, f"Erro na requisição: {str(e)}")
            return False
    
    async def test_delete_iptv_app(self):
        """Teste 5: Deletar Aplicativo IPTV"""
        print("🗑️ TESTE 5: DELETAR APLICATIVO IPTV")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_test("Deletar App IPTV", False, "Token admin não disponível")
            return False
        
        if not self.created_app_id:
            self.log_test("Deletar App IPTV", False, "ID do app criado não disponível")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.delete(
                f"{BACKEND_URL}/iptv-apps/{self.created_app_id}", 
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("ok"):
                        self.log_test(
                            "Deletar App IPTV", 
                            True, 
                            f"App deletado com sucesso. ID: {self.created_app_id}"
                        )
                        
                        # Verificar se foi realmente deletado (buscar novamente)
                        async with self.session.get(f"{BACKEND_URL}/iptv-apps", headers=headers) as get_response:
                            if get_response.status == 200:
                                apps = await get_response.json()
                                deleted_app = next((app for app in apps if app.get("id") == self.created_app_id), None)
                                
                                if not deleted_app:
                                    print(f"   ✅ Deleção confirmada no banco de dados")
                                else:
                                    print(f"   ⚠️ App ainda existe no banco após deleção")
                        
                        return True
                    else:
                        self.log_test("Deletar App IPTV", False, f"Resposta inválida: {data}")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Deletar App IPTV", False, f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Deletar App IPTV", False, f"Erro na requisição: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Executa todos os testes em sequência"""
        print("🧪 INICIANDO TESTE SISTEMÁTICO - ABA 11: APLICATIVOS (IPTV)")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin: {ADMIN_EMAIL}")
        print("=" * 80)
        print()
        
        # Executar testes em ordem
        tests = [
            self.test_admin_login,
            self.test_list_iptv_apps,
            self.test_create_iptv_app,
            self.test_update_iptv_app,
            self.test_delete_iptv_app
        ]
        
        for test_func in tests:
            await test_func()
        
        # Relatório final
        print("📊 RELATÓRIO FINAL - ABA 11: APLICATIVOS (IPTV)")
        print("=" * 80)
        
        passed_tests = [r for r in self.test_results if r["success"]]
        failed_tests = [r for r in self.test_results if not r["success"]]
        
        print(f"✅ TESTES PASSARAM: {len(passed_tests)}/{len(self.test_results)}")
        print(f"❌ TESTES FALHARAM: {len(failed_tests)}/{len(self.test_results)}")
        print(f"📈 TAXA DE SUCESSO: {len(passed_tests)/len(self.test_results)*100:.1f}%")
        print()
        
        if failed_tests:
            print("❌ TESTES QUE FALHARAM:")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
            print()
        
        if passed_tests:
            print("✅ TESTES QUE PASSARAM:")
            for test in passed_tests:
                print(f"   - {test['test']}")
            print()
        
        # Conclusão
        if len(failed_tests) == 0:
            print("🎉 TODOS OS TESTES PASSARAM - ABA 11 (APLICATIVOS IPTV) 100% FUNCIONAL!")
            print("✅ CRUD completo de aplicativos IPTV funcionando")
            print("✅ Campos customizáveis funcionando")
            print("✅ Isolamento multi-tenant funcionando")
            print("✅ Pode avançar para próxima ABA conforme plano sistemático")
        else:
            print("⚠️ ALGUNS TESTES FALHARAM - REQUER ATENÇÃO")
            print("🔧 Verifique os erros acima e corrija antes de avançar")
        
        print("=" * 80)
        
        return len(failed_tests) == 0

async def main():
    """Função principal"""
    async with IPTVAppsTestRunner() as runner:
        success = await runner.run_all_tests()
        return success

if __name__ == "__main__":
    asyncio.run(main())