#!/usr/bin/env python3
"""
TESTE COMPLETO DA INTEGRAÇÃO WHATSAPP COM EVOLUTION API v1.8.7
Conforme review request específico do usuário

CONTEXTO:
- Evolution API v1.8.7 rodando em: http://45.157.157.69:8080
- API Key: B4F8E9A2C5D7F1E3A9B6C8D2E5F7A1B3
- Backend CYBERTV já configurado e reiniciado
- QR Code sendo gerado com sucesso diretamente na Evolution API

TESTE:
1. Login como reseller: fabio@gmail.com / 102030ab
2. Criar conexão WhatsApp com limites específicos
3. Aguardar 30 segundos
4. Buscar QR Code
5. Verificar se a instância foi criada na Evolution API
"""

import asyncio
import httpx
import json
import time
from datetime import datetime

# Configurações
BACKEND_URL = "https://wppconnect-fix.preview.emergentagent.com"
EVOLUTION_API_URL = "http://45.157.157.69:8080"
EVOLUTION_API_KEY = "B4F8E9A2C5D7F1E3A9B6C8D2E5F7A1B3"

# Credenciais do teste
RESELLER_EMAIL = "fabio@gmail.com"
RESELLER_PASSWORD = "102030ab"

class EvolutionAPITester:
    def __init__(self):
        self.token = None
        self.reseller_id = None
        self.connection_id = None
        self.instance_name = None
        
    async def run_complete_test(self):
        """Executar teste completo conforme review request"""
        print("🚀 INICIANDO TESTE COMPLETO DA INTEGRAÇÃO WHATSAPP COM EVOLUTION API v1.8.7")
        print("=" * 80)
        
        try:
            # 1. Login como reseller
            await self.test_reseller_login()
            
            # 2. Criar conexão WhatsApp
            await self.test_create_whatsapp_connection()
            
            # 3. Aguardar 30 segundos
            await self.wait_30_seconds()
            
            # 4. Buscar QR Code
            await self.test_get_qr_code()
            
            # 5. Verificar se a instância foi criada na Evolution API
            await self.test_verify_evolution_instance()
            
            # Teste adicional: Verificar configurações WhatsApp
            await self.test_whatsapp_config()
            
            # Teste adicional: Verificar estatísticas
            await self.test_whatsapp_stats()
            
            print("\n🎉 TESTE COMPLETO FINALIZADO!")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ ERRO CRÍTICO NO TESTE: {e}")
            import traceback
            traceback.print_exc()
    
    async def test_reseller_login(self):
        """1. Login como reseller: fabio@gmail.com / 102030ab"""
        print("\n📋 TESTE 1: LOGIN COMO RESELLER")
        print("-" * 50)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/api/resellers/login",
                json={
                    "email": RESELLER_EMAIL,
                    "password": RESELLER_PASSWORD
                },
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                self.reseller_id = data.get("reseller_id")
                
                print(f"✅ LOGIN SUCESSO!")
                print(f"   Token: {self.token[:50]}...")
                print(f"   Reseller ID: {self.reseller_id}")
                
                if not self.token or not self.reseller_id:
                    raise Exception("Token ou Reseller ID não encontrados na resposta")
                    
            else:
                print(f"❌ FALHA NO LOGIN: {response.status_code}")
                print(f"   Resposta: {response.text}")
                raise Exception(f"Login falhou com status {response.status_code}")
    
    async def test_create_whatsapp_connection(self):
        """2. Criar conexão WhatsApp com limites específicos"""
        print("\n📋 TESTE 2: CRIAR CONEXÃO WHATSAPP")
        print("-" * 50)
        
        if not self.token or not self.reseller_id:
            raise Exception("Token ou Reseller ID não disponível")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/api/whatsapp/connections",
                json={
                    "reseller_id": self.reseller_id,
                    "max_received_daily": 200,
                    "max_sent_daily": 200
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.token}"
                }
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.connection_id = data.get("id")
                self.instance_name = data.get("instance_name")
                
                print(f"✅ CONEXÃO CRIADA COM SUCESSO!")
                print(f"   Connection ID: {self.connection_id}")
                print(f"   Instance Name: {self.instance_name}")
                print(f"   Status: {data.get('status')}")
                print(f"   Max Received Daily: {data.get('max_received_daily')}")
                print(f"   Max Sent Daily: {data.get('max_sent_daily')}")
                
                if not self.connection_id or not self.instance_name:
                    raise Exception("Connection ID ou Instance Name não encontrados")
                    
            else:
                print(f"❌ FALHA NA CRIAÇÃO: {response.status_code}")
                print(f"   Resposta: {response.text}")
                
                # Se for erro 503, pode ser que Evolution API não esteja disponível
                if response.status_code == 503:
                    print("⚠️  NOTA: Evolution API pode não estar disponível no momento")
                    print("   Isso é esperado se o servidor não estiver rodando")
                    return  # Continuar teste mesmo assim
                else:
                    raise Exception(f"Criação de conexão falhou com status {response.status_code}")
    
    async def wait_30_seconds(self):
        """3. Aguardar 30 segundos"""
        print("\n📋 TESTE 3: AGUARDAR 30 SEGUNDOS")
        print("-" * 50)
        
        print("⏱️  Aguardando 30 segundos para Evolution API processar...")
        for i in range(30, 0, -1):
            print(f"   {i} segundos restantes...", end="\r")
            await asyncio.sleep(1)
        
        print("\n✅ AGUARDO CONCLUÍDO!")
    
    async def test_get_qr_code(self):
        """4. Buscar QR Code"""
        print("\n📋 TESTE 4: BUSCAR QR CODE")
        print("-" * 50)
        
        if not self.token or not self.connection_id:
            print("⚠️  Token ou Connection ID não disponível, pulando teste")
            return
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BACKEND_URL}/api/whatsapp/connections/{self.connection_id}/qrcode",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                qr_code = data.get("qr_code")
                status = data.get("status")
                message = data.get("message")
                
                print(f"✅ QR CODE RESPONSE RECEBIDO!")
                print(f"   Status: {status}")
                print(f"   QR Code presente: {'Sim' if qr_code else 'Não'}")
                print(f"   Instance Name: {data.get('instance_name')}")
                print(f"   Expires In: {data.get('expires_in')} segundos")
                
                if message:
                    print(f"   Mensagem: {message}")
                
                if qr_code:
                    print(f"   QR Code (primeiros 100 chars): {qr_code[:100]}...")
                    print("✅ QR CODE OBTIDO COM SUCESSO!")
                else:
                    print("⚠️  QR Code ainda não disponível (normal se Evolution API não estiver rodando)")
                    
            else:
                print(f"❌ FALHA AO BUSCAR QR CODE: {response.status_code}")
                print(f"   Resposta: {response.text}")
    
    async def test_verify_evolution_instance(self):
        """5. Verificar se a instância foi criada na Evolution API"""
        print("\n📋 TESTE 5: VERIFICAR INSTÂNCIA NA EVOLUTION API")
        print("-" * 50)
        
        if not self.instance_name:
            print("⚠️  Instance Name não disponível, pulando teste")
            return
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Testar endpoint de status da instância
                response = await client.get(
                    f"{EVOLUTION_API_URL}/instance/connectionState/{self.instance_name}",
                    headers={"apikey": EVOLUTION_API_KEY}
                )
                
                print(f"Status da verificação: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ INSTÂNCIA ENCONTRADA NA EVOLUTION API!")
                    print(f"   Instance: {self.instance_name}")
                    print(f"   State: {data.get('state', 'unknown')}")
                    print(f"   Response: {json.dumps(data, indent=2)}")
                    
                elif response.status_code == 404:
                    print(f"❌ INSTÂNCIA NÃO ENCONTRADA NA EVOLUTION API")
                    print(f"   Instance: {self.instance_name}")
                    print("   Isso pode indicar que a criação falhou")
                    
                else:
                    print(f"⚠️  RESPOSTA INESPERADA: {response.status_code}")
                    print(f"   Resposta: {response.text}")
                    
        except httpx.TimeoutException:
            print("❌ TIMEOUT ao conectar com Evolution API")
            print("   Evolution API pode não estar disponível")
            
        except httpx.ConnectError:
            print("❌ ERRO DE CONEXÃO com Evolution API")
            print("   Verifique se Evolution API está rodando em http://45.157.157.69:8080")
            
        except Exception as e:
            print(f"❌ ERRO ao verificar instância: {e}")
    
    async def test_whatsapp_config(self):
        """Teste adicional: Verificar configurações WhatsApp"""
        print("\n📋 TESTE ADICIONAL: CONFIGURAÇÕES WHATSAPP")
        print("-" * 50)
        
        if not self.token:
            print("⚠️  Token não disponível, pulando teste")
            return
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BACKEND_URL}/api/whatsapp/config",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ CONFIGURAÇÕES OBTIDAS!")
                print(f"   Reseller ID: {data.get('reseller_id')}")
                print(f"   Plano: {data.get('plan')}")
                print(f"   Transfer Message: {data.get('transfer_message')}")
                print(f"   Enable Rotation: {data.get('enable_rotation')}")
                print(f"   Rotation Strategy: {data.get('rotation_strategy')}")
                
            else:
                print(f"❌ FALHA AO BUSCAR CONFIG: {response.status_code}")
                print(f"   Resposta: {response.text}")
    
    async def test_whatsapp_stats(self):
        """Teste adicional: Verificar estatísticas WhatsApp"""
        print("\n📋 TESTE ADICIONAL: ESTATÍSTICAS WHATSAPP")
        print("-" * 50)
        
        if not self.token:
            print("⚠️  Token não disponível, pulando teste")
            return
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BACKEND_URL}/api/whatsapp/stats",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ ESTATÍSTICAS OBTIDAS!")
                print(f"   Total Connections: {data.get('total_connections')}")
                print(f"   Active Connections: {data.get('active_connections')}")
                print(f"   Total Received Today: {data.get('total_received_today')}")
                print(f"   Total Sent Today: {data.get('total_sent_today')}")
                
                plan_info = data.get('plan', {})
                if plan_info:
                    print(f"   Plano: {plan_info.get('name')} (max: {plan_info.get('max_numbers')} números)")
                
            else:
                print(f"❌ FALHA AO BUSCAR STATS: {response.status_code}")
                print(f"   Resposta: {response.text}")

async def main():
    """Função principal"""
    print("🔥 TESTE COMPLETO DA INTEGRAÇÃO WHATSAPP EVOLUTION API v1.8.7")
    print("Conforme review request específico do usuário")
    print(f"Backend: {BACKEND_URL}")
    print(f"Evolution API: {EVOLUTION_API_URL}")
    print(f"Credenciais: {RESELLER_EMAIL} / {RESELLER_PASSWORD}")
    print("=" * 80)
    
    tester = EvolutionAPITester()
    await tester.run_complete_test()

if __name__ == "__main__":
    asyncio.run(main())