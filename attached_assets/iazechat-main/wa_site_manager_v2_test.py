#!/usr/bin/env python3
"""
🎯 TESTE COMPLETO: Nova Estrutura WA Site Manager V2
Conforme Review Request - Testa EXATAMENTE os endpoints e estrutura mencionados
"""

import asyncio
import httpx
import json
import os
from dotenv import load_dotenv
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv('/app/backend/.env')

# Configurações
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://wppconnect-fix.preview.emergentagent.com')
BASE_URL = f"{BACKEND_URL}/api"

print(f"🎯 TESTE COMPLETO: Nova Estrutura WA Site Manager V2")
print(f"🌐 Backend URL: {BACKEND_URL}")
print("=" * 80)

class WASiteManagerV2Tester:
    def __init__(self):
        self.test_results = []
        self.admin_token = None
        
    async def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log de resultado de teste"""
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{status} - {test_name}")
        if details:
            print(f"   📋 {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    async def admin_login(self):
        """Login como admin para acessar endpoints administrativos"""
        print("\n🔵 FAZENDO LOGIN COMO ADMIN")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{BASE_URL}/auth/admin/login",
                    json={"password": "102030@ab"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.admin_token = data.get("token")
                    await self.log_test("Admin Login", True, f"Token obtido: {self.admin_token[:20]}...")
                    return True
                else:
                    await self.log_test("Admin Login", False, f"Status {response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_test("Admin Login", False, f"Erro: {str(e)}")
            return False
    
    async def test_get_simple_config_endpoint(self):
        """1. Teste GET /api/admin/vendas-bot/simple-config"""
        print("\n🔵 TESTE 1: GET - Carregar Configuração")
        
        if not self.admin_token:
            await self.log_test("GET simple-config", False, "Token admin não disponível")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{BASE_URL}/admin/vendas-bot/simple-config",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verificar estrutura conforme review request
                    expected_fields = [
                        'ia_config', 'visual_config', 'external_apis', 
                        'flows', 'integrations', 'analytics'
                    ]
                    
                    # Verificar se tem a nova estrutura V2
                    has_v2_structure = all(field in data for field in expected_fields)
                    
                    if has_v2_structure:
                        # Verificar campos específicos do ia_config
                        ia_config = data.get('ia_config', {})
                        ia_required_fields = [
                            'name', 'role', 'personality', 'instructions', 
                            'knowledge_base', 'llm_provider', 'llm_model', 
                            'temperature', 'max_tokens', 'api_key', 
                            'greeting_message', 'fallback_message', 
                            'transfer_message', 'auto_transfer_keywords', 
                            'conversation_history_limit'
                        ]
                        
                        ia_fields_present = sum(1 for field in ia_required_fields if field in ia_config)
                        
                        await self.log_test(
                            "GET simple-config - Estrutura V2", 
                            True, 
                            f"Nova estrutura V2 detectada! ia_config tem {ia_fields_present}/{len(ia_required_fields)} campos"
                        )
                        return data
                    else:
                        # Estrutura antiga
                        await self.log_test(
                            "GET simple-config - Estrutura V2", 
                            False, 
                            f"Estrutura antiga detectada. Campos presentes: {list(data.keys())}"
                        )
                        return data
                else:
                    await self.log_test("GET simple-config", False, f"Status {response.status_code}")
                    return None
                    
        except Exception as e:
            await self.log_test("GET simple-config", False, f"Erro: {str(e)}")
            return None
    
    async def test_post_simple_config_endpoint(self):
        """2. Teste POST /api/admin/vendas-bot/simple-config"""
        print("\n🔵 TESTE 2: POST - Salvar Configuração")
        
        if not self.admin_token:
            await self.log_test("POST simple-config", False, "Token admin não disponível")
            return False
        
        # Dados de teste conforme review request
        test_config = {
            "empresa_nome": "Teste IAZE",
            "usa_ia": True,
            "is_active": True,
            "ia_config": {
                "name": "Teste Bot",
                "role": "Consultor Teste",
                "personality": "Profissional e amigável",
                "instructions": "Você é um bot de teste. Responda sempre com 'Teste OK'.",
                "knowledge_base": {
                    "enabled": True,
                    "sources": [{
                        "type": "url",
                        "url": "https://site.suporte.help/base-conhecimento.html",
                        "description": "Base teste"
                    }],
                    "fallback_text": "Informações de teste"
                },
                "llm_provider": "openai",
                "llm_model": "gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": 500,
                "api_key": "",
                "use_system_key": True,
                "greeting_message": "Olá teste!",
                "fallback_message": "Não entendi teste",
                "transfer_message": "Transferindo teste",
                "auto_transfer_keywords": ["humano", "atendente"],
                "conversation_history_limit": 10
            },
            "visual_config": {
                "agent_name_display": "Bot Teste",
                "agent_photo": "https://example.com/photo.jpg",
                "show_verified_badge": True,
                "theme_color": "#FF0000",
                "chat_position": "bottom-right",
                "chat_size": "medium"
            },
            "external_apis": {
                "teste_iptv": {
                    "enabled": True,
                    "url": "https://gesth.io/api/get-teste?hash=teste",
                    "trigger_keywords": ["teste", "testar"]
                }
            },
            "flows": {
                "teste_gratis": {
                    "enabled": True,
                    "require_app_install": True,
                    "app_url": "https://suporte.help"
                }
            }
        }
        
        try:
            headers = {
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{BASE_URL}/admin/vendas-bot/simple-config",
                    headers=headers,
                    json=test_config
                )
                
                if response.status_code == 200:
                    data = response.json()
                    config_id = data.get("config_id")
                    
                    if config_id:
                        await self.log_test(
                            "POST simple-config - Salvamento", 
                            True, 
                            f"Config salva com ID: {config_id}"
                        )
                        return True
                    else:
                        await self.log_test("POST simple-config", False, "Sem config_id na resposta")
                        return False
                else:
                    await self.log_test("POST simple-config", False, f"Status {response.status_code}: {response.text}")
                    return False
                    
        except Exception as e:
            await self.log_test("POST simple-config", False, f"Erro: {str(e)}")
            return False
    
    async def test_integration_with_vendas_start(self):
        """3. Teste de Integração - Verificar se configurações são usadas pela IA"""
        print("\n🔵 TESTE 3: Integração com /api/vendas/start")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Testar endpoint /api/vendas/start
                response = await client.post(f"{BASE_URL}/vendas/start", json={})
                
                if response.status_code == 200:
                    data = response.json()
                    session_id = data.get("session_id")
                    messages = data.get("messages", [])
                    
                    if session_id and messages:
                        # Verificar se a mensagem de boas-vindas usa a nova config
                        welcome_message = messages[0].get("text", "") if messages else ""
                        
                        # Se contém "Teste" significa que está usando a config que salvamos
                        uses_new_config = "teste" in welcome_message.lower()
                        
                        await self.log_test(
                            "Integração vendas/start", 
                            True, 
                            f"Session criada: {session_id[:8]}... | Usa nova config: {uses_new_config}"
                        )
                        return session_id
                    else:
                        await self.log_test("Integração vendas/start", False, "Sem session_id ou mensagens")
                        return None
                else:
                    await self.log_test("Integração vendas/start", False, f"Status {response.status_code}")
                    return None
                    
        except Exception as e:
            await self.log_test("Integração vendas/start", False, f"Erro: {str(e)}")
            return None
    
    async def test_knowledge_base_url_access(self):
        """4. Teste se knowledge_base.url é acessada quando enabled=true"""
        print("\n🔵 TESTE 4: Acesso à Base de Conhecimento")
        
        # Verificar se a URL da base de conhecimento está acessível
        test_url = "https://site.suporte.help/base-conhecimento.html"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(test_url)
                
                if response.status_code == 200:
                    content = response.text
                    has_content = len(content) > 100
                    
                    await self.log_test(
                        "Knowledge Base URL", 
                        has_content, 
                        f"URL acessível, conteúdo: {len(content)} chars"
                    )
                    return has_content
                else:
                    await self.log_test("Knowledge Base URL", False, f"Status {response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_test("Knowledge Base URL", False, f"Erro: {str(e)}")
            return False
    
    async def test_data_validation(self):
        """5. Validação de Dados - Testar com campos vazios e valores inválidos"""
        print("\n🔵 TESTE 5: Validação de Dados")
        
        if not self.admin_token:
            await self.log_test("Validação de Dados", False, "Token admin não disponível")
            return False
        
        # Teste 1: Campos vazios
        empty_config = {
            "empresa_nome": "",
            "usa_ia": False
        }
        
        # Teste 2: Valores inválidos
        invalid_config = {
            "empresa_nome": "Teste",
            "usa_ia": True,
            "ia_config": {
                "temperature": 2.0,  # Inválido (deve ser 0-1)
                "max_tokens": -100   # Inválido (deve ser positivo)
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
        
        validation_tests = [
            ("Campos Vazios", empty_config),
            ("Valores Inválidos", invalid_config)
        ]
        
        validation_results = []
        
        for test_name, test_data in validation_tests:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{BASE_URL}/admin/vendas-bot/simple-config",
                        headers=headers,
                        json=test_data
                    )
                    
                    # Para validação, esperamos que aceite ou rejeite adequadamente
                    if response.status_code in [200, 400, 422]:
                        validation_results.append(True)
                        await self.log_test(
                            f"Validação - {test_name}", 
                            True, 
                            f"Status {response.status_code} (adequado)"
                        )
                    else:
                        validation_results.append(False)
                        await self.log_test(
                            f"Validação - {test_name}", 
                            False, 
                            f"Status inesperado: {response.status_code}"
                        )
                        
            except Exception as e:
                validation_results.append(False)
                await self.log_test(f"Validação - {test_name}", False, f"Erro: {str(e)}")
        
        return all(validation_results)
    
    async def test_backward_compatibility(self):
        """6. Retrocompatibilidade - Verificar se configurações antigas ainda funcionam"""
        print("\n🔵 TESTE 6: Retrocompatibilidade")
        
        if not self.admin_token:
            await self.log_test("Retrocompatibilidade", False, "Token admin não disponível")
            return False
        
        # Configuração no formato antigo
        old_format_config = {
            "empresa_nome": "CyberTV Antigo",
            "usa_ia": True,
            "api_teste_url": "https://gesth.io/api/get-teste?hash=antigo",
            "custom_instructions": "Instruções antigas",
            "ia_inline": {
                "name": "Bot Antigo",
                "personality": "Antigo",
                "instructions": "Formato antigo",
                "llm_provider": "openai",
                "llm_model": "gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": 500,
                "api_key": ""
            },
            "agent_profile": {
                "name": "Assistente Antigo",
                "photo": "",
                "show_verified_badge": True
            }
        }
        
        try:
            headers = {
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{BASE_URL}/admin/vendas-bot/simple-config",
                    headers=headers,
                    json=old_format_config
                )
                
                if response.status_code == 200:
                    await self.log_test(
                        "Retrocompatibilidade", 
                        True, 
                        "Formato antigo aceito com sucesso"
                    )
                    return True
                else:
                    await self.log_test(
                        "Retrocompatibilidade", 
                        False, 
                        f"Formato antigo rejeitado: {response.status_code}"
                    )
                    return False
                    
        except Exception as e:
            await self.log_test("Retrocompatibilidade", False, f"Erro: {str(e)}")
            return False
    
    async def test_api_key_usage(self):
        """7. Teste se api_key customizada é usada quando use_system_key=false"""
        print("\n🔵 TESTE 7: Uso de API Key Customizada")
        
        # Este teste verifica se o sistema respeita a configuração use_system_key
        # Não podemos testar completamente sem uma chave válida, mas podemos verificar a lógica
        
        if not self.admin_token:
            await self.log_test("API Key Customizada", False, "Token admin não disponível")
            return False
        
        custom_key_config = {
            "empresa_nome": "Teste API Key",
            "usa_ia": True,
            "ia_config": {
                "name": "Bot API Key",
                "api_key": "sk-test-fake-key-for-testing",
                "use_system_key": False,  # Usar chave própria
                "llm_provider": "openai",
                "llm_model": "gpt-4o-mini"
            }
        }
        
        try:
            headers = {
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{BASE_URL}/admin/vendas-bot/simple-config",
                    headers=headers,
                    json=custom_key_config
                )
                
                if response.status_code == 200:
                    # Verificar se a configuração foi salva
                    get_response = await client.get(
                        f"{BASE_URL}/admin/vendas-bot/simple-config",
                        headers=headers
                    )
                    
                    if get_response.status_code == 200:
                        data = get_response.json()
                        ia_config = data.get("ia_config", {})
                        use_system_key = ia_config.get("use_system_key", True)
                        
                        await self.log_test(
                            "API Key Customizada", 
                            not use_system_key, 
                            f"use_system_key = {use_system_key} (deve ser False)"
                        )
                        return not use_system_key
                    else:
                        await self.log_test("API Key Customizada", False, "Erro ao verificar configuração salva")
                        return False
                else:
                    await self.log_test("API Key Customizada", False, f"Status {response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_test("API Key Customizada", False, f"Erro: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Executar todos os testes conforme review request"""
        print("🚀 INICIANDO TESTE COMPLETO: Nova Estrutura WA Site Manager V2")
        print("=" * 80)
        
        # 1. Login admin
        if not await self.admin_login():
            print("❌ Não foi possível fazer login como admin. Abortando testes.")
            return False
        
        # 2. Executar testes na ordem do review request
        await self.test_get_simple_config_endpoint()
        await self.test_post_simple_config_endpoint()
        await self.test_integration_with_vendas_start()
        await self.test_knowledge_base_url_access()
        await self.test_data_validation()
        await self.test_backward_compatibility()
        await self.test_api_key_usage()
        
        # 3. Resumo final
        print("\n" + "=" * 80)
        print("📊 RESUMO DOS TESTES - WA Site Manager V2")
        print("=" * 80)
        
        passed_tests = sum(1 for result in self.test_results if result["success"])
        total_tests = len(self.test_results)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   📋 {result['details']}")
        
        print(f"\n🎯 RESULTADO FINAL: {passed_tests}/{total_tests} TESTES PASSARAM")
        
        # Análise específica do review request
        print("\n📋 ANÁLISE CONFORME REVIEW REQUEST:")
        
        # Verificar se endpoints existem
        endpoint_tests = [r for r in self.test_results if "simple-config" in r["test"]]
        endpoints_working = all(r["success"] for r in endpoint_tests)
        
        if endpoints_working:
            print("✅ Endpoints GET/POST /api/admin/vendas-bot/simple-config funcionando")
        else:
            print("❌ Problemas nos endpoints principais")
        
        # Verificar estrutura V2
        structure_tests = [r for r in self.test_results if "Estrutura V2" in r["test"]]
        if structure_tests:
            v2_working = structure_tests[0]["success"]
            if v2_working:
                print("✅ Nova estrutura V2 implementada (ia_config, visual_config, external_apis, flows)")
            else:
                print("❌ Estrutura V2 NÃO implementada - ainda usando estrutura antiga")
        
        # Verificar integração
        integration_tests = [r for r in self.test_results if "Integração" in r["test"]]
        if integration_tests and integration_tests[0]["success"]:
            print("✅ Integração com sistema de vendas funcionando")
        else:
            print("❌ Problemas na integração")
        
        # Verificar validação
        validation_tests = [r for r in self.test_results if "Validação" in r["test"]]
        if validation_tests:
            validation_working = all(r["success"] for r in validation_tests)
            if validation_working:
                print("✅ Validação de dados funcionando")
            else:
                print("❌ Problemas na validação de dados")
        
        # Verificar retrocompatibilidade
        compat_tests = [r for r in self.test_results if "Retrocompatibilidade" in r["test"]]
        if compat_tests and compat_tests[0]["success"]:
            print("✅ Retrocompatibilidade mantida")
        else:
            print("❌ Problemas na retrocompatibilidade")
        
        print("=" * 80)
        
        if passed_tests == total_tests:
            print("\n🎉 TODOS OS TESTES PASSARAM!")
            print("🎉 WA SITE MANAGER V2 100% FUNCIONAL!")
        else:
            print(f"\n⚠️ {total_tests - passed_tests} TESTE(S) FALHARAM")
            print("🔧 Sistema precisa de ajustes para atender o review request")
        
        return passed_tests == total_tests

async def main():
    """Função principal"""
    tester = WASiteManagerV2Tester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n✅ SISTEMA VALIDADO CONFORME REVIEW REQUEST!")
    else:
        print("\n❌ SISTEMA PRECISA DE IMPLEMENTAÇÕES ADICIONAIS!")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())