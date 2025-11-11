#!/usr/bin/env python3
"""
🧪 TESTE SISTEMÁTICO - ABA 7: DADOS PERMITIDOS
Testa funcionalidades de gerenciamento de dados permitidos: PIX, CPFs, Emails, Telefones, Chaves Aleatórias
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Configuração do teste
BACKEND_URL = "https://wppconnect-fix.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "102030@ab"

class ABA7DadosPermitidosTest:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.test_results = []
        
    async def setup(self):
        """Inicializa sessão HTTP"""
        self.session = aiohttp.ClientSession()
        print("🔧 Sessão HTTP inicializada")
        
    async def cleanup(self):
        """Limpa recursos"""
        if self.session:
            await self.session.close()
        print("🧹 Recursos limpos")
        
    def log_result(self, test_name: str, success: bool, details: str):
        """Registra resultado do teste"""
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{status} - {test_name}")
        if details:
            print(f"   {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
    async def test_1_admin_login(self):
        """Teste 1: Login do Admin"""
        try:
            url = f"{BACKEND_URL}/auth/admin/login"
            payload = {"password": ADMIN_PASSWORD}
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    self.admin_token = data.get("token")
                    
                    if self.admin_token:
                        self.log_result(
                            "1. Admin Login", 
                            True, 
                            f"Login realizado com sucesso. Token obtido: {self.admin_token[:50]}..."
                        )
                        return True
                    else:
                        self.log_result("1. Admin Login", False, "Token não retornado na resposta")
                        return False
                else:
                    error_text = await response.text()
                    self.log_result("1. Admin Login", False, f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_result("1. Admin Login", False, f"Erro na requisição: {str(e)}")
            return False
            
    async def test_2_get_config_initial(self):
        """Teste 2: GET Config - Verificar campos pix_key e allowed_data"""
        try:
            url = f"{BACKEND_URL}/config"
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    config = await response.json()
                    
                    # Verificar se campos existem
                    has_pix_key = "pix_key" in config
                    has_allowed_data = "allowed_data" in config
                    
                    if has_pix_key and has_allowed_data:
                        allowed_data = config.get("allowed_data", {})
                        fields = ["cpfs", "emails", "phones", "random_keys"]
                        has_all_fields = all(field in allowed_data for field in fields)
                        
                        if has_all_fields:
                            self.log_result(
                                "2. GET Config - Verificar Campos", 
                                True, 
                                f"Todos os campos presentes: pix_key ✓, allowed_data.cpfs ✓, allowed_data.emails ✓, allowed_data.phones ✓, allowed_data.random_keys ✓"
                            )
                            return True, config
                        else:
                            missing = [f for f in fields if f not in allowed_data]
                            self.log_result(
                                "2. GET Config - Verificar Campos", 
                                False, 
                                f"Campos faltando em allowed_data: {missing}"
                            )
                            return False, config
                    else:
                        missing = []
                        if not has_pix_key:
                            missing.append("pix_key")
                        if not has_allowed_data:
                            missing.append("allowed_data")
                        
                        self.log_result(
                            "2. GET Config - Verificar Campos", 
                            False, 
                            f"Campos faltando: {missing}"
                        )
                        return False, config
                else:
                    error_text = await response.text()
                    self.log_result("2. GET Config - Verificar Campos", False, f"Status {response.status}: {error_text}")
                    return False, None
                    
        except Exception as e:
            self.log_result("2. GET Config - Verificar Campos", False, f"Erro na requisição: {str(e)}")
            return False, None
            
    async def test_3_save_pix_key(self):
        """Teste 3: Salvar Chave PIX"""
        try:
            url = f"{BACKEND_URL}/config"
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            payload = {"pix_key": "chave_pix_teste@example.com"}
            
            async with self.session.put(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    self.log_result(
                        "3. Salvar Chave PIX", 
                        True, 
                        "Chave PIX 'chave_pix_teste@example.com' salva com sucesso"
                    )
                    return True
                else:
                    error_text = await response.text()
                    self.log_result("3. Salvar Chave PIX", False, f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_result("3. Salvar Chave PIX", False, f"Erro na requisição: {str(e)}")
            return False
            
    async def test_4_add_allowed_cpfs(self):
        """Teste 4: Adicionar CPFs Permitidos"""
        try:
            url = f"{BACKEND_URL}/config"
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            payload = {
                "allowed_data": {
                    "cpfs": ["123.456.789-00", "987.654.321-00"]
                }
            }
            
            async with self.session.put(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    self.log_result(
                        "4. Adicionar CPFs Permitidos", 
                        True, 
                        "CPFs '123.456.789-00' e '987.654.321-00' adicionados com sucesso"
                    )
                    return True
                else:
                    error_text = await response.text()
                    self.log_result("4. Adicionar CPFs Permitidos", False, f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_result("4. Adicionar CPFs Permitidos", False, f"Erro na requisição: {str(e)}")
            return False
            
    async def test_5_add_allowed_emails(self):
        """Teste 5: Adicionar Emails Permitidos"""
        try:
            url = f"{BACKEND_URL}/config"
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            payload = {
                "allowed_data": {
                    "emails": ["teste@example.com", "admin@example.com"]
                }
            }
            
            async with self.session.put(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    self.log_result(
                        "5. Adicionar Emails Permitidos", 
                        True, 
                        "Emails 'teste@example.com' e 'admin@example.com' adicionados com sucesso"
                    )
                    return True
                else:
                    error_text = await response.text()
                    self.log_result("5. Adicionar Emails Permitidos", False, f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_result("5. Adicionar Emails Permitidos", False, f"Erro na requisição: {str(e)}")
            return False
            
    async def test_6_add_allowed_phones(self):
        """Teste 6: Adicionar Telefones/WhatsApp Permitidos"""
        try:
            url = f"{BACKEND_URL}/config"
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            payload = {
                "allowed_data": {
                    "phones": ["+5511999999999", "+5521988888888"]
                }
            }
            
            async with self.session.put(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    self.log_result(
                        "6. Adicionar Telefones/WhatsApp Permitidos", 
                        True, 
                        "Telefones '+5511999999999' e '+5521988888888' adicionados com sucesso"
                    )
                    return True
                else:
                    error_text = await response.text()
                    self.log_result("6. Adicionar Telefones/WhatsApp Permitidos", False, f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_result("6. Adicionar Telefones/WhatsApp Permitidos", False, f"Erro na requisição: {str(e)}")
            return False
            
    async def test_7_add_random_keys(self):
        """Teste 7: Adicionar Chaves Aleatórias PIX"""
        try:
            url = f"{BACKEND_URL}/config"
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            payload = {
                "allowed_data": {
                    "random_keys": ["chave-random-123", "chave-random-456"]
                }
            }
            
            async with self.session.put(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    self.log_result(
                        "7. Adicionar Chaves Aleatórias PIX", 
                        True, 
                        "Chaves 'chave-random-123' e 'chave-random-456' adicionadas com sucesso"
                    )
                    return True
                else:
                    error_text = await response.text()
                    self.log_result("7. Adicionar Chaves Aleatórias PIX", False, f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_result("7. Adicionar Chaves Aleatórias PIX", False, f"Erro na requisição: {str(e)}")
            return False
            
    async def test_8_verify_persistence(self):
        """Teste 8: Verificar Persistência - Confirmar que todos os dados foram salvos"""
        try:
            url = f"{BACKEND_URL}/config"
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    config = await response.json()
                    
                    # Verificar PIX key
                    pix_key = config.get("pix_key")
                    pix_ok = pix_key == "chave_pix_teste@example.com"
                    
                    # Verificar allowed_data
                    allowed_data = config.get("allowed_data", {})
                    
                    # Verificar CPFs
                    cpfs = allowed_data.get("cpfs", [])
                    cpfs_ok = "123.456.789-00" in cpfs and "987.654.321-00" in cpfs
                    
                    # Verificar emails
                    emails = allowed_data.get("emails", [])
                    emails_ok = "teste@example.com" in emails and "admin@example.com" in emails
                    
                    # Verificar telefones
                    phones = allowed_data.get("phones", [])
                    phones_ok = "+5511999999999" in phones and "+5521988888888" in phones
                    
                    # Verificar chaves aleatórias
                    random_keys = allowed_data.get("random_keys", [])
                    random_keys_ok = "chave-random-123" in random_keys and "chave-random-456" in random_keys
                    
                    # Resultado final
                    all_ok = pix_ok and cpfs_ok and emails_ok and phones_ok and random_keys_ok
                    
                    if all_ok:
                        self.log_result(
                            "8. Verificar Persistência", 
                            True, 
                            f"Todos os dados persistidos corretamente: PIX ✓, CPFs ✓, Emails ✓, Telefones ✓, Chaves Aleatórias ✓"
                        )
                        return True, config
                    else:
                        issues = []
                        if not pix_ok:
                            issues.append(f"PIX key incorreta: esperado 'chave_pix_teste@example.com', encontrado '{pix_key}'")
                        if not cpfs_ok:
                            issues.append(f"CPFs incorretos: esperado ['123.456.789-00', '987.654.321-00'], encontrado {cpfs}")
                        if not emails_ok:
                            issues.append(f"Emails incorretos: esperado ['teste@example.com', 'admin@example.com'], encontrado {emails}")
                        if not phones_ok:
                            issues.append(f"Telefones incorretos: esperado ['+5511999999999', '+5521988888888'], encontrado {phones}")
                        if not random_keys_ok:
                            issues.append(f"Chaves aleatórias incorretas: esperado ['chave-random-123', 'chave-random-456'], encontrado {random_keys}")
                        
                        self.log_result(
                            "8. Verificar Persistência", 
                            False, 
                            f"Problemas encontrados: {'; '.join(issues)}"
                        )
                        return False, config
                else:
                    error_text = await response.text()
                    self.log_result("8. Verificar Persistência", False, f"Status {response.status}: {error_text}")
                    return False, None
                    
        except Exception as e:
            self.log_result("8. Verificar Persistência", False, f"Erro na requisição: {str(e)}")
            return False, None
            
    async def run_all_tests(self):
        """Executa todos os testes em sequência"""
        print("🧪 INICIANDO TESTE SISTEMÁTICO - ABA 7: DADOS PERMITIDOS")
        print("=" * 80)
        print(f"🎯 Backend URL: {BACKEND_URL}")
        print(f"👤 Admin: {ADMIN_EMAIL}")
        print("=" * 80)
        
        await self.setup()
        
        try:
            # Teste 1: Admin Login
            login_success = await self.test_1_admin_login()
            if not login_success:
                print("❌ TESTE ABORTADO: Falha no login do admin")
                return
                
            # Teste 2: GET Config inicial
            config_success, initial_config = await self.test_2_get_config_initial()
            if not config_success:
                print("⚠️ AVISO: Campos não encontrados, mas continuando testes...")
                
            # Teste 3: Salvar PIX Key
            await self.test_3_save_pix_key()
            
            # Teste 4: Adicionar CPFs
            await self.test_4_add_allowed_cpfs()
            
            # Teste 5: Adicionar Emails
            await self.test_5_add_allowed_emails()
            
            # Teste 6: Adicionar Telefones
            await self.test_6_add_allowed_phones()
            
            # Teste 7: Adicionar Chaves Aleatórias
            await self.test_7_add_random_keys()
            
            # Teste 8: Verificar Persistência
            persistence_success, final_config = await self.test_8_verify_persistence()
            
            # Relatório final
            self.print_final_report()
            
        finally:
            await self.cleanup()
            
    def print_final_report(self):
        """Imprime relatório final dos testes"""
        print("\n" + "=" * 80)
        print("📊 RELATÓRIO FINAL - ABA 7: DADOS PERMITIDOS")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 RESULTADO GERAL: {passed_tests}/{total_tests} TESTES PASSARAM ({success_rate:.1f}% SUCCESS RATE)")
        
        if failed_tests == 0:
            print("🎉 TODOS OS TESTES PASSARAM - ABA 7 (DADOS PERMITIDOS) 100% FUNCIONAL!")
        else:
            print(f"⚠️ {failed_tests} TESTE(S) FALHARAM - REQUER ATENÇÃO")
            
        print("\n📋 DETALHES DOS TESTES:")
        for i, result in enumerate(self.test_results, 1):
            status = "✅" if result["success"] else "❌"
            print(f"{i}. {status} {result['test']}")
            if result["details"]:
                print(f"   {result['details']}")
                
        print("\n🎯 FUNCIONALIDADES TESTADAS:")
        print("✅ Login Admin (POST /api/auth/admin/login)")
        print("✅ Verificar Config (GET /api/config)")
        print("✅ Salvar Chave PIX (PUT /api/config)")
        print("✅ Adicionar CPFs Permitidos (PUT /api/config)")
        print("✅ Adicionar Emails Permitidos (PUT /api/config)")
        print("✅ Adicionar Telefones/WhatsApp Permitidos (PUT /api/config)")
        print("✅ Adicionar Chaves Aleatórias PIX (PUT /api/config)")
        print("✅ Verificar Persistência (GET /api/config)")
        
        print("\n" + "=" * 80)

async def main():
    """Função principal"""
    test = ABA7DadosPermitidosTest()
    await test.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())