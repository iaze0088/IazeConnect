#!/usr/bin/env python3
"""
Script para configurar webhooks da Evolution API automaticamente
"""
import asyncio
import httpx
import os
from motor.motor_asyncio import AsyncIOMotorClient

# Configurações
EVOLUTION_API_URL = os.environ.get('EVOLUTION_API_URL', 'http://45.157.157.69:8080')
EVOLUTION_API_KEY = os.environ.get('EVOLUTION_API_KEY', 'B4F8E9A2C5D7F1E3A9B6C8D2E5F7A1B3')
BACKEND_URL = "https://wppconnect-fix.preview.emergentagent.com"
WEBHOOK_URL = f"{BACKEND_URL}/api/whatsapp/webhook/evolution"
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')

print("=" * 80)
print("🔧 CONFIGURAÇÃO DE WEBHOOKS - EVOLUTION API")
print("=" * 80)
print(f"Evolution API: {EVOLUTION_API_URL}")
print(f"Webhook URL: {WEBHOOK_URL}")
print("=" * 80)

async def configure_webhooks():
    """Configurar webhooks para todas as instâncias"""
    
    # Conectar ao MongoDB
    print("\n📊 Conectando ao MongoDB...")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.support_chat
    
    # Buscar todas as conexões WhatsApp
    print("🔍 Buscando conexões WhatsApp no banco de dados...")
    connections = await db.whatsapp_connections.find({}, {"_id": 0}).to_list(length=100)
    
    print(f"✅ Encontradas {len(connections)} conexões\n")
    
    if not connections:
        print("⚠️ Nenhuma conexão WhatsApp encontrada no banco!")
        return
    
    # Configurar webhook para cada instância
    async with httpx.AsyncClient(timeout=30.0) as http_client:
        for conn in connections:
            instance_name = conn.get("instance_name")
            if not instance_name:
                print(f"⚠️ Conexão sem instance_name: {conn.get('id')}")
                continue
            
            print(f"\n{'='*60}")
            print(f"📱 Configurando webhook para: {instance_name}")
            print(f"{'='*60}")
            
            # Configurar webhook global
            webhook_config = {
                "enabled": True,
                "url": WEBHOOK_URL,
                "webhookByEvents": True,
                "events": [
                    "MESSAGES_UPSERT",
                    "MESSAGES_UPDATE", 
                    "CONNECTION_UPDATE",
                    "QRCODE_UPDATED"
                ]
            }
            
            try:
                # Endpoint correto para v1.8.7
                response = await http_client.post(
                    f"{EVOLUTION_API_URL}/webhook/set/{instance_name}",
                    json=webhook_config,
                    headers={
                        "Content-Type": "application/json",
                        "apikey": EVOLUTION_API_KEY
                    }
                )
                
                print(f"📤 Status Code: {response.status_code}")
                
                if response.status_code in [200, 201]:
                    print(f"✅ Webhook configurado com sucesso!")
                    print(f"   URL: {WEBHOOK_URL}")
                    print(f"   Eventos: {webhook_config['events']}")
                    
                    # Verificar configuração
                    verify_response = await http_client.get(
                        f"{EVOLUTION_API_URL}/webhook/find/{instance_name}",
                        headers={"apikey": EVOLUTION_API_KEY}
                    )
                    
                    if verify_response.status_code == 200:
                        webhook_info = verify_response.json()
                        print(f"\n🔍 Verificação:")
                        print(f"   Enabled: {webhook_info.get('enabled')}")
                        print(f"   URL: {webhook_info.get('url')}")
                else:
                    print(f"❌ Erro ao configurar webhook: {response.status_code}")
                    print(f"   Response: {response.text}")
                    
            except Exception as e:
                print(f"❌ Exceção ao configurar webhook: {e}")
                import traceback
                traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("🎉 CONFIGURAÇÃO CONCLUÍDA!")
    print("=" * 80)
    print("\n📋 Próximos passos:")
    print("1. Envie uma mensagem para o número WhatsApp conectado")
    print("2. Verifique os logs: tail -f /var/log/supervisor/backend.out.log")
    print("3. A mensagem deve aparecer no dashboard do agente")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(configure_webhooks())
