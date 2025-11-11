#!/usr/bin/env python3
"""
🧪 TESTE SISTEMÁTICO - ABA 15: WA SITE (BOT DE VENDAS)

PROGRESSO: 12/16 ABAs testadas ✅ | 2 com problemas (endpoints não encontrados)

ABA 15 - WA SITE - FUNCIONALIDADES A TESTAR:
1. Admin Login - POST /api/auth/admin/login
2. GET /api/admin/vendas-bot/config - Obter configuração do WA Site
3. POST /api/admin/vendas-bot/simple-config - Salvar configuração do WA Site
4. POST /api/admin/vendas-bot/upload-instructions - Upload de instruções (TXT)
5. POST /api/vendas/start - Criar sessão de chat
6. POST /api/vendas/message - Enviar mensagem ao bot

Admin: admin@admin.com / 102030@ab
Backend: Usar REACT_APP_BACKEND_URL do .env
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime
import io

# Read backend URL from environment
def get_backend_url():
    """Get backend URL from frontend .env file"""
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except:
        pass
    return "http://localhost:8001"

BACKEND_URL = get_backend_url() + "/api"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "102030@ab"

class WASiteTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_results = []
        self.session_id = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
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
            # Show only relevant parts of response
            if 'token' in response_data:
                print(f"   Token: {response_data['token'][:50]}...")
            elif 'config' in response_data:
                print(f"   Config keys: {list(response_data.get('config', {}).keys())}")
            elif 'message' in response_data:
                print(f"   Message: {response_data['message']}")
            else:
                print(f"   Response: {json.dumps(response_data, indent=2)[:300]}...")
        print()
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
    
    async def test_admin_login(self):
        """Test 1: Admin Login - POST /api/auth/admin/login"""
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
                    if self.auth_token:
                        self.log_result("Admin Login", True, f"Login successful with credentials {ADMIN_EMAIL}", data)
                        return True
                    else:
                        self.log_result("Admin Login", False, "No token in response", data)
                        return False
                else:
                    error_text = await response.text()
                    self.log_result("Admin Login", False, f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_result("Admin Login", False, f"Exception: {str(e)}")
            return False
    
    async def test_get_wa_site_config(self):
        """Test 2: GET /api/admin/vendas-bot/config - Obter configuração do WA Site"""
        print("📋 TESTE 2: OBTER CONFIGURAÇÃO DO WA SITE")
        print("=" * 50)
        
        if not self.auth_token:
            self.log_result("GET WA Site Config", False, "No auth token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            async with self.session.get(f"{BACKEND_URL}/admin/vendas-bot/config", headers=headers) as response:
                if response.status == 200:
                    config_data = await response.json()
                    self.log_result("GET /admin/vendas-bot/config", True, "Configuração obtida com sucesso", config_data)
                    return True
                else:
                    error_text = await response.text()
                    self.log_result("GET /admin/vendas-bot/config", False, f"Status {response.status}: {error_text}")
                    return False
        except Exception as e:
            self.log_result("GET /admin/vendas-bot/config", False, f"Exception: {str(e)}")
            return False
    
    async def test_save_wa_site_config(self):
        """Test 3: POST /api/admin/vendas-bot/simple-config - Salvar configuração do WA Site"""
        print("💾 TESTE 3: SALVAR CONFIGURAÇÃO DO WA SITE")
        print("=" * 50)
        
        if not self.auth_token:
            self.log_result("Save WA Site Config", False, "No auth token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test data with correct V2 format based on WASiteConfigV2 model
        config_data = {
            "empresa_nome": "Empresa Teste",
            "usa_ia": True,
            "is_active": True,
            "ia_config": {
                "name": "Juliana",
                "role": "Consultora de Vendas",
                "personality": "Profissional, amigável e prestativa",
                "instructions": "Você é Juliana, assistente de vendas da empresa. Seja educada e ajude com informações sobre nossos produtos e serviços.",
                "knowledge_base": {
                    "enabled": True,
                    "sources": [
                        {
                            "type": "url",
                            "url": "https://example.com/knowledge-base",
                            "description": "Base de conhecimento da empresa"
                        }
                    ],
                    "fallback_text": "Consulte nossa base de conhecimento para mais informações."
                },
                "llm_provider": "openai",
                "llm_model": "gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": 500,
                "api_key": "sk-test-key-for-wa-site-bot",
                "use_system_key": False,
                "greeting_message": "Olá! Como posso ajudar você hoje?",
                "fallback_message": "Desculpe, não entendi. Pode reformular?",
                "transfer_message": "Vou transferir você para um atendente humano."
            },
            "visual_config": {
                "agent_photo": "",
                "agent_name_display": "Juliana Silva",
                "show_verified_badge": True,
                "theme_color": "#0084ff",
                "chat_position": "bottom-right",
                "chat_size": "medium"
            }
        }
        
        try:
            async with self.session.post(f"{BACKEND_URL}/admin/vendas-bot/simple-config", json=config_data, headers=headers) as response:
                if response.status in [200, 201]:
                    response_data = await response.json()
                    self.log_result("POST /admin/vendas-bot/simple-config", True, "Configuração salva com sucesso", response_data)
                    return True
                else:
                    error_text = await response.text()
                    self.log_result("POST /admin/vendas-bot/simple-config", False, f"Status {response.status}: {error_text}")
                    return False
        except Exception as e:
            self.log_result("POST /admin/vendas-bot/simple-config", False, f"Exception: {str(e)}")
            return False
    
    async def test_upload_instructions(self):
        """Test 4: POST /api/admin/vendas-bot/upload-instructions - Upload de instruções (TXT)"""
        print("📄 TESTE 4: UPLOAD DE INSTRUÇÕES (TXT)")
        print("=" * 50)
        
        if not self.auth_token:
            self.log_result("Upload Instructions", False, "No auth token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Create test TXT file content
        instructions_content = """Instruções para o Bot de Vendas:

1. Sempre cumprimente o cliente de forma educada
2. Pergunte como pode ajudar
3. Ofereça informações sobre produtos e serviços
4. Seja proativo em sugerir soluções
5. Mantenha um tom profissional e amigável
6. Se não souber algo, direcione para um atendente humano

Produtos disponíveis:
- Plano Básico: R$ 29,90/mês
- Plano Premium: R$ 49,90/mês
- Plano Empresarial: R$ 99,90/mês

Contato para suporte: suporte@empresa.com
"""
        
        try:
            # Create form data with file upload
            form_data = aiohttp.FormData()
            form_data.add_field('file', 
                              io.BytesIO(instructions_content.encode('utf-8')), 
                              filename='instructions.txt', 
                              content_type='text/plain')
            
            async with self.session.post(f"{BACKEND_URL}/admin/vendas-bot/upload-instructions", 
                                       data=form_data, headers=headers) as response:
                if response.status in [200, 201]:
                    response_data = await response.json()
                    self.log_result("POST /admin/vendas-bot/upload-instructions", True, "Instruções enviadas com sucesso", response_data)
                    return True
                elif response.status == 404:
                    self.log_result("POST /admin/vendas-bot/upload-instructions", False, "Endpoint não disponível na versão V2 - funcionalidade movida para configuração inline")
                    return False
                else:
                    error_text = await response.text()
                    self.log_result("POST /admin/vendas-bot/upload-instructions", False, f"Status {response.status}: {error_text}")
                    return False
        except Exception as e:
            self.log_result("POST /admin/vendas-bot/upload-instructions", False, f"Exception: {str(e)}")
            return False
    
    async def test_create_chat_session(self):
        """Test 5: POST /api/vendas/start - Criar sessão de chat"""
        print("🚀 TESTE 5: CRIAR SESSÃO DE CHAT")
        print("=" * 50)
        
        # Note: This endpoint might not require auth token based on typical chat implementations
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        session_data = {
            "whatsapp": "5511999999999",
            "name": "Cliente Teste"
        }
        
        try:
            async with self.session.post(f"{BACKEND_URL}/vendas/start", json=session_data, headers=headers) as response:
                if response.status in [200, 201]:
                    response_data = await response.json()
                    self.session_id = response_data.get("session_id")
                    self.log_result("POST /vendas/start", True, f"Sessão criada com sucesso. Session ID: {self.session_id}", response_data)
                    return True
                else:
                    error_text = await response.text()
                    self.log_result("POST /vendas/start", False, f"Status {response.status}: {error_text}")
                    return False
        except Exception as e:
            self.log_result("POST /vendas/start", False, f"Exception: {str(e)}")
            return False
    
    async def test_send_message_to_bot(self):
        """Test 6: POST /api/vendas/message - Enviar mensagem ao bot"""
        print("💬 TESTE 6: ENVIAR MENSAGEM AO BOT")
        print("=" * 50)
        
        if not self.session_id:
            self.log_result("Send Message to Bot", False, "No session_id available - create session first")
            return False
        
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        message_data = {
            "session_id": self.session_id,
            "text": "Olá! Gostaria de saber mais sobre os planos disponíveis."
        }
        
        try:
            async with self.session.post(f"{BACKEND_URL}/vendas/message", json=message_data, headers=headers) as response:
                if response.status in [200, 201]:
                    response_data = await response.json()
                    bot_response = response_data.get("response", "")
                    self.log_result("POST /vendas/message", True, f"Mensagem enviada e bot respondeu: '{bot_response[:100]}...'", response_data)
                    return True
                else:
                    error_text = await response.text()
                    self.log_result("POST /vendas/message", False, f"Status {response.status}: {error_text}")
                    return False
        except Exception as e:
            self.log_result("POST /vendas/message", False, f"Exception: {str(e)}")
            return False
    
    async def test_bot_conversation_flow(self):
        """Test 7: Testar fluxo completo de conversa com o bot"""
        print("🤖 TESTE 7: FLUXO COMPLETO DE CONVERSA")
        print("=" * 50)
        
        if not self.session_id:
            self.log_result("Bot Conversation Flow", False, "No session_id available")
            return False
        
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        # Test multiple messages to verify bot is responding consistently
        test_messages = [
            "Qual é o preço do plano básico?",
            "E o plano premium?",
            "Como faço para contratar?",
            "Obrigado pela informação!"
        ]
        
        successful_responses = 0
        
        for i, message in enumerate(test_messages, 1):
            try:
                message_data = {
                    "session_id": self.session_id,
                    "text": message
                }
                
                async with self.session.post(f"{BACKEND_URL}/vendas/message", json=message_data, headers=headers) as response:
                    if response.status in [200, 201]:
                        response_data = await response.json()
                        bot_response = response_data.get("response", "")
                        print(f"   Mensagem {i}: '{message}' → Bot: '{bot_response[:80]}...'")
                        successful_responses += 1
                        await asyncio.sleep(1)  # Small delay between messages
                    else:
                        print(f"   Mensagem {i}: ERRO {response.status}")
                        break
            except Exception as e:
                print(f"   Mensagem {i}: EXCEPTION {str(e)}")
                break
        
        if successful_responses == len(test_messages):
            self.log_result("Bot Conversation Flow", True, f"Bot respondeu a todas as {successful_responses} mensagens corretamente")
            return True
        else:
            self.log_result("Bot Conversation Flow", False, f"Bot respondeu apenas {successful_responses}/{len(test_messages)} mensagens")
            return False
    
    async def run_all_tests(self):
        """Run all WA Site tests in sequence"""
        print("🧪 INICIANDO TESTE SISTEMÁTICO - ABA 15: WA SITE (BOT DE VENDAS)")
        print("=" * 70)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin Credentials: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        print("=" * 70)
        print()
        
        # Test 1: Authentication (required for admin endpoints)
        auth_success = await self.test_admin_login()
        
        if auth_success:
            # Test 2-4: Admin configuration endpoints
            await self.test_get_wa_site_config()
            await self.test_save_wa_site_config()
            await self.test_upload_instructions()
        else:
            print("❌ Authentication failed - skipping admin config tests")
        
        # Test 5-7: Bot functionality (may work without admin auth)
        await self.test_create_chat_session()
        if self.session_id:
            await self.test_send_message_to_bot()
            await self.test_bot_conversation_flow()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 RESUMO DOS TESTES - ABA 15: WA SITE (BOT DE VENDAS)")
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
        print("🎯 OBJETIVO: Verificar se o WA Site (Bot de Vendas) está 100% funcional")
        
        if failed_tests == 0:
            print("🎉 TODOS OS TESTES PASSARAM! ABA 15 (WA SITE) ESTÁ 100% FUNCIONAL!")
            print("✅ Pode avançar para ABA 16 (BACKUP) conforme plano sistemático")
        else:
            print(f"⚠️  {failed_tests} funcionalidades ainda precisam de atenção.")
            print("🔧 Verifique os endpoints que falharam antes de avançar para próxima ABA")
        
        print("=" * 70)

async def main():
    """Main test execution"""
    async with WASiteTester() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())