#!/usr/bin/env python3
"""
SOLUÇÃO DEFINITIVA: Criar agente e garantir visibilidade de tickets
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
from datetime import datetime, timezone

async def fix_agent_and_tickets():
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
    db = client.support_chat
    
    print("=" * 80)
    print("🔧 SOLUÇÃO DEFINITIVA: CRIANDO AGENTE fabio321")
    print("=" * 80)
    
    # Reseller correto dos tickets WhatsApp
    reseller_id = '49376e6f-4122-4fcf-88ab-97965c472711'
    
    # Buscar departamento WHATSAPP 1
    dept = await db.departments.find_one(
        {'name': 'WHATSAPP 1', 'reseller_id': reseller_id},
        {'_id': 0}
    )
    
    if not dept:
        print("❌ Departamento não encontrado!")
        return
    
    dept_id = dept['id']
    print(f"✅ Departamento WHATSAPP 1: {dept_id}")
    print(f"   Reseller: {reseller_id}")
    
    # Verificar se fabio321 já existe
    existing = await db.users.find_one({'username': 'fabio321', 'reseller_id': reseller_id}, {'_id': 0})
    
    if existing:
        print(f"✅ Usuário fabio321 já existe: {existing['id']}")
        agent_id = existing['id']
        
        # Atualizar departamentos
        await db.users.update_one(
            {'id': agent_id},
            {'$set': {'department_ids': [dept_id]}}
        )
        print(f"✅ Departamentos atualizados")
    else:
        # Criar novo agente
        agent_id = str(uuid.uuid4())
        print(f"⚠️ Criando novo usuário fabio321: {agent_id}")
        
        new_agent = {
            'id': agent_id,
            'reseller_id': reseller_id,
            'username': 'fabio321',
            'password': 'fabio321',  # TROCAR DEPOIS!
            'name': 'Fabio 321',
            'email': f'fabio321@{reseller_id}.temp',
            'user_type': 'agent',
            'department_ids': [dept_id],
            'is_active': True,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        await db.users.insert_one(new_agent)
        print(f"✅ Agente criado com sucesso!")
    
    # Adicionar agente ao array agent_ids do departamento
    current_agent_ids = dept.get('agent_ids', [])
    if agent_id not in current_agent_ids:
        current_agent_ids.append(agent_id)
        
        await db.departments.update_one(
            {'id': dept_id},
            {'$set': {'agent_ids': current_agent_ids}}
        )
        print(f"✅ Agente adicionado ao agent_ids do departamento")
    else:
        print(f"✅ Agente já está no agent_ids do departamento")
    
    # Verificar tickets
    tickets = await db.tickets.find({
        'department_id': dept_id,
        'status': 'open'
    }, {'_id': 0}).to_list(length=100)
    
    print(f"\n📊 TICKETS DISPONÍVEIS NO DEPARTAMENTO: {len(tickets)}")
    for t in tickets:
        print(f"   - {t['id']}: {t['client_name']} ({t.get('client_phone', 'N/A')})")
    
    print("\n" + "=" * 80)
    print("🎉 CONFIGURAÇÃO CONCLUÍDA!")
    print("=" * 80)
    print("\n📋 CREDENCIAIS:")
    print("   Username: fabio321")
    print("   Password: fabio321")
    print(f"   Departamento: WHATSAPP 1")
    print(f"\n✅ {len(tickets)} tickets devem aparecer no dashboard!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(fix_agent_and_tickets())
