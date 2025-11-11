#!/usr/bin/env python3
"""
TESTE CRÍTICO: ENVIO E RECEBIMENTO DE MENSAGENS

CONTEXTO:
- Usuário reporta "Erro ao enviar mensagem" tanto para clientes quanto atendentes
- URL do backend: https://wppconnect-fix.preview.emergentagent.com
- Endpoint problemático: POST /api/messages

TESTE SOLICITADO:

1. TESTE LOGIN DO AGENTE:
   - POST /api/agents/login
   - Body: {"username": "fabio21", "password": "102030@ab"}
   - Verificar se login retorna token válido

2. TESTE ENVIO DE MENSAGEM (AGENTE → CLIENTE):
   - POST /api/messages
   - Header: Authorization: Bearer {token_do_agente}
   - Body: {
       "from_type": "agent",
       "from_id": "{agent_id_do_token}",
       "to_type": "client",
       "to_id": "19989612020",  
       "ticket_id": "{ticket_id_existente}",
       "kind": "text",
       "text": "Teste de mensagem do agente",
       "file_url": null
     }
   - Verificar se retorna 200 OK e message_id

3. TESTE LOGIN DO CLIENTE:
   - POST /api/clients/login
   - Body: {"whatsapp": "19989612020", "pin": "01"}
   - Verificar se login retorna token válido

4. TESTE ENVIO DE MENSAGEM (CLIENTE → SISTEMA):
   - POST /api/messages
   - Header: Authorization: Bearer {token_do_cliente}
   - Body: {
       "from_type": "client",
       "from_id": "19989612020",
       "to_type": "agent",
       "to_id": null,
       "kind": "text",
       "text": "Teste de mensagem do cliente",
       "file_url": null
     }
   - Verificar se retorna 200 OK e message_id

5. VERIFICAR LOGS DO BACKEND:
   - Verificar se há erros 500, 422, 400, ou exceptions não tratadas
   - Verificar se há problemas com WebSocket ou serialização

OBJETIVO: Identificar por que o envio de mensagens está falhando e retornando "Erro ao enviar mensagem" no frontend.

CREDENCIAIS CONHECIDAS:
- Agente: fabio21 / 102030@ab
- Cliente: 19989612020 / PIN 01

IMPORTANTE: Este é um problema crítico que está impedindo a funcionalidade principal do sistema.
"""

import asyncio
import aiohttp
import json
import os
import subprocess
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import uuid

# Configurações
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://wppconnect-fix.preview.emergentagent.com')
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'support_chat')

class MessageSendingTestRunner:
    def __init__(self):
        self.client = AsyncIOMotorClient(MONGO_URL)
        self.db = self.client[DB_NAME]
        self.session = None
        self.test_results = []
        
        # Credenciais do review request
        self.agent_credentials = {
            "login": "fabio21",
            "password": "102030@ab"
        }
        
        self.client_credentials = {
            "whatsapp": "19989612020",
            "pin": "01"
        }
        
        # Tokens e IDs obtidos durante os testes
        self.agent_token = None
        self.agent_id = None
        self.client_token = None
        self.client_id = None
        self.ticket_id = None
        
    async def setup_session(self):
        """Configurar sessão HTTP"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Limpar sessão HTTP"""
        if self.session:
            await self.session.close()
            
    def log_result(self, test_name: str, success: bool, message: str = "", details: dict = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}"
        if message:
            result += f" - {message}"
        print(result)
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {}
        })
        
    async def make_request(self, method: str, endpoint: str, data: dict = None, 
                          token: str = None, headers: dict = None) -> tuple[bool, dict, int]:
        """Make HTTP request with error handling"""
        url = f"{BACKEND_URL}/api{endpoint}"
        
        request_headers = {"Content-Type": "application/json"}
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        if headers:
            request_headers.update(headers)
            
        try:
            if method.upper() == "GET":
                async with self.session.get(url, headers=request_headers) as response:
                    status = response.status
                    try:
                        data = await response.json()
                    except:
                        data = {"text": await response.text()}
                    return status < 400, data, status
                    
            elif method.upper() == "POST":
                async with self.session.post(url, json=data, headers=request_headers) as response:
                    status = response.status
                    try:
                        response_data = await response.json()
                    except:
                        response_data = {"text": await response.text()}
                    return status < 400, response_data, status
                    
            else:
                return False, {"error": f"Unsupported method: {method}"}, 0
                
        except Exception as e:
            return False, {"error": str(e)}, 0
            
    async def test_agent_login(self) -> bool:
        """Teste 1: Login do Agente fabio21"""
        print("\n🔑 TESTE 1: Login do Agente")
        print("=" * 60)
        print(f"Credenciais: {self.agent_credentials['login']} / {self.agent_credentials['password']}")
        
        try:
            success, response, status = await self.make_request(
                "POST", 
                "/auth/agent/login",
                self.agent_credentials
            )
            
            print(f"📊 Status: {status}")
            print(f"📄 Response: {json.dumps(response, indent=2)}")
            
            if success and "token" in response:
                self.agent_token = response["token"]
                self.agent_id = response.get("user_data", {}).get("id")
                
                self.log_result(
                    "Agent Login", 
                    True, 
                    f"Login successful - Agent ID: {self.agent_id}",
                    {"token": self.agent_token[:50] + "...", "agent_id": self.agent_id}
                )
                print(f"✅ Login bem-sucedido!")
                print(f"   Agent ID: {self.agent_id}")
                print(f"   Token: {self.agent_token[:50]}...")
                return True
            else:
                self.log_result(
                    "Agent Login", 
                    False, 
                    f"Login failed - Status: {status}",
                    {"response": response}
                )
                print(f"❌ Login falhou: {response}")
                return False
                
        except Exception as e:
            self.log_result("Agent Login", False, f"Exception: {str(e)}")
            print(f"💥 ERRO no login do agente: {e}")
            return False
    
    async def test_client_login(self) -> bool:
        """Teste 2: Login do Cliente"""
        print("\n🔑 TESTE 2: Login do Cliente")
        print("=" * 60)
        print(f"Credenciais: {self.client_credentials['whatsapp']} / PIN {self.client_credentials['pin']}")
        
        try:
            success, response, status = await self.make_request(
                "POST", 
                "/auth/client/login",
                self.client_credentials
            )
            
            print(f"📊 Status: {status}")
            print(f"📄 Response: {json.dumps(response, indent=2)}")
            
            if success and "token" in response:
                self.client_token = response["token"]
                self.client_id = response.get("user_data", {}).get("id")
                
                self.log_result(
                    "Client Login", 
                    True, 
                    f"Login successful - Client ID: {self.client_id}",
                    {"token": self.client_token[:50] + "...", "client_id": self.client_id}
                )
                print(f"✅ Login bem-sucedido!")
                print(f"   Client ID: {self.client_id}")
                print(f"   Token: {self.client_token[:50]}...")
                return True
            else:
                self.log_result(
                    "Client Login", 
                    False, 
                    f"Login failed - Status: {status}",
                    {"response": response}
                )
                print(f"❌ Login falhou: {response}")
                return False
                
        except Exception as e:
            self.log_result("Client Login", False, f"Exception: {str(e)}")
            print(f"💥 ERRO no login do cliente: {e}")
            return False
    
    async def find_or_create_ticket(self) -> bool:
        """Encontrar ou criar um ticket para os testes"""
        print("\n🎫 PREPARAÇÃO: Encontrar/Criar Ticket")
        print("=" * 60)
        
        try:
            # Primeiro, tentar encontrar um ticket existente para o cliente
            tickets = await self.db.tickets.find({
                "client_id": self.client_id,
                "status": {"$in": ["open", "waiting"]}
            }).to_list(10)
            
            if tickets:
                self.ticket_id = tickets[0]["id"]
                print(f"✅ Ticket existente encontrado: {self.ticket_id}")
                return True
            
            # Se não encontrou, criar um novo ticket
            self.ticket_id = str(uuid.uuid4())
            
            new_ticket = {
                "id": self.ticket_id,
                "client_id": self.client_id,
                "client_name": "Cliente Teste",
                "status": "open",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "reseller_id": None  # Será definido pelo tenant middleware
            }
            
            await self.db.tickets.insert_one(new_ticket)
            print(f"✅ Novo ticket criado: {self.ticket_id}")
            return True
            
        except Exception as e:
            print(f"💥 ERRO ao preparar ticket: {e}")
            return False
    
    async def test_agent_send_message(self) -> bool:
        """Teste 3: Agente envia mensagem para cliente"""
        print("\n📤 TESTE 3: Agente → Cliente")
        print("=" * 60)
        
        if not self.agent_token or not self.ticket_id:
            self.log_result("Agent Send Message", False, "Missing agent token or ticket ID")
            print("❌ Token do agente ou ticket ID não disponível")
            return False
        
        message_data = {
            "from_type": "agent",
            "from_id": self.agent_id,
            "to_type": "client", 
            "to_id": self.client_credentials["whatsapp"],
            "ticket_id": self.ticket_id,
            "kind": "text",
            "text": "Teste de mensagem do agente para o cliente",
            "file_url": None
        }
        
        print(f"📋 Dados da mensagem:")
        print(json.dumps(message_data, indent=2))
        
        try:
            success, response, status = await self.make_request(
                "POST",
                "/messages",
                message_data,
                self.agent_token
            )
            
            print(f"📊 Status: {status}")
            print(f"📄 Response: {json.dumps(response, indent=2)}")
            
            if success and ("id" in response or "message_id" in response):
                message_id = response.get("id") or response.get("message_id")
                self.log_result(
                    "Agent Send Message", 
                    True, 
                    f"Message sent successfully - ID: {message_id}",
                    {"message_id": message_id, "status": status}
                )
                print(f"✅ Mensagem enviada com sucesso!")
                print(f"   Message ID: {message_id}")
                return True
            else:
                self.log_result(
                    "Agent Send Message", 
                    False, 
                    f"Failed to send message - Status: {status}",
                    {"response": response, "status": status}
                )
                print(f"❌ Falha ao enviar mensagem: {response}")
                return False
                
        except Exception as e:
            self.log_result("Agent Send Message", False, f"Exception: {str(e)}")
            print(f"💥 ERRO ao enviar mensagem do agente: {e}")
            return False
    
    async def test_client_send_message(self) -> bool:
        """Teste 4: Cliente envia mensagem para sistema"""
        print("\n📤 TESTE 4: Cliente → Sistema")
        print("=" * 60)
        
        if not self.client_token:
            self.log_result("Client Send Message", False, "Missing client token")
            print("❌ Token do cliente não disponível")
            return False
        
        message_data = {
            "from_type": "client",
            "from_id": self.client_credentials["whatsapp"],
            "to_type": "agent",
            "to_id": None,  # Sistema decide qual agente
            "kind": "text",
            "text": "Teste de mensagem do cliente para o sistema",
            "file_url": None
        }
        
        # Se temos ticket_id, incluir
        if self.ticket_id:
            message_data["ticket_id"] = self.ticket_id
        
        print(f"📋 Dados da mensagem:")
        print(json.dumps(message_data, indent=2))
        
        try:
            success, response, status = await self.make_request(
                "POST",
                "/messages",
                message_data,
                self.client_token
            )
            
            print(f"📊 Status: {status}")
            print(f"📄 Response: {json.dumps(response, indent=2)}")
            
            if success and ("id" in response or "message_id" in response):
                message_id = response.get("id") or response.get("message_id")
                self.log_result(
                    "Client Send Message", 
                    True, 
                    f"Message sent successfully - ID: {message_id}",
                    {"message_id": message_id, "status": status}
                )
                print(f"✅ Mensagem enviada com sucesso!")
                print(f"   Message ID: {message_id}")
                return True
            else:
                self.log_result(
                    "Client Send Message", 
                    False, 
                    f"Failed to send message - Status: {status}",
                    {"response": response, "status": status}
                )
                print(f"❌ Falha ao enviar mensagem: {response}")
                return False
                
        except Exception as e:
            self.log_result("Client Send Message", False, f"Exception: {str(e)}")
            print(f"💥 ERRO ao enviar mensagem do cliente: {e}")
            return False
    
    async def check_backend_logs(self):
        """Verificar logs do backend para erros"""
        print("\n📋 VERIFICAÇÃO DE LOGS DO BACKEND")
        print("=" * 60)
        
        try:
            # Verificar logs do supervisor
            result = subprocess.run(
                ["tail", "-n", "50", "/var/log/supervisor/backend.out.log"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logs = result.stdout
                print("📄 Últimas 50 linhas do log do backend:")
                print(logs)
                
                # Procurar por erros específicos
                error_patterns = [
                    "ObjectId is not JSON serializable",
                    "500 Internal Server Error",
                    "422 Unprocessable Entity", 
                    "400 Bad Request",
                    "Exception",
                    "Error",
                    "Failed"
                ]
                
                found_errors = []
                for pattern in error_patterns:
                    if pattern.lower() in logs.lower():
                        found_errors.append(pattern)
                
                if found_errors:
                    print(f"\n⚠️ Erros encontrados nos logs:")
                    for error in found_errors:
                        print(f"   - {error}")
                else:
                    print(f"\n✅ Nenhum erro crítico encontrado nos logs")
                    
            else:
                print("⚠️ Não foi possível acessar logs do backend")
                
            # Também verificar logs de erro
            result = subprocess.run(
                ["tail", "-n", "20", "/var/log/supervisor/backend.err.log"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                print("\n📄 Logs de erro do backend:")
                print(result.stdout)
                
        except Exception as e:
            print(f"⚠️ Erro ao verificar logs: {e}")
    
    async def verify_messages_in_database(self):
        """Verificar se as mensagens foram salvas no banco de dados"""
        print("\n🗄️ VERIFICAÇÃO NO BANCO DE DADOS")
        print("=" * 60)
        
        try:
            # Buscar mensagens relacionadas ao nosso teste
            messages = await self.db.messages.find({
                "$or": [
                    {"from_id": self.agent_id},
                    {"from_id": self.client_credentials["whatsapp"]},
                    {"ticket_id": self.ticket_id}
                ]
            }).sort("created_at", -1).limit(10).to_list(10)
            
            print(f"📊 Encontradas {len(messages)} mensagens relacionadas ao teste:")
            
            for i, msg in enumerate(messages, 1):
                print(f"\n   {i}. Message ID: {msg.get('id', 'N/A')}")
                print(f"      From: {msg.get('from_type', 'N/A')} ({msg.get('from_id', 'N/A')})")
                print(f"      Text: {msg.get('text', 'N/A')[:50]}...")
                print(f"      Ticket: {msg.get('ticket_id', 'N/A')}")
                print(f"      Created: {msg.get('created_at', 'N/A')}")
            
            if messages:
                print(f"\n✅ Mensagens foram salvas no banco de dados")
            else:
                print(f"\n⚠️ Nenhuma mensagem encontrada no banco de dados")
                
        except Exception as e:
            print(f"💥 ERRO ao verificar banco de dados: {e}")
    
    async def run_all_tests(self):
        """Executar todos os testes"""
        print("🚀 INICIANDO TESTE CRÍTICO: ENVIO E RECEBIMENTO DE MENSAGENS")
        print("=" * 80)
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print(f"🗄️ MongoDB: {MONGO_URL}")
        print(f"👤 Agente: {self.agent_credentials['login']} / {self.agent_credentials['password']}")
        print(f"📱 Cliente: {self.client_credentials['whatsapp']} / PIN {self.client_credentials['pin']}")
        
        try:
            await self.setup_session()
            
            # Executar testes em sequência
            test1_success = await self.test_agent_login()
            test2_success = await self.test_client_login()
            
            # Só continuar se os logins funcionaram
            if test1_success and test2_success:
                ticket_ready = await self.find_or_create_ticket()
                
                if ticket_ready:
                    test3_success = await self.test_agent_send_message()
                    test4_success = await self.test_client_send_message()
                else:
                    test3_success = False
                    test4_success = False
            else:
                test3_success = False
                test4_success = False
            
            # Verificações adicionais
            await self.check_backend_logs()
            await self.verify_messages_in_database()
            
            # Resumo final
            print("\n" + "=" * 80)
            print("📊 RESUMO FINAL DOS TESTES")
            print("=" * 80)
            
            total_tests = len(self.test_results)
            passed_tests = sum(1 for r in self.test_results if r["success"])
            
            print(f"📈 Total de testes: {total_tests}")
            print(f"✅ Testes passaram: {passed_tests}")
            print(f"❌ Testes falharam: {total_tests - passed_tests}")
            print(f"📊 Taxa de sucesso: {(passed_tests/total_tests)*100:.1f}%")
            
            print("\n📋 DETALHES DOS TESTES:")
            for i, result in enumerate(self.test_results, 1):
                status_icon = "✅" if result["success"] else "❌"
                print(f"{i}. {status_icon} {result['test']}")
                if result["message"]:
                    print(f"   {result['message']}")
                if not result["success"] and result["details"]:
                    print(f"   Detalhes: {result['details']}")
            
            # Análise específica do problema
            print("\n🎯 ANÁLISE DO PROBLEMA 'Erro ao enviar mensagem':")
            
            if test1_success:
                print("✅ Login do agente funcionando")
            else:
                print("❌ PROBLEMA: Login do agente falhando")
            
            if test2_success:
                print("✅ Login do cliente funcionando")
            else:
                print("❌ PROBLEMA: Login do cliente falhando")
            
            if test3_success:
                print("✅ Envio de mensagem do agente funcionando")
            else:
                print("❌ PROBLEMA: Envio de mensagem do agente falhando")
            
            if test4_success:
                print("✅ Envio de mensagem do cliente funcionando")
            else:
                print("❌ PROBLEMA: Envio de mensagem do cliente falhando")
            
            overall_success = all([test1_success, test2_success, test3_success, test4_success])
            
            if overall_success:
                print("\n🎉 RESULTADO FINAL: SISTEMA DE MENSAGENS 100% FUNCIONAL!")
                print("✅ Não foi possível reproduzir o erro 'Erro ao enviar mensagem'")
                print("💡 O problema pode estar no frontend ou em condições específicas")
            else:
                print("\n❌ RESULTADO FINAL: PROBLEMAS DETECTADOS NO SISTEMA DE MENSAGENS")
                print("🔍 Problemas identificados que podem causar 'Erro ao enviar mensagem':")
                
                failed_tests = [r for r in self.test_results if not r["success"]]
                for failed in failed_tests:
                    print(f"   - {failed['test']}: {failed['message']}")
            
            return overall_success
            
        except Exception as e:
            print(f"💥 ERRO CRÍTICO durante execução dos testes: {e}")
            return False
        finally:
            await self.cleanup_session()

async def main():
    """Função principal"""
    runner = MessageSendingTestRunner()
    success = await runner.run_all_tests()
    
    if success:
        print("\n🎯 CONCLUSÃO: Sistema de mensagens funcionando perfeitamente!")
        print("💡 Se o erro persiste no frontend, verificar:")
        print("   - Conexão WebSocket")
        print("   - Tratamento de erros no JavaScript")
        print("   - Headers de autenticação")
        print("   - Serialização de dados")
        exit(0)
    else:
        print("\n⚠️ CONCLUSÃO: Problemas detectados no sistema de mensagens!")
        print("🔧 Verificar logs acima para detalhes específicos")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())