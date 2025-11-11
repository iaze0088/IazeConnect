#!/usr/bin/env python3
"""
Script para atualizar manualmente o status de uma conexão WhatsApp
Útil quando a conexão foi feita mas o webhook não atualizou o status
"""

import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

async def update_connection_status(instance_name=None, phone_number=None):
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['support_chat']
    
    # Buscar conexão
    if instance_name:
        query = {'instance_name': instance_name}
    elif phone_number:
        query = {'phone_number': phone_number}
    else:
        # Buscar todas as conexões "connecting"
        query = {'status': 'connecting'}
    
    connections = await db.whatsapp_connections.find(query).to_list(length=100)
    
    if not connections:
        print("❌ Nenhuma conexão encontrada")
        return
    
    print(f"\n📱 Encontradas {len(connections)} conexões")
    
    for conn in connections:
        print(f"\n{'='*50}")
        print(f"Instance: {conn.get('instance_name')}")
        print(f"Status atual: {conn.get('status')}")
        print(f"Connected: {conn.get('connected')}")
        print(f"Phone: {conn.get('phone_number')}")
        
        # Perguntar se quer atualizar
        response = input(f"\n✅ Marcar como CONECTADO? (s/n): ")
        
        if response.lower() == 's':
            # Pedir número de telefone se não tiver
            if not conn.get('phone_number'):
                phone = input("📞 Digite o número de telefone (com DDI, ex: 5511999999999): ")
            else:
                phone = conn.get('phone_number')
            
            # Atualizar
            await db.whatsapp_connections.update_one(
                {'id': conn['id']},
                {'$set': {
                    'status': 'connected',
                    'connected': True,
                    'phone_number': phone,
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }}
            )
            
            print(f"✅ Conexão atualizada!")
            print(f"   Status: connected")
            print(f"   Phone: {phone}")
        else:
            print("⏭️  Pulando...")

async def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.startswith('55'):  # Número de telefone
            await update_connection_status(phone_number=arg)
        else:  # Instance name
            await update_connection_status(instance_name=arg)
    else:
        # Buscar todas pendentes
        await update_connection_status()

if __name__ == "__main__":
    print("🔧 WhatsApp Connection Status Updater")
    print("="*50)
    asyncio.run(main())
