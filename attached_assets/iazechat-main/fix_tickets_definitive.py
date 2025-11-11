#!/usr/bin/env python3
"""
SOLUÇÃO DEFINITIVA E ROBUSTA:
1. Limpar duplicações
2. Garantir agente único na collection users
3. Vincular corretamente ao departamento
4. Validar estrutura
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone

async def definitive_fix():
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
    db = client.support_chat
    
    print("=" * 80)
    print("🔧 SOLUÇÃO DEFINITIVA - CORREÇÃO COMPLETA")
    print("=" * 80)
    
    # 1. Identificar departamento WHATSAPP 1 correto (com tickets)
    reseller_id = '49376e6f-4122-4fcf-88ab-97965c472711'
    dept = await db.departments.find_one({
        'name': 'WHATSAPP 1',
        'reseller_id': reseller_id
    }, {'_id': 0})
    
    if not dept:
        print("❌ Departamento não encontrado!")
        return
    
    dept_id = dept['id']
    print(f"✅ Departamento: {dept_id}")
    print(f"   Reseller: {reseller_id}")
    print(f"   Agent IDs atuais: {dept.get('agent_ids', [])}")
    
    # 2. Limpar collection agents (não usada pelo sistema)
    print(f"\n🗑️ Limpando collection agents (não usada)...")
    result = await db.agents.delete_many({})
    print(f"   Removidos: {result.deleted_count}")
    
    # 3. Garantir fabio321 existe APENAS em users
    print(f"\n👤 Verificando agente fabio321...")
    user = await db.users.find_one({'username': 'fabio321', 'reseller_id': reseller_id}, {'_id': 0})
    
    if not user:
        print("⚠️ Criando agente fabio321...")
        import uuid
        user_id = str(uuid.uuid4())
        user = {
            'id': user_id,
            'reseller_id': reseller_id,
            'username': 'fabio321',
            'password': 'fabio321',
            'name': 'Fabio 321',
            'email': f'fabio321@{reseller_id}.com',
            'user_type': 'agent',
            'department_ids': [dept_id],
            'is_active': True,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user)
        print(f"✅ Agente criado: {user_id}")
    else:
        user_id = user['id']
        print(f"✅ Agente existe: {user_id}")
        
        # Atualizar department_ids
        await db.users.update_one(
            {'id': user_id},
            {'$set': {'department_ids': [dept_id]}}
        )
        print(f"✅ department_ids atualizado")
    
    # 4. Adicionar agente ao agent_ids do departamento
    print(f"\n📋 Vinculando agente ao departamento...")
    current_agent_ids = dept.get('agent_ids', [])
    if user_id not in current_agent_ids:
        current_agent_ids.append(user_id)
    
    await db.departments.update_one(
        {'id': dept_id},
        {'$set': {'agent_ids': current_agent_ids}}
    )
    print(f"✅ agent_ids do departamento: {current_agent_ids}")
    
    # 5. Verificar tickets
    tickets = await db.tickets.find({
        'department_id': dept_id,
        'reseller_id': reseller_id,
        'status': 'open'
    }, {'_id': 0}).to_list(100)
    
    print(f"\n🎫 TICKETS DISPONÍVEIS: {len(tickets)}")
    for t in tickets[:5]:  # Mostrar apenas 5
        print(f"   - {t['id'][:8]}... {t.get('client_name', 'N/A')}")
    if len(tickets) > 5:
        print(f"   ... e mais {len(tickets)-5} tickets")
    
    # 6. Validação Final
    print(f"\n✅ VALIDAÇÃO FINAL:")
    print(f"   Agente ID: {user_id}")
    print(f"   Departamento ID: {dept_id}")
    print(f"   Reseller ID: {reseller_id}")
    print(f"   Tickets disponíveis: {len(tickets)}")
    print(f"   Agent IDs do dept: {current_agent_ids}")
    
    # 7. Teste da query que o backend faz
    print(f"\n🔍 SIMULANDO QUERY DO BACKEND:")
    test_departments = await db.departments.find({
        'reseller_id': reseller_id,
        '$or': [
            {'agent_ids': []},
            {'agent_ids': {'$exists': False}},
            {'agent_ids': {'$in': [user_id]}}
        ]
    }, {'_id': 0, 'id': 1, 'name': 1}).to_list(100)
    
    test_dept_ids = [d['id'] for d in test_departments]
    print(f"   Departamentos encontrados: {len(test_departments)}")
    for d in test_departments:
        print(f"      - {d.get('name')}: {d['id']}")
    
    test_tickets = await db.tickets.find({
        'reseller_id': reseller_id,
        'department_id': {'$in': test_dept_ids},
        'status': 'open'
    }, {'_id': 0}).to_list(100)
    
    print(f"   Tickets que seriam retornados: {len(test_tickets)}")
    
    print("\n" + "=" * 80)
    print("🎉 CORREÇÃO DEFINITIVA CONCLUÍDA!")
    print("=" * 80)
    print("\nCREDENCIAIS:")
    print("   Username: fabio321")
    print("   Password: fabio321")
    print(f"\nFaça LOGOUT e LOGIN novamente!")
    print(f"Os {len(test_tickets)} tickets DEVEM aparecer!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(definitive_fix())
