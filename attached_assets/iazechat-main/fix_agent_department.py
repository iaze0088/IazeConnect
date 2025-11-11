#!/usr/bin/env python3
"""
Script para vincular agente ao departamento WHATSAPP 1
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

async def fix_agent_department():
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
    db = client.support_chat
    
    # Reseller ID correto (dos logs)
    reseller_id = '49376e6f-4122-4fcf-88ab-97965c472711'
    
    # Buscar departamento WHATSAPP 1
    dept = await db.departments.find_one(
        {'name': 'WHATSAPP 1', 'reseller_id': reseller_id}, 
        {'_id': 0}
    )
    
    if not dept:
        print('❌ Departamento WHATSAPP 1 não encontrado!')
        return
    
    print(f'✅ Departamento encontrado: {dept["id"]}')
    
    # Buscar usuário fabio123
    user = await db.users.find_one({'username': 'fabio123'}, {'_id': 0})
    
    if not user:
        print('❌ Usuário fabio123 não encontrado!')
        print('Listando usuários disponíveis:')
        users = await db.users.find({'reseller_id': reseller_id}, {'_id': 0}).to_list(length=100)
        for u in users:
            print(f'  - {u.get("username")} ({u.get("user_type")})')
        return
    
    print(f'✅ Usuário encontrado: {user["id"]} - Tipo: {user.get("user_type")}')
    
    # Atualizar departamentos
    result = await db.users.update_one(
        {'id': user['id']},
        {'$set': {'department_ids': [dept['id']]}}
    )
    
    print(f'✅ Agente vinculado ao departamento WHATSAPP 1!')
    print(f'   Modified: {result.modified_count}')
    
    # Verificar
    updated_user = await db.users.find_one({'id': user['id']}, {'_id': 0})
    print(f'✅ Departamentos atualizados: {updated_user.get("department_ids")}')

if __name__ == "__main__":
    asyncio.run(fix_agent_department())
