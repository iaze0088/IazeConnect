#!/usr/bin/env python3
"""
CORREÇÃO DEFINITIVA: Criar agente na collection CORRETA (agents, não users)
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone

async def fix_agent_in_correct_collection():
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
    db = client.support_chat
    
    print("=" * 80)
    print("🔧 CORREÇÃO CRÍTICA: Criando agente na collection AGENTS")
    print("=" * 80)
    
    # ID do agente que foi criado
    agent_id = 'bff14c70-56bd-4b9f-9c1b-4a745fa57687'
    reseller_id = '49376e6f-4122-4fcf-88ab-97965c472711'
    dept_id = 'd525463d-0691-4525-aee1-5a74fc0a69a0'
    
    # Verificar se já existe na collection agents
    existing_agent = await db.agents.find_one({'id': agent_id}, {'_id': 0})
    
    if existing_agent:
        print(f"✅ Agente já existe na collection agents")
    else:
        print(f"⚠️ Criando agente na collection AGENTS (não users!)")
        
        # Criar na collection agents
        agent = {
            'id': agent_id,
            'reseller_id': reseller_id,
            'username': 'fabio321',
            'name': 'Fabio 321',
            'email': f'fabio321@{reseller_id}.temp',
            'department_ids': [dept_id],
            'is_active': True,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        await db.agents.insert_one(agent)
        print(f"✅ Agente criado na collection AGENTS!")
    
    # Verificar collections
    print(f"\n📊 VERIFICAÇÃO:")
    
    # Collection agents
    agents = await db.agents.find({'id': agent_id}, {'_id': 0}).to_list(length=10)
    print(f"   Agents collection: {len(agents)} registros")
    if agents:
        for a in agents:
            print(f"      - ID: {a['id']}, Username: {a.get('username')}, Depts: {a.get('department_ids')}")
    
    # Collection users
    users = await db.users.find({'id': agent_id}, {'_id': 0}).to_list(length=10)
    print(f"   Users collection: {len(users)} registros")
    if users:
        for u in users:
            print(f"      - ID: {u['id']}, Username: {u.get('username')}, Type: {u.get('user_type')}")
    
    # Verificar tickets
    tickets = await db.tickets.find({'department_id': dept_id, 'status': 'open'}, {'_id': 0}).to_list(length=100)
    print(f"\n   Tickets disponíveis: {len(tickets)}")
    
    print("\n" + "=" * 80)
    print("🎉 CORREÇÃO APLICADA!")
    print("=" * 80)
    print("\nAgora faça LOGIN novamente com:")
    print("   Username: fabio321")
    print("   Password: fabio321")
    print("\nOs tickets DEVEM aparecer!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(fix_agent_in_correct_collection())
