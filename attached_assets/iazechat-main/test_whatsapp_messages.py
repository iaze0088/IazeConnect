#!/usr/bin/env python3
"""
Script para buscar mensagens diretamente do servidor WPPConnect
Útil quando webhooks não estão funcionando
"""
import asyncio
import httpx
from motor.motor_asyncio import AsyncIOMotorClient

WPPCONNECT_URL = "http://95.217.178.51:21465"

async def fetch_messages(instance_name):
    """Buscar mensagens novas da instância"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{WPPCONNECT_URL}/api/{instance_name}/all-chats-new-messages",
                headers={"Accept": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Resposta recebida: {len(data.get('response', {}).get('messages', []))} mensagens")
                return data.get('response', {}).get('messages', [])
            else:
                print(f"❌ Erro: Status {response.status_code}")
                return []
                
    except Exception as e:
        print(f"❌ Erro ao buscar mensagens: {e}")
        return []

async def main():
    # Buscar conexão ativa
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['support_chat']
    
    conn = await db.whatsapp_connections.find_one({'instance_name': 'fabio_1_1761480481'})
    
    if not conn:
        print("❌ Conexão não encontrada")
        return
    
    print(f"🔍 Buscando mensagens para: {conn['instance_name']}")
    print(f"📱 Número: {conn.get('phone_number')}")
    print("")
    
    messages = await fetch_messages(conn['instance_name'])
    
    if messages:
        print(f"📨 {len(messages)} mensagens encontradas:")
        for msg in messages[:5]:  # Mostrar apenas primeiras 5
            print(f"  - De: {msg.get('from', 'N/A')}")
            print(f"    Texto: {msg.get('body', 'N/A')[:50]}...")
            print("")
    else:
        print("⚠️  Nenhuma mensagem nova encontrada")

if __name__ == "__main__":
    asyncio.run(main())
