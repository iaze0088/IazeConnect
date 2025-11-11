#!/usr/bin/env python3
"""
🧪 TESTE FINAL - VALIDAR TODAS AS FUNCIONALIDADES APÓS CORREÇÃO
Executar os 8 testes críticos conforme review request
Backend URL: https://suporte.help/api
Admin: admin@admin.com / 102030@ab
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Configuração
BACKEND_URL = "https://suporte.help/api"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "102030@ab"

class FinalValidationTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_result(self, test_name: str, success: bool, details: str, response_data=None):
        """Log test result"""
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"\n{status} - {test_name}")
        print(f"   {details}")
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
        
        self.results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
    
    async def test_1_admin_login(self):
        """TESTE 1 - LOGIN ADMIN"""
        print("\n" + "="*60)
        print("🔑 TESTE 1: ADMIN LOGIN")
        print("="*60)
        
        try:
            url = f"{BACKEND_URL}/auth/admin/login"
            payload = {"password": ADMIN_PASSWORD}
            
            print(f"POST {url}")
            print(f"Body: {json.dumps(payload)}")
            
            async with self.session.post(url, json=payload) as response:
                data = await response.json()
                
                if response.status == 200 and data.get("token"):
                    self.admin_token = data["token"]
                    self.log_result(
                        "TESTE 1 - LOGIN ADMIN", 
                        True, 
                        f"Status: {response.status}, Token obtido com sucesso"
                    )
                    print(f"   Token: {self.admin_token[:50]}...")
                    return True
                else:
                    self.log_result(
                        "TESTE 1 - LOGIN ADMIN", 
                        False, 
                        f"Status: {response.status}, Falha no login", 
                        data
                    )
                    return False
                    
        except Exception as e:
            self.log_result(
                "TESTE 1 - LOGIN ADMIN", 
                False, 
                f"Erro de conexão: {str(e)}"
            )
            return False
    
    async def test_2_criar_revenda(self):
        """TESTE 2 - CRIAR REVENDA"""
        print("\n" + "="*60)
        print("🏢 TESTE 2: CRIAR REVENDA")
        print("="*60)
        
        if not self.admin_token:
            self.log_result("TESTE 2 - CRIAR REVENDA", False, "Token admin não disponível")
            return False
        
        try:
            url = f"{BACKEND_URL}/resellers"
            payload = {
                "name": "Teste Final",
                "email": "teste@test.com", 
                "password": "123"
            }
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            print(f"POST {url}")
            print(f"Headers: Authorization: Bearer {self.admin_token[:20]}...")
            print(f"Body: {json.dumps(payload)}")
            
            async with self.session.post(url, json=payload, headers=headers) as response:
                data = await response.json()
                
                if response.status in [200, 201]:
                    self.log_result(
                        "TESTE 2 - CRIAR REVENDA", 
                        True, 
                        f"Status: {response.status}, Revenda criada com sucesso"
                    )
                    print(f"   Revenda ID: {data.get('id', 'N/A')}")
                    return True
                else:
                    self.log_result(
                        "TESTE 2 - CRIAR REVENDA", 
                        False, 
                        f"Status: {response.status}, Falha na criação", 
                        data
                    )
                    return False
                    
        except Exception as e:
            self.log_result(
                "TESTE 2 - CRIAR REVENDA", 
                False, 
                f"Erro de conexão: {str(e)}"
            )
            return False
    
    async def test_3_salvar_departamento(self):
        """TESTE 3 - SALVAR DEPARTAMENTO"""
        print("\n" + "="*60)
        print("🏛️ TESTE 3: SALVAR DEPARTAMENTO")
        print("="*60)
        
        if not self.admin_token:
            self.log_result("TESTE 3 - SALVAR DEPARTAMENTO", False, "Token admin não disponível")
            return False
        
        try:
            url = f"{BACKEND_URL}/ai/departments"
            payload = {
                "name": "Dept Teste",
                "description": "Teste"
            }
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            print(f"POST {url}")
            print(f"Headers: Authorization: Bearer {self.admin_token[:20]}...")
            print(f"Body: {json.dumps(payload)}")
            
            async with self.session.post(url, json=payload, headers=headers) as response:
                data = await response.json()
                
                if response.status in [200, 201]:
                    self.log_result(
                        "TESTE 3 - SALVAR DEPARTAMENTO", 
                        True, 
                        f"Status: {response.status}, Departamento criado com sucesso"
                    )
                    print(f"   Departamento ID: {data.get('id', 'N/A')}")
                    return True
                else:
                    self.log_result(
                        "TESTE 3 - SALVAR DEPARTAMENTO", 
                        False, 
                        f"Status: {response.status}, Falha na criação", 
                        data
                    )
                    return False
                    
        except Exception as e:
            self.log_result(
                "TESTE 3 - SALVAR DEPARTAMENTO", 
                False, 
                f"Erro de conexão: {str(e)}"
            )
            return False
    
    async def test_4_salvar_msg_rapida(self):
        """TESTE 4 - SALVAR MSG RÁPIDA"""
        print("\n" + "="*60)
        print("💬 TESTE 4: SALVAR MSG RÁPIDA")
        print("="*60)
        
        if not self.admin_token:
            self.log_result("TESTE 4 - SALVAR MSG RÁPIDA", False, "Token admin não disponível")
            return False
        
        try:
            # Primeiro, pegar config atual
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            print(f"GET {BACKEND_URL}/config")
            async with self.session.get(f"{BACKEND_URL}/config", headers=headers) as response:
                if response.status != 200:
                    self.log_result(
                        "TESTE 4 - SALVAR MSG RÁPIDA", 
                        False, 
                        f"Falha ao obter config atual: {response.status}"
                    )
                    return False
                
                config = await response.json()
                print(f"   Config atual obtida")
            
            # Adicionar nova mensagem rápida
            quick_blocks = config.get("quick_blocks", [])
            quick_blocks.append({
                "id": f"test_{datetime.now().strftime('%H%M%S')}",
                "title": "Teste Final",
                "message": "Esta é uma mensagem de teste final"
            })
            
            config["quick_blocks"] = quick_blocks
            
            print(f"PUT {BACKEND_URL}/config")
            print(f"   Adicionando nova mensagem rápida")
            
            async with self.session.put(f"{BACKEND_URL}/config", json=config, headers=headers) as response:
                data = await response.json()
                
                if response.status == 200:
                    self.log_result(
                        "TESTE 4 - SALVAR MSG RÁPIDA", 
                        True, 
                        f"Status: {response.status}, Mensagem rápida salva com sucesso"
                    )
                    return True
                else:
                    self.log_result(
                        "TESTE 4 - SALVAR MSG RÁPIDA", 
                        False, 
                        f"Status: {response.status}, Falha ao salvar", 
                        data
                    )
                    return False
                    
        except Exception as e:
            self.log_result(
                "TESTE 4 - SALVAR MSG RÁPIDA", 
                False, 
                f"Erro de conexão: {str(e)}"
            )
            return False
    
    async def test_5_salvar_dados_permitidos(self):
        """TESTE 5 - SALVAR DADOS PERMITIDOS"""
        print("\n" + "="*60)
        print("🔒 TESTE 5: SALVAR DADOS PERMITIDOS")
        print("="*60)
        
        if not self.admin_token:
            self.log_result("TESTE 5 - SALVAR DADOS PERMITIDOS", False, "Token admin não disponível")
            return False
        
        try:
            url = f"{BACKEND_URL}/config"
            payload = {
                "allowed_data": {
                    "cpfs": ["999.999.999-99"]
                }
            }
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            print(f"PUT {url}")
            print(f"Headers: Authorization: Bearer {self.admin_token[:20]}...")
            print(f"Body: {json.dumps(payload)}")
            
            async with self.session.put(url, json=payload, headers=headers) as response:
                data = await response.json()
                
                if response.status == 200:
                    self.log_result(
                        "TESTE 5 - SALVAR DADOS PERMITIDOS", 
                        True, 
                        f"Status: {response.status}, Dados permitidos salvos com sucesso"
                    )
                    return True
                else:
                    self.log_result(
                        "TESTE 5 - SALVAR DADOS PERMITIDOS", 
                        False, 
                        f"Status: {response.status}, Falha ao salvar", 
                        data
                    )
                    return False
                    
        except Exception as e:
            self.log_result(
                "TESTE 5 - SALVAR DADOS PERMITIDOS", 
                False, 
                f"Erro de conexão: {str(e)}"
            )
            return False
    
    async def test_6_criar_aviso(self):
        """TESTE 6 - CRIAR AVISO"""
        print("\n" + "="*60)
        print("📢 TESTE 6: CRIAR AVISO")
        print("="*60)
        
        if not self.admin_token:
            self.log_result("TESTE 6 - CRIAR AVISO", False, "Token admin não disponível")
            return False
        
        try:
            url = f"{BACKEND_URL}/notices"
            payload = {
                "title": "Teste",
                "message": "Mensagem teste",
                "type": "info"
            }
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            print(f"POST {url}")
            print(f"Headers: Authorization: Bearer {self.admin_token[:20]}...")
            print(f"Body: {json.dumps(payload)}")
            
            async with self.session.post(url, json=payload, headers=headers) as response:
                data = await response.json()
                
                if response.status in [200, 201]:
                    self.log_result(
                        "TESTE 6 - CRIAR AVISO", 
                        True, 
                        f"Status: {response.status}, Aviso criado com sucesso"
                    )
                    print(f"   Aviso ID: {data.get('id', 'N/A')}")
                    return True
                else:
                    self.log_result(
                        "TESTE 6 - CRIAR AVISO", 
                        False, 
                        f"Status: {response.status}, Falha na criação", 
                        data
                    )
                    return False
                    
        except Exception as e:
            self.log_result(
                "TESTE 6 - CRIAR AVISO", 
                False, 
                f"Erro de conexão: {str(e)}"
            )
            return False
    
    async def test_7_criar_backup(self):
        """TESTE 7 - CRIAR BACKUP"""
        print("\n" + "="*60)
        print("💾 TESTE 7: CRIAR BACKUP")
        print("="*60)
        
        if not self.admin_token:
            self.log_result("TESTE 7 - CRIAR BACKUP", False, "Token admin não disponível")
            return False
        
        try:
            url = f"{BACKEND_URL}/admin/backup/create"
            payload = {
                "backup_type": "database"
            }
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            print(f"POST {url}")
            print(f"Headers: Authorization: Bearer {self.admin_token[:20]}...")
            print(f"Body: {json.dumps(payload)}")
            
            async with self.session.post(url, json=payload, headers=headers) as response:
                data = await response.json()
                
                if response.status in [200, 201]:
                    self.log_result(
                        "TESTE 7 - CRIAR BACKUP", 
                        True, 
                        f"Status: {response.status}, Backup criado com sucesso"
                    )
                    return True
                else:
                    self.log_result(
                        "TESTE 7 - CRIAR BACKUP", 
                        False, 
                        f"Status: {response.status}, Falha na criação", 
                        data
                    )
                    return False
                    
        except Exception as e:
            self.log_result(
                "TESTE 7 - CRIAR BACKUP", 
                False, 
                f"Erro de conexão: {str(e)}"
            )
            return False
    
    async def test_8_wa_site_config(self):
        """TESTE 8 - WA SITE CONFIG"""
        print("\n" + "="*60)
        print("🤖 TESTE 8: WA SITE CONFIG")
        print("="*60)
        
        if not self.admin_token:
            self.log_result("TESTE 8 - WA SITE CONFIG", False, "Token admin não disponível")
            return False
        
        try:
            url = f"{BACKEND_URL}/admin/vendas-bot/simple-config"
            payload = {
                "ai_instructions": "Teste instruções"
            }
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            print(f"POST {url}")
            print(f"Headers: Authorization: Bearer {self.admin_token[:20]}...")
            print(f"Body: {json.dumps(payload)}")
            
            async with self.session.post(url, json=payload, headers=headers) as response:
                data = await response.json()
                
                if response.status in [200, 201]:
                    self.log_result(
                        "TESTE 8 - WA SITE CONFIG", 
                        True, 
                        f"Status: {response.status}, Config salva com sucesso"
                    )
                    return True
                else:
                    self.log_result(
                        "TESTE 8 - WA SITE CONFIG", 
                        False, 
                        f"Status: {response.status}, Falha ao salvar", 
                        data
                    )
                    return False
                    
        except Exception as e:
            self.log_result(
                "TESTE 8 - WA SITE CONFIG", 
                False, 
                f"Erro de conexão: {str(e)}"
            )
            return False
    
    async def run_all_tests(self):
        """Executa todos os 8 testes críticos"""
        print("🧪 INICIANDO TESTE FINAL - VALIDAR TODAS AS FUNCIONALIDADES")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        print("="*80)
        
        # Executar todos os testes em sequência
        test_results = []
        
        test_results.append(await self.test_1_admin_login())
        test_results.append(await self.test_2_criar_revenda())
        test_results.append(await self.test_3_salvar_departamento())
        test_results.append(await self.test_4_salvar_msg_rapida())
        test_results.append(await self.test_5_salvar_dados_permitidos())
        test_results.append(await self.test_6_criar_aviso())
        test_results.append(await self.test_7_criar_backup())
        test_results.append(await self.test_8_wa_site_config())
        
        # Resumo final
        print("\n" + "="*80)
        print("📊 RESUMO FINAL DOS TESTES")
        print("="*80)
        
        passed = sum(test_results)
        total = len(test_results)
        success_rate = (passed / total) * 100
        
        print(f"✅ TESTES PASSARAM: {passed}/{total} ({success_rate:.1f}%)")
        print(f"❌ TESTES FALHARAM: {total - passed}/{total}")
        
        if passed == total:
            print("\n🎉 TODOS OS TESTES PASSARAM! SISTEMA 100% FUNCIONAL!")
        else:
            print(f"\n⚠️ {total - passed} TESTE(S) FALHARAM - VERIFICAR DETALHES ACIMA")
        
        print("\n📋 DETALHES POR TESTE:")
        for result in self.results:
            status = "✅" if result["success"] else "❌"
            print(f"   {status} {result['test']}")
        
        return passed == total

async def main():
    """Função principal"""
    async with FinalValidationTester() as tester:
        success = await tester.run_all_tests()
        return success

if __name__ == "__main__":
    asyncio.run(main())