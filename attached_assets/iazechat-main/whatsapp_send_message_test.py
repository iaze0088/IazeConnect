#!/usr/bin/env python3
"""
TESTE ESPECÍFICO: Endpoint de Envio de Mensagem do Atendente

**Problema Reportado:**
- Painel do atendente mostra "Erro ao enviar mensagem"
- Número: +55 51 99351-3841
- IA está ativa mas atendente não consegue enviar mensagem manual

**Endpoint a Testar:**
POST /api/whatsapp/send-message

**Teste Necessário:**
1. Fazer login como atendente
2. Tentar enviar mensagem para o número +55 51 99351-3841
3. Capturar o erro exato retornado
4. Verificar logs do Evolution API
5. Verificar se instância WhatsApp está conectada
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import subprocess

# Configurações
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://wppconnect-fix.preview.emergentagent.com')
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'support_chat')

# Dados do teste conforme review request
TEST_NUMBER = "+55 51 99351-3841"
TEST_NUMBER_CLEAN = "5551993513841"
TEST_MESSAGE = "Teste de mensagem"

class WhatsAppSendMessageTester:
    def __init__(self):
        self.client = AsyncIOMotorClient(MONGO_URL)
        self.db = self.client[DB_NAME]
        self.session = None
        self.agent_token = None
        self.test_results = []
        
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
        
    async def find_active_agent(self):
        """Encontrar um agente ativo no sistema para fazer login"""
        print("🔍 Procurando agente ativo no sistema...")
        
        # Buscar agentes ativos na collection users
        agents = await self.db.users.find({
            "user_type": "agent",
            "is_active": {"$ne": False}
        }).to_list(10)
        
        print(f"   📊 Encontrados {len(agents)} agentes no sistema")
        
        for agent in agents:
            username = agent.get("username")
            name = agent.get("name", "N/A")
            reseller_id = agent.get("reseller_id", "N/A")
            print(f"   👤 Agent: {username} ({name}) - Reseller: {reseller_id}")
            
        # Tentar alguns agentes conhecidos
        test_agents = [
            {"username": "fabio123", "password": "fabio123"},
            {"username": "fabioteste", "password": "123"},
            {"username": "admin", "password": "admin123"},
            {"username": "agente1", "password": "123456"},
        ]
        
        for test_agent in test_agents:
            try:
                async with self.session.post(
                    f"{BACKEND_URL}/api/auth/agent/login",
                    json={
                        "login": test_agent["username"],
                        "password": test_agent["password"]
                    },
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        token = data.get("token")
                        if token:
                            print(f"   ✅ Login bem-sucedido: {test_agent['username']}")
                            return token, test_agent["username"]
                    else:
                        print(f"   ❌ Login falhou para {test_agent['username']}: {response.status}")
                        
            except Exception as e:
                print(f"   ❌ Erro ao tentar login {test_agent['username']}: {e}")
                
        return None, None
        
    async def test_agent_login(self):
        """Teste 1: Fazer login como atendente"""
        print("\n🔑 TESTE 1: Login do Atendente")
        print("=" * 60)
        
        try:
            token, username = await self.find_active_agent()
            
            if token:
                self.agent_token = token
                self.log_result("Agent Login", True, f"Login bem-sucedido: {username}")
                return True
            else:
                self.log_result("Agent Login", False, "Nenhum agente conseguiu fazer login")
                return False
                
        except Exception as e:
            self.log_result("Agent Login", False, f"Erro durante login: {e}")
            return False
    
    async def check_whatsapp_instances(self):
        """Teste 2: Verificar instâncias WhatsApp disponíveis"""
        print("\n📱 TESTE 2: Verificar Instâncias WhatsApp")
        print("=" * 60)
        
        if not self.agent_token:
            self.log_result("WhatsApp Instances", False, "Token de agente necessário")
            return False
            
        try:
            # Tentar buscar instâncias WhatsApp
            async with self.session.get(
                f"{BACKEND_URL}/api/whatsapp/instances",
                headers={"Authorization": f"Bearer {self.agent_token}"}
            ) as response:
                
                status = response.status
                
                try:
                    data = await response.json()
                except:
                    data = {"detail": await response.text()}
                
                print(f"📊 Status: {status}")
                print(f"📄 Response: {json.dumps(data, indent=2)}")
                
                if status == 200 and isinstance(data, list):
                    instance_count = len(data)
                    print(f"   📱 Instâncias encontradas: {instance_count}")
                    
                    if instance_count > 0:
                        for i, instance in enumerate(data):
                            instance_name = instance.get("instance_name", "N/A")
                            status_conn = instance.get("status", "N/A")
                            print(f"   {i+1}. {instance_name} - Status: {status_conn}")
                        
                        self.log_result("WhatsApp Instances", True, f"{instance_count} instâncias encontradas", {"instances": data})
                        return data[0].get("instance_name")  # Retornar primeira instância
                    else:
                        self.log_result("WhatsApp Instances", False, "Nenhuma instância WhatsApp configurada")
                        return None
                else:
                    self.log_result("WhatsApp Instances", False, f"Erro ao buscar instâncias: {data}")
                    return None
                    
        except Exception as e:
            self.log_result("WhatsApp Instances", False, f"Erro na requisição: {e}")
            return None
    
    async def test_send_message_endpoint(self, instance_name: str = None):
        """Teste 3: Testar endpoint de envio de mensagem"""
        print("\n📤 TESTE 3: Endpoint de Envio de Mensagem")
        print("=" * 60)
        
        if not self.agent_token:
            self.log_result("Send Message Endpoint", False, "Token de agente necessário")
            return False
            
        # Se não temos instância, usar uma padrão
        if not instance_name:
            instance_name = "nome-da-instancia"  # Conforme dados do review request
            
        # Dados do teste conforme review request
        test_data = {
            "instance_name": instance_name,
            "number": TEST_NUMBER_CLEAN,
            "text": TEST_MESSAGE
        }
        
        print(f"📋 Dados do teste:")
        print(f"   Instance: {instance_name}")
        print(f"   Número: {TEST_NUMBER} → {TEST_NUMBER_CLEAN}")
        print(f"   Mensagem: {TEST_MESSAGE}")
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/api/whatsapp/send-message",
                json=test_data,
                headers={
                    "Authorization": f"Bearer {self.agent_token}",
                    "Content-Type": "application/json"
                }
            ) as response:
                
                status = response.status
                headers = dict(response.headers)
                
                try:
                    data = await response.json()
                except:
                    data = {"detail": await response.text()}
                
                print(f"📊 Status: {status}")
                print(f"📋 Headers: {json.dumps(headers, indent=2)}")
                print(f"📄 Response: {json.dumps(data, indent=2)}")
                
                # Analisar resposta
                if status == 200:
                    success = data.get("success", False)
                    if success:
                        self.log_result("Send Message Endpoint", True, "Mensagem enviada com sucesso", data)
                        return True
                    else:
                        error = data.get("error", "Erro desconhecido")
                        self.log_result("Send Message Endpoint", False, f"API retornou erro: {error}", data)
                        return False
                else:
                    error_detail = data.get("detail", data)
                    self.log_result("Send Message Endpoint", False, f"HTTP {status}: {error_detail}", data)
                    return False
                    
        except Exception as e:
            self.log_result("Send Message Endpoint", False, f"Erro na requisição: {e}")
            return False
    
    async def check_evolution_api_health(self):
        """Teste 4: Verificar saúde da Evolution API"""
        print("\n🏥 TESTE 4: Saúde da Evolution API")
        print("=" * 60)
        
        evolution_url = os.environ.get('EVOLUTION_API_URL', 'http://evolution.suporte.help:8080')
        evolution_key = os.environ.get('EVOLUTION_API_KEY', 'iaze-evolution-2025-secure-key')
        
        print(f"🌐 Evolution API URL: {evolution_url}")
        print(f"🔑 Evolution API Key: {evolution_key[:20]}...")
        
        try:
            # Testar endpoint de health da Evolution API
            async with self.session.get(
                f"{evolution_url}/",
                headers={"apikey": evolution_key},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                
                status = response.status
                
                try:
                    data = await response.json()
                except:
                    data = {"text": await response.text()}
                
                print(f"📊 Status: {status}")
                print(f"📄 Response: {json.dumps(data, indent=2)}")
                
                if status == 200:
                    self.log_result("Evolution API Health", True, "Evolution API está online", data)
                    return True
                else:
                    self.log_result("Evolution API Health", False, f"Evolution API retornou {status}", data)
                    return False
                    
        except asyncio.TimeoutError:
            self.log_result("Evolution API Health", False, "Timeout ao conectar com Evolution API")
            return False
        except Exception as e:
            self.log_result("Evolution API Health", False, f"Erro ao conectar: {e}")
            return False
    
    async def check_backend_logs(self):
        """Teste 5: Verificar logs do backend"""
        print("\n📋 TESTE 5: Logs do Backend")
        print("=" * 60)
        
        try:
            # Verificar logs do supervisor backend
            result = subprocess.run(
                ["tail", "-n", "50", "/var/log/supervisor/backend.out.log"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logs = result.stdout
                print("📄 Últimas 50 linhas do log do backend:")
                print("-" * 40)
                print(logs)
                print("-" * 40)
                
                # Procurar por erros relacionados ao WhatsApp
                whatsapp_errors = []
                for line in logs.split('\n'):
                    if any(keyword in line.lower() for keyword in ['whatsapp', 'evolution', 'send', 'message', 'error']):
                        whatsapp_errors.append(line)
                
                if whatsapp_errors:
                    print("🔍 Linhas relacionadas ao WhatsApp:")
                    for error in whatsapp_errors[-10:]:  # Últimas 10
                        print(f"   {error}")
                
                self.log_result("Backend Logs", True, f"Logs acessados - {len(whatsapp_errors)} linhas relacionadas ao WhatsApp")
                return True
            else:
                self.log_result("Backend Logs", False, f"Erro ao acessar logs: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_result("Backend Logs", False, f"Erro ao verificar logs: {e}")
            return False
    
    async def run_all_tests(self):
        """Executar todos os testes"""
        print("🚀 INICIANDO TESTE ESPECÍFICO: Endpoint de Envio de Mensagem do Atendente")
        print("=" * 80)
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print(f"📱 Número de teste: {TEST_NUMBER}")
        print(f"💬 Mensagem de teste: {TEST_MESSAGE}")
        print("=" * 80)
        
        try:
            await self.setup_session()
            
            # Executar testes em sequência
            print("\n🔄 Executando testes...")
            
            # 1. Login do agente
            login_success = await self.test_agent_login()
            
            # 2. Verificar instâncias WhatsApp
            instance_name = None
            if login_success:
                instance_name = await self.check_whatsapp_instances()
            
            # 3. Testar endpoint de envio
            send_success = False
            if login_success:
                send_success = await self.test_send_message_endpoint(instance_name)
            
            # 4. Verificar saúde da Evolution API
            evolution_health = await self.check_evolution_api_health()
            
            # 5. Verificar logs do backend
            logs_success = await self.check_backend_logs()
            
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
                print(f"{i}. {status_icon} {result['test']}: {result['message']}")
            
            # Diagnóstico específico do problema
            print("\n🔍 DIAGNÓSTICO DO PROBLEMA:")
            
            if not login_success:
                print("❌ PROBLEMA CRÍTICO: Não foi possível fazer login como agente")
                print("   - Verificar credenciais dos agentes")
                print("   - Verificar se há agentes ativos no sistema")
                
            elif not send_success:
                print("❌ PROBLEMA IDENTIFICADO: Endpoint de envio de mensagem falhou")
                print("   - Verificar configuração da Evolution API")
                print("   - Verificar se instância WhatsApp está conectada")
                print("   - Verificar logs do backend para erro específico")
                
                if not evolution_health:
                    print("   - Evolution API não está respondendo")
                    print("   - Verificar se servidor Evolution está online")
                    print("   - Verificar configuração de rede/firewall")
                
            else:
                print("✅ TESTES PASSARAM: Endpoint de envio funcionando")
                print("   - O problema pode ser específico do frontend")
                print("   - Verificar console do navegador para erros JavaScript")
                
            return send_success
            
        except Exception as e:
            print(f"💥 ERRO CRÍTICO durante execução dos testes: {e}")
            return False
        finally:
            await self.cleanup_session()

async def main():
    """Função principal"""
    tester = WhatsAppSendMessageTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎯 CONCLUSÃO: Endpoint de envio de mensagem funcionando!")
        exit(0)
    else:
        print("\n⚠️ CONCLUSÃO: Problema identificado no endpoint de envio!")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())