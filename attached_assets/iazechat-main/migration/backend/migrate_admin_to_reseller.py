"""
Script para migrar dados do Admin Master para o Reseller Principal
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'support_chat')

async def migrate_data():
    """Migrar todos os dados do admin master para o reseller principal"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    reseller_id = "1c2a3bc0-535b-4e77-bda7-04108e6bce5c"  # Reseller suporte.help
    
    print("🔄 MIGRANDO DADOS DO ADMIN MASTER PARA RESELLER PRINCIPAL...\n")
    print("="*80)
    
    # 1. Migrar clientes
    result = await db.users.update_many(
        {"user_type": "client", "$or": [{"reseller_id": None}, {"reseller_id": {"$exists": False}}]},
        {"$set": {"reseller_id": reseller_id}}
    )
    print(f"👤 CLIENTES migrados: {result.modified_count}")
    
    # 2. Migrar atendentes
    result = await db.users.update_many(
        {"user_type": "agent", "$or": [{"reseller_id": None}, {"reseller_id": {"$exists": False}}]},
        {"$set": {"reseller_id": reseller_id}}
    )
    print(f"👥 ATENDENTES migrados: {result.modified_count}")
    
    # 3. Migrar tickets
    result = await db.tickets.update_many(
        {"$or": [{"reseller_id": None}, {"reseller_id": {"$exists": False}}]},
        {"$set": {"reseller_id": reseller_id}}
    )
    print(f"🎫 TICKETS migrados: {result.modified_count}")
    
    # 4. Migrar AI Agents
    result = await db.ai_agents.update_many(
        {"$or": [{"reseller_id": None}, {"reseller_id": {"$exists": False}}]},
        {"$set": {"reseller_id": reseller_id}}
    )
    print(f"🤖 AI AGENTS migrados: {result.modified_count}")
    
    # 5. Migrar departamentos
    result = await db.departments.update_many(
        {"$or": [{"reseller_id": None}, {"reseller_id": {"$exists": False}}]},
        {"$set": {"reseller_id": reseller_id}}
    )
    print(f"🏢 DEPARTAMENTOS migrados: {result.modified_count}")
    
    # 6. Migrar WhatsApp instances
    result = await db.whatsapp_instances.update_many(
        {"$or": [{"reseller_id": None}, {"reseller_id": {"$exists": False}}]},
        {"$set": {"reseller_id": reseller_id}}
    )
    print(f"📱 WHATSAPP INSTANCES migradas: {result.modified_count}")
    
    # 7. Migrar avisos/notices
    result = await db.notices.update_many(
        {"$or": [{"reseller_id": None}, {"reseller_id": {"$exists": False}}]},
        {"$set": {"reseller_id": reseller_id}}
    )
    print(f"📢 AVISOS migrados: {result.modified_count}")
    
    # 8. Migrar configuração de vendas (se existir)
    result = await db.vendas_simple_config.update_many(
        {"$or": [{"reseller_id": None}, {"reseller_id": {"$exists": False}}]},
        {"$set": {"reseller_id": reseller_id}}
    )
    print(f"💰 VENDAS CONFIG migradas: {result.modified_count}")
    
    print("\n" + "="*80)
    print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print(f"\n📋 Todos os dados agora pertencem ao reseller:")
    print(f"   ID: {reseller_id}")
    print(f"   Nome: suporte")
    print(f"   Domínio: suporte.help")
    print(f"\n🎯 Próximo passo: Configurar IA para /vendas no painel do reseller")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(migrate_data())
