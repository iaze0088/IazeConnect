"""
Script de otimização: Criar índices MongoDB para melhorar performance
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'support_chat')

async def create_index_safe(collection, index_spec, **kwargs):
    """Criar índice com tratamento de erros"""
    try:
        await collection.create_index(index_spec, **kwargs)
        return True
    except Exception as e:
        # Silenciar erros de índices já existentes
        if "already exists" in str(e) or "Index with name" in str(e) or "same name" in str(e):
            return False
        # Reportar outros erros mas continuar
        print(f"  ⚠️  Erro ao criar índice {index_spec}: {str(e)[:80]}")
        return False

async def create_indexes():
    """Criar índices nas collections principais"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("🔍 Criando índices MongoDB...")
    print("=" * 50)
    
    # 1. TICKETS - Queries mais comuns
    print("\n📋 Tickets...")
    created = 0
    created += await create_index_safe(db.tickets, [("status", 1)])
    created += await create_index_safe(db.tickets, [("client_id", 1)])
    created += await create_index_safe(db.tickets, [("agent_id", 1)])
    created += await create_index_safe(db.tickets, [("reseller_id", 1)])
    created += await create_index_safe(db.tickets, [("created_at", -1)])
    created += await create_index_safe(db.tickets, [("status", 1), ("reseller_id", 1)])
    created += await create_index_safe(db.tickets, [("agent_id", 1), ("status", 1)])
    print(f"✅ {created} novos índices criados")
    
    # 2. MESSAGES - Busca por ticket e ordenação por timestamp
    print("\n💬 Messages...")
    created = 0
    created += await create_index_safe(db.messages, [("ticket_id", 1)])
    created += await create_index_safe(db.messages, [("timestamp", -1)])
    created += await create_index_safe(db.messages, [("from_id", 1)])
    created += await create_index_safe(db.messages, [("to_id", 1)])
    created += await create_index_safe(db.messages, [("ticket_id", 1), ("timestamp", -1)])
    print(f"✅ {created} novos índices criados")
    
    # 3. USERS - Login e busca por revenda
    print("\n👥 Users...")
    created = 0
    created += await create_index_safe(db.users, [("email", 1)], unique=True)
    created += await create_index_safe(db.users, [("whatsapp", 1)])
    created += await create_index_safe(db.users, [("reseller_id", 1)])
    created += await create_index_safe(db.users, [("user_type", 1)])
    created += await create_index_safe(db.users, [("reseller_id", 1), ("user_type", 1)])
    print(f"✅ {created} novos índices criados")
    
    # 4. AGENTS - Login e status
    print("\n🎧 Agents...")
    created = 0
    created += await create_index_safe(db.agents, [("email", 1)], unique=True)
    created += await create_index_safe(db.agents, [("reseller_id", 1)])
    created += await create_index_safe(db.agents, [("status", 1)])
    created += await create_index_safe(db.agents, [("reseller_id", 1), ("status", 1)])
    print(f"✅ {created} novos índices criados")
    
    # 5. RESELLERS - Login e domínio
    print("\n🏢 Resellers...")
    created = 0
    created += await create_index_safe(db.resellers, [("email", 1)], unique=True)
    created += await create_index_safe(db.resellers, [("custom_domain", 1)])
    created += await create_index_safe(db.resellers, [("parent_id", 1)])
    print(f"✅ {created} novos índices criados")
    
    # 6. WHATSAPP INSTANCES - Busca rápida
    print("\n📱 WhatsApp Instances...")
    created = 0
    created += await create_index_safe(db.whatsapp_instances, [("instance_name", 1)])
    created += await create_index_safe(db.whatsapp_instances, [("reseller_id", 1)])
    created += await create_index_safe(db.whatsapp_instances, [("status", 1)])
    created += await create_index_safe(db.whatsapp_instances, [("reseller_id", 1), ("status", 1)])
    print(f"✅ {created} novos índices criados")
    
    # 7. AI AGENTS - Busca por revenda e status
    print("\n🤖 AI Agents...")
    created = 0
    created += await create_index_safe(db.ai_agents, [("reseller_id", 1)])
    created += await create_index_safe(db.ai_agents, [("enabled", 1)])
    created += await create_index_safe(db.ai_agents, [("reseller_id", 1), ("enabled", 1)])
    print(f"✅ {created} novos índices criados")
    
    # 8. VENDAS (novo sistema)
    print("\n💰 Vendas...")
    created = 0
    created += await create_index_safe(db.vendas_sessions, [("session_id", 1)], unique=True)
    created += await create_index_safe(db.vendas_messages, [("session_id", 1)])
    created += await create_index_safe(db.vendas_messages, [("timestamp", -1)])
    created += await create_index_safe(db.vendas_simple_config, [("is_active", 1)])
    print(f"✅ {created} novos índices criados")
    
    # 9. SUBSCRIPTIONS - Pagamentos
    print("\n💳 Subscriptions...")
    created = 0
    created += await create_index_safe(db.subscriptions, [("reseller_id", 1)])
    created += await create_index_safe(db.subscriptions, [("status", 1)])
    created += await create_index_safe(db.subscriptions, [("end_date", 1)])
    created += await create_index_safe(db.subscriptions, [("reseller_id", 1), ("status", 1)])
    print(f"✅ {created} novos índices criados")
    
    print("\n" + "=" * 50)
    print("✅ OTIMIZAÇÃO CONCLUÍDA!")
    print(f"⚡ Queries devem ser mais rápidas!")
    
    # Listar todos os índices criados
    print("\n📋 Verificando índices...")
    collections = ['tickets', 'messages', 'users', 'agents', 'resellers', 
                   'whatsapp_instances', 'ai_agents', 'vendas_sessions']
    
    for coll_name in collections:
        try:
            indexes = await db[coll_name].index_information()
            print(f"  {coll_name}: {len(indexes)} índices totais")
        except Exception as e:
            print(f"  {coll_name}: Erro ao verificar índices")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_indexes())
