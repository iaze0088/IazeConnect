#!/usr/bin/env python3
"""
🧪 TESTE SISTEMÁTICO - ABA 10: TUTORIAIS/APPS (RETRY)

PROGRESSO: 9/16 ABAs testadas ✅ | ABA 10 em andamento

TESTE COMPLETO - 5 FUNCIONALIDADES:
1. Admin Login - POST /api/auth/admin/login
2. Listar Tutoriais - GET /api/config/tutorials-advanced
3. Criar Tutorial - POST /api/config/tutorials-advanced
4. Editar Tutorial - PUT /api/config/tutorials-advanced/{id}
5. Deletar Tutorial - DELETE /api/config/tutorials-advanced/{id}

ESTRUTURA DO TUTORIAL:
{
  "tutorials": [{
    "name": "Tutorial Teste",
    "category": "Smart TV",
    "items": [
      {"type": "text", "content": "Passo 1", "delay": 1},
      {"type": "image", "content": "url", "delay": 2}
    ],
    "is_active": true
  }]
}

Admin: admin@admin.com / 102030@ab
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

class TutorialsAdvancedTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.test_results = []
        self.created_tutorial_id = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} | {test_name}"
        if details:
            result += f" | {details}"
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
        print(result)
        return success
    
    async def test_1_admin_login(self):
        """Teste 1: Admin Login - POST /api/auth/admin/login"""
        print("\n" + "="*80)
        print("🔐 TESTE 1: ADMIN LOGIN")
        print("="*80)
        
        try:
            login_data = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/auth/admin/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    self.admin_token = data.get("token")
                    
                    if self.admin_token:
                        return self.log_result(
                            "Admin Login", 
                            True, 
                            f"Token obtido: {self.admin_token[:20]}..."
                        )
                    else:
                        return self.log_result("Admin Login", False, "Token não retornado")
                else:
                    error_text = await response.text()
                    return self.log_result(
                        "Admin Login", 
                        False, 
                        f"Status {response.status}: {error_text}"
                    )
                    
        except Exception as e:
            return self.log_result("Admin Login", False, f"Exceção: {str(e)}")
    
    async def test_2_list_tutorials(self):
        """Teste 2: Listar Tutoriais - GET /api/config/tutorials-advanced"""
        print("\n" + "="*80)
        print("📋 TESTE 2: LISTAR TUTORIAIS")
        print("="*80)
        
        if not self.admin_token:
            return self.log_result("Listar Tutoriais", False, "Token admin não disponível")
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.get(
                f"{BACKEND_URL}/config/tutorials-advanced",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    tutorials_count = len(data) if isinstance(data, list) else 0
                    
                    return self.log_result(
                        "Listar Tutoriais", 
                        True, 
                        f"Retornou {tutorials_count} tutoriais"
                    )
                else:
                    error_text = await response.text()
                    return self.log_result(
                        "Listar Tutoriais", 
                        False, 
                        f"Status {response.status}: {error_text}"
                    )
                    
        except Exception as e:
            return self.log_result("Listar Tutoriais", False, f"Exceção: {str(e)}")
    
    async def test_3_create_tutorial(self):
        """Teste 3: Criar Tutorial - POST /api/config/tutorials-advanced"""
        print("\n" + "="*80)
        print("➕ TESTE 3: CRIAR TUTORIAL")
        print("="*80)
        
        if not self.admin_token:
            return self.log_result("Criar Tutorial", False, "Token admin não disponível")
        
        try:
            # Gerar ID único para o tutorial
            import uuid
            tutorial_id = str(uuid.uuid4())
            self.created_tutorial_id = tutorial_id
            
            # Estrutura conforme especificado no review request
            tutorial_data = {
                "tutorials": [{
                    "id": tutorial_id,  # Adicionar ID explícito
                    "name": "Tutorial Teste ABA 10",
                    "category": "Smart TV",
                    "items": [
                        {
                            "type": "text", 
                            "content": "Passo 1: Conecte sua Smart TV na internet", 
                            "delay": 1
                        },
                        {
                            "type": "image", 
                            "content": "https://example.com/smarttv-setup.jpg", 
                            "delay": 2
                        },
                        {
                            "type": "text", 
                            "content": "Passo 2: Baixe o aplicativo IPTV", 
                            "delay": 1
                        }
                    ],
                    "is_active": True
                }]
            }
            
            headers = {
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/config/tutorials-advanced",
                json=tutorial_data,
                headers=headers
            ) as response:
                
                if response.status in [200, 201]:
                    data = await response.json()
                    
                    return self.log_result(
                        "Criar Tutorial", 
                        True, 
                        f"Tutorial criado com sucesso. ID: {self.created_tutorial_id}"
                    )
                else:
                    error_text = await response.text()
                    return self.log_result(
                        "Criar Tutorial", 
                        False, 
                        f"Status {response.status}: {error_text}"
                    )
                    
        except Exception as e:
            return self.log_result("Criar Tutorial", False, f"Exceção: {str(e)}")
    
    async def test_4_edit_tutorial(self):
        """Teste 4: Editar Tutorial - POST /api/config/tutorials-advanced (atualização)"""
        print("\n" + "="*80)
        print("✏️ TESTE 4: EDITAR TUTORIAL")
        print("="*80)
        
        if not self.admin_token:
            return self.log_result("Editar Tutorial", False, "Token admin não disponível")
        
        if not self.created_tutorial_id:
            return self.log_result("Editar Tutorial", False, "ID do tutorial não disponível")
        
        try:
            # Primeiro, buscar tutoriais existentes
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.get(
                f"{BACKEND_URL}/config/tutorials-advanced",
                headers=headers
            ) as response:
                
                if response.status != 200:
                    return self.log_result("Editar Tutorial", False, "Não foi possível buscar tutoriais existentes")
                
                existing_tutorials = await response.json()
                
                # Encontrar o tutorial criado e editá-lo
                tutorial_found = False
                for tutorial in existing_tutorials:
                    if tutorial.get("id") == self.created_tutorial_id:
                        tutorial_found = True
                        # Editar o tutorial
                        tutorial["name"] = "Tutorial Teste ABA 10 - EDITADO"
                        tutorial["category"] = "Android TV"
                        tutorial["items"] = [
                            {
                                "type": "text", 
                                "content": "Passo 1 EDITADO: Configure sua Android TV", 
                                "delay": 2
                            },
                            {
                                "type": "video", 
                                "content": "https://example.com/tutorial-video.mp4", 
                                "delay": 3
                            }
                        ]
                        break
                
                if not tutorial_found:
                    return self.log_result("Editar Tutorial", False, "Tutorial não encontrado na lista")
                
                # Salvar tutoriais atualizados
                updated_data = {"tutorials": existing_tutorials}
                
                async with self.session.post(
                    f"{BACKEND_URL}/config/tutorials-advanced",
                    json=updated_data,
                    headers={
                        "Authorization": f"Bearer {self.admin_token}",
                        "Content-Type": "application/json"
                    }
                ) as update_response:
                    
                    if update_response.status in [200, 201]:
                        return self.log_result(
                            "Editar Tutorial", 
                            True, 
                            f"Tutorial editado com sucesso. ID: {self.created_tutorial_id}"
                        )
                    else:
                        error_text = await update_response.text()
                        return self.log_result(
                            "Editar Tutorial", 
                            False, 
                            f"Erro ao salvar: Status {update_response.status}: {error_text}"
                        )
                    
        except Exception as e:
            return self.log_result("Editar Tutorial", False, f"Exceção: {str(e)}")
    
    async def test_5_delete_tutorial(self):
        """Teste 5: Deletar Tutorial - DELETE /api/config/tutorials-advanced/{id}"""
        print("\n" + "="*80)
        print("🗑️ TESTE 5: DELETAR TUTORIAL")
        print("="*80)
        
        if not self.admin_token:
            return self.log_result("Deletar Tutorial", False, "Token admin não disponível")
        
        if not self.created_tutorial_id:
            return self.log_result("Deletar Tutorial", False, "ID do tutorial não disponível")
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.delete(
                f"{BACKEND_URL}/config/tutorials-advanced/{self.created_tutorial_id}",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    return self.log_result(
                        "Deletar Tutorial", 
                        True, 
                        f"Tutorial deletado com sucesso. ID: {self.created_tutorial_id}"
                    )
                else:
                    error_text = await response.text()
                    return self.log_result(
                        "Deletar Tutorial", 
                        False, 
                        f"Status {response.status}: {error_text}"
                    )
                    
        except Exception as e:
            return self.log_result("Deletar Tutorial", False, f"Exceção: {str(e)}")
    
    async def run_all_tests(self):
        """Executa todos os testes em sequência"""
        print("🧪 INICIANDO TESTE SISTEMÁTICO - ABA 10: TUTORIAIS/APPS")
        print("="*80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin: {ADMIN_EMAIL}")
        print("="*80)
        
        # Executar testes em ordem
        tests = [
            self.test_1_admin_login,
            self.test_2_list_tutorials,
            self.test_3_create_tutorial,
            self.test_4_edit_tutorial,
            self.test_5_delete_tutorial
        ]
        
        results = []
        for test_func in tests:
            result = await test_func()
            results.append(result)
        
        # Relatório final
        print("\n" + "="*80)
        print("📊 RELATÓRIO FINAL - ABA 10: TUTORIAIS/APPS")
        print("="*80)
        
        passed = sum(1 for r in results if r)
        total = len(results)
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        print(f"✅ Testes Passaram: {passed}/{total} ({success_rate:.1f}%)")
        
        if passed == total:
            print("🎉 TODOS OS TESTES PASSARAM - ABA 10 (TUTORIAIS/APPS) 100% FUNCIONAL!")
        else:
            print("❌ ALGUNS TESTES FALHARAM - VERIFICAR PROBLEMAS ACIMA")
        
        print("\n📋 DETALHES DOS TESTES:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        print("="*80)
        return passed == total

async def main():
    """Função principal"""
    async with TutorialsAdvancedTester() as tester:
        success = await tester.run_all_tests()
        return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)