"""
Script para sincronizar department_ids em agentes antigos
Executa a sincronização reversa: departamento → agente
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')

async def sync_agent_departments():
    """Sincronizar department_ids para todos os agentes"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.support_chat
    
    print("🔄 Iniciando sincronização de departamentos para agentes...")
    
    # Buscar todos os departamentos
    departments = await db.departments.find({}).to_list(None)
    print(f"📋 Encontrados {len(departments)} departamentos")
    
    synced_count = 0
    
    for dept in departments:
        dept_id = dept["id"]
        agent_ids = dept.get("agent_ids", [])
        
        if not agent_ids:
            print(f"⏭️  Departamento '{dept['name']}' sem agentes específicos (todos têm acesso)")
            continue
        
        print(f"\n📂 Departamento: {dept['name']} (ID: {dept_id})")
        print(f"   Agentes: {len(agent_ids)}")
        
        for agent_id in agent_ids:
            # Verificar se agente existe
            agent = await db.users.find_one({"id": agent_id, "user_type": "agent"})
            
            if not agent:
                print(f"   ⚠️  Agente {agent_id} não encontrado")
                continue
            
            # Adicionar department_id ao agente (se ainda não tiver)
            current_dept_ids = agent.get("department_ids", [])
            
            if dept_id not in current_dept_ids:
                await db.users.update_one(
                    {"id": agent_id, "user_type": "agent"},
                    {"$addToSet": {"department_ids": dept_id}}
                )
                print(f"   ✅ Agente '{agent.get('name', agent_id)}' sincronizado com departamento '{dept['name']}'")
                synced_count += 1
            else:
                print(f"   ✓  Agente '{agent.get('name', agent_id)}' já tinha departamento '{dept['name']}'")
    
    print(f"\n✅ Sincronização concluída!")
    print(f"📊 Total de agentes sincronizados: {synced_count}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(sync_agent_departments())
