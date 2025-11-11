#!/usr/bin/env python3
"""
TESTE COMPLETO: WA Site /vendas - IA não está lendo instruções e enviando mensagens

CONTEXTO:
- Servidor externo: suporte.help (198.96.94.106)
- Backend corrigido: httpx==0.27.2 instalado
- openai==1.12.0 instalado  
- AsyncOpenAI agora pode ser criado sem erro
- Rotas /api/vendas/* reativadas em server.py
- vendas_ai_humanized.py usando OpenAI diretamente

PROBLEMAS REPORTADOS:
1. IA não está lendo as instruções configuradas (ia_inline.instructions no MongoDB)
2. Não consegue enviar mensagens na conversa /vendas

TESTES NECESSÁRIOS:
1. Verificar Configuração no MongoDB
2. Teste POST /api/vendas/start
3. Teste POST /api/vendas/message
4. Verificar Logs do Backend
"""

import asyncio
import httpx
import json
import uuid
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

# Configuração
BACKEND_URL = "https://suporte.help"
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "support_chat"

class VendasTester:
    def __init__(self):
        self.client = None
        self.db = None
        self.session_id = None
        self.test_results = []
        
    async def setup(self):
        """Conectar ao MongoDB"""
        try:
            self.client = AsyncIOMotorClient(MONGO_URL)
            self.db = self.client[DB_NAME]
            print("✅ Conectado ao MongoDB")
        except Exception as e:
            print(f"❌ Erro ao conectar MongoDB: {e}")
            raise
    
    async def cleanup(self):
        """Fechar conexões"""
        if self.client:
            self.client.close()
    
    def log_result(self, test_name: str, success: bool, details: str):
        """Registrar resultado do teste"""
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{status} - {test_name}")
        print(f"   {details}")
        print()
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    async def test_1_mongodb_config(self):
        """TESTE 1: Verificar Configuração no MongoDB"""
        try:
            # Verificar vendas_simple_config
            config = await self.db.vendas_simple_config.find_one({})
            
            if not config:
                self.log_result(
                    "1. MongoDB Config", 
                    False, 
                    "vendas_simple_config não encontrado no MongoDB"
                )
                return False
            
            usa_ia = config.get("usa_ia", False)
            ia_inline = config.get("ia_inline", {})
            instructions = ia_inline.get("instructions", "") if ia_inline else ""
            
            details = f"""
Config encontrada:
- usa_ia: {usa_ia}
- ia_inline existe: {'Sim' if ia_inline else 'Não'}
- instructions length: {len(instructions)} chars
- ia_inline.name: {ia_inline.get('name', 'N/A') if ia_inline else 'N/A'}
- ia_inline.api_key: {'Configurada' if ia_inline.get('api_key') else 'FALTANDO'}"""
            
            success = usa_ia and ia_inline and len(instructions) > 0
            
            self.log_result("1. MongoDB Config", success, details)
            return success
            
        except Exception as e:
            self.log_result("1. MongoDB Config", False, f"Erro: {e}")
            return False
    
    async def test_2_vendas_start(self):
        """TESTE 2: POST /api/vendas/start"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{BACKEND_URL}/api/vendas/start",
                    json={
                        "whatsapp": "5511999999999",
                        "name": "Teste Cliente"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.session_id = data.get("session_id")
                    messages = data.get("messages", [])
                    
                    welcome_msg = messages[0] if messages else {}
                    welcome_text = welcome_msg.get("text", "")
                    
                    # Verificar se a mensagem menciona "Juliana" (das instruções)
                    has_juliana = "juliana" in welcome_text.lower()
                    
                    details = f"""
Status: {response.status_code}
Session ID: {self.session_id}
Welcome message: {welcome_text[:100]}...
Menciona 'Juliana': {has_juliana}
Messages count: {len(messages)}"""
                    
                    success = self.session_id and len(welcome_text) > 10
                    self.log_result("2. POST /vendas/start", success, details)
                    return success
                else:
                    self.log_result(
                        "2. POST /vendas/start", 
                        False, 
                        f"Status: {response.status_code}, Response: {response.text}"
                    )
                    return False
                    
        except Exception as e:
            self.log_result("2. POST /vendas/start", False, f"Erro: {e}")
            return False
    
    async def test_3_vendas_message_hello(self):
        """TESTE 3: POST /api/vendas/message - Saudação"""
        if not self.session_id:
            self.log_result("3. Message Hello", False, "Session ID não disponível")
            return False
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{BACKEND_URL}/api/vendas/message",
                    json={
                        "session_id": self.session_id,
                        "text": "Olá"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    messages = data.get("messages", [])
                    
                    # Buscar resposta do bot
                    bot_message = None
                    for msg in messages:
                        if msg.get("from_type") == "bot":
                            bot_message = msg
                            break
                    
                    if bot_message:
                        bot_text = bot_message.get("text", "")
                        has_juliana = "juliana" in bot_text.lower()
                        
                        details = f"""
Status: {response.status_code}
Bot response: {bot_text[:150]}...
Menciona 'Juliana': {has_juliana}
Response length: {len(bot_text)} chars"""
                        
                        success = len(bot_text) > 10
                        self.log_result("3. Message Hello", success, details)
                        return success
                    else:
                        self.log_result("3. Message Hello", False, "Nenhuma resposta do bot encontrada")
                        return False
                else:
                    self.log_result(
                        "3. Message Hello", 
                        False, 
                        f"Status: {response.status_code}, Response: {response.text}"
                    )
                    return False
                    
        except Exception as e:
            self.log_result("3. Message Hello", False, f"Erro: {e}")
            return False
    
    async def test_4_vendas_message_plans(self):
        """TESTE 4: POST /api/vendas/message - Pergunta sobre planos"""
        if not self.session_id:
            self.log_result("4. Message Plans", False, "Session ID não disponível")
            return False
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{BACKEND_URL}/api/vendas/message",
                    json={
                        "session_id": self.session_id,
                        "text": "Quais são os planos disponíveis?"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    messages = data.get("messages", [])
                    
                    # Buscar resposta do bot
                    bot_message = None
                    for msg in messages:
                        if msg.get("from_type") == "bot":
                            bot_message = msg
                            break
                    
                    if bot_message:
                        bot_text = bot_message.get("text", "")
                        
                        # Verificar se menciona preços ou informações relevantes
                        has_price_info = any(word in bot_text.lower() for word in [
                            "r$", "real", "preço", "valor", "plano", "tela", "mês"
                        ])
                        
                        details = f"""
Status: {response.status_code}
Bot response: {bot_text[:200]}...
Contém info de preços: {has_price_info}
Response length: {len(bot_text)} chars"""
                        
                        success = len(bot_text) > 20 and has_price_info
                        self.log_result("4. Message Plans", success, details)
                        return success
                    else:
                        self.log_result("4. Message Plans", False, "Nenhuma resposta do bot encontrada")
                        return False
                else:
                    self.log_result(
                        "4. Message Plans", 
                        False, 
                        f"Status: {response.status_code}, Response: {response.text}"
                    )
                    return False
                    
        except Exception as e:
            self.log_result("4. Message Plans", False, f"Erro: {e}")
            return False
    
    async def test_5_vendas_messages_history(self):
        """TESTE 5: GET /api/vendas/messages/{session_id}"""
        if not self.session_id:
            self.log_result("5. Messages History", False, "Session ID não disponível")
            return False
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{BACKEND_URL}/api/vendas/messages/{self.session_id}"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    messages = data.get("messages", [])
                    
                    client_msgs = [m for m in messages if m.get("from_type") == "client"]
                    bot_msgs = [m for m in messages if m.get("from_type") == "bot"]
                    
                    details = f"""
Status: {response.status_code}
Total messages: {len(messages)}
Client messages: {len(client_msgs)}
Bot messages: {len(bot_msgs)}
Messages structure: OK"""
                    
                    success = len(messages) > 0 and len(bot_msgs) > 0
                    self.log_result("5. Messages History", success, details)
                    return success
                else:
                    self.log_result(
                        "5. Messages History", 
                        False, 
                        f"Status: {response.status_code}, Response: {response.text}"
                    )
                    return False
                    
        except Exception as e:
            self.log_result("5. Messages History", False, f"Erro: {e}")
            return False
    
    async def test_6_mongodb_persistence(self):
        """TESTE 6: Verificar persistência no MongoDB"""
        if not self.session_id:
            self.log_result("6. MongoDB Persistence", False, "Session ID não disponível")
            return False
        
        try:
            # Verificar se a sessão foi salva
            session = await self.db.vendas_sessions.find_one({"session_id": self.session_id})
            
            # Verificar se as mensagens foram salvas
            messages = await self.db.vendas_messages.find({"session_id": self.session_id}).to_list(None)
            
            client_msgs = [m for m in messages if m.get("from_type") == "client"]
            bot_msgs = [m for m in messages if m.get("from_type") == "bot"]
            
            details = f"""
Session exists: {'Sim' if session else 'Não'}
Total messages in DB: {len(messages)}
Client messages: {len(client_msgs)}
Bot messages: {len(bot_msgs)}
Session data: {session.get('whatsapp') if session else 'N/A'}"""
            
            success = session is not None and len(messages) > 0 and len(bot_msgs) > 0
            self.log_result("6. MongoDB Persistence", success, details)
            return success
            
        except Exception as e:
            self.log_result("6. MongoDB Persistence", False, f"Erro: {e}")
            return False
    
    async def check_backend_logs(self):
        """Verificar logs do backend para erros"""
        try:
            import subprocess
            
            # Verificar logs do supervisor
            result = subprocess.run(
                ["tail", "-n", "50", "/var/log/supervisor/backend.err.log"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logs = result.stdout
                
                # Procurar por erros relacionados ao vendas
                vendas_errors = []
                for line in logs.split('\n'):
                    if any(keyword in line.lower() for keyword in ['vendas', 'openai', 'error', 'exception']):
                        vendas_errors.append(line)
                
                print("=== LOGS DO BACKEND (últimas 50 linhas) ===")
                if vendas_errors:
                    print("Erros relacionados ao vendas encontrados:")
                    for error in vendas_errors[-10:]:  # Últimos 10 erros
                        print(f"  {error}")
                else:
                    print("Nenhum erro relacionado ao vendas encontrado nos logs recentes")
                print()
            
        except Exception as e:
            print(f"❌ Erro ao verificar logs: {e}")
    
    async def run_all_tests(self):
        """Executar todos os testes"""
        print("🚀 INICIANDO TESTE COMPLETO DO SISTEMA /VENDAS")
        print("=" * 60)
        print()
        
        await self.setup()
        
        # Executar testes em sequência
        tests = [
            self.test_1_mongodb_config,
            self.test_2_vendas_start,
            self.test_3_vendas_message_hello,
            self.test_4_vendas_message_plans,
            self.test_5_vendas_messages_history,
            self.test_6_mongodb_persistence
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            success = await test()
            if success:
                passed += 1
        
        # Verificar logs
        await self.check_backend_logs()
        
        # Resumo final
        print("=" * 60)
        print("📊 RESUMO DOS TESTES")
        print("=" * 60)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
        
        print()
        print(f"🎯 RESULTADO FINAL: {passed}/{total} testes passaram ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 TODOS OS TESTES PASSARAM! Sistema /vendas funcionando corretamente.")
        else:
            print("⚠️ ALGUNS TESTES FALHARAM. Verifique os detalhes acima.")
        
        await self.cleanup()
        
        return passed, total

async def main():
    """Função principal"""
    tester = VendasTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())