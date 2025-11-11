"""
Script de Verificação de Persistência de Dados
Execute ANTES e DEPOIS do deploy para garantir que nada foi perdido
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')

async def verify_data_persistence():
    """Verificar integridade dos dados"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.support_chat
    
    print("\n" + "="*60)
    print("🔍 VERIFICAÇÃO DE PERSISTÊNCIA DE DADOS - IAZE")
    print("="*60)
    print(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🗄️  Banco: {MONGO_URL}")
    print("="*60 + "\n")
    
    # 1. Tickets
    total_tickets = await db.tickets.count_documents({})
    tickets_espera = await db.tickets.count_documents({"status": "open", "agent_id": {"$exists": False}})
    tickets_atendendo = await db.tickets.count_documents({"status": "open", "agent_id": {"$exists": True}})
    tickets_finalizados = await db.tickets.count_documents({"status": "closed"})
    
    print("📋 TICKETS (Conversas):")
    print(f"   Total: {total_tickets}")
    print(f"   ⏳ Em Espera: {tickets_espera}")
    print(f"   💬 Em Atendimento: {tickets_atendendo}")
    print(f"   ✅ Finalizados: {tickets_finalizados}")
    
    # 2. Mensagens
    total_messages = await db.messages.count_documents({})
    print(f"\n💬 MENSAGENS:")
    print(f"   Total: {total_messages}")
    
    # 3. Usuários
    total_users = await db.users.count_documents({})
    admins = await db.users.count_documents({"user_type": "admin"})
    resellers = await db.users.count_documents({"user_type": "reseller"})
    agents = await db.users.count_documents({"user_type": "agent"})
    
    print(f"\n👥 USUÁRIOS:")
    print(f"   Total: {total_users}")
    print(f"   🔑 Admins: {admins}")
    print(f"   🏢 Resellers: {resellers}")
    print(f"   👨‍💼 Agentes: {agents}")
    
    # 4. Departamentos
    total_departments = await db.departments.count_documents({})
    print(f"\n📂 DEPARTAMENTOS:")
    print(f"   Total: {total_departments}")
    
    # 5. Clientes
    total_clients = await db.clients.count_documents({})
    print(f"\n👤 CLIENTES:")
    print(f"   Total: {total_clients}")
    
    # 6. Configurações de Revendas
    total_configs = await db.reseller_configs.count_documents({})
    print(f"\n⚙️  CONFIGURAÇÕES:")
    print(f"   Total: {total_configs}")
    
    # 7. WhatsApp
    total_whatsapp = await db.whatsapp_connections.count_documents({})
    whatsapp_connected = await db.whatsapp_connections.count_documents({"status": "connected"})
    print(f"\n📱 WHATSAPP:")
    print(f"   Total conexões: {total_whatsapp}")
    print(f"   Conectadas: {whatsapp_connected}")
    
    # 8. Avisos
    total_notices = await db.notices.count_documents({})
    print(f"\n📢 AVISOS:")
    print(f"   Total: {total_notices}")
    
    # Resumo
    print("\n" + "="*60)
    print("📊 RESUMO:")
    print("="*60)
    
    total_records = (
        total_tickets + 
        total_messages + 
        total_users + 
        total_departments + 
        total_clients + 
        total_configs +
        total_whatsapp +
        total_notices
    )
    
    print(f"📈 Total de registros no banco: {total_records:,}")
    
    if total_records > 0:
        print("✅ Banco de dados contém dados")
    else:
        print("⚠️  Banco de dados vazio (primeira inicialização?)")
    
    print("\n" + "="*60)
    print("💾 SALVE ESTES NÚMEROS PARA COMPARAR APÓS O DEPLOY!")
    print("="*60 + "\n")
    
    # Criar arquivo de log
    log_file = f"/tmp/data_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(log_file, 'w') as f:
        f.write(f"Data/Hora: {datetime.now()}\n")
        f.write(f"Total Tickets: {total_tickets}\n")
        f.write(f"  - Espera: {tickets_espera}\n")
        f.write(f"  - Atendendo: {tickets_atendendo}\n")
        f.write(f"  - Finalizados: {tickets_finalizados}\n")
        f.write(f"Total Mensagens: {total_messages}\n")
        f.write(f"Total Usuários: {total_users}\n")
        f.write(f"Total Departamentos: {total_departments}\n")
        f.write(f"Total Clientes: {total_clients}\n")
        f.write(f"Total Configs: {total_configs}\n")
        f.write(f"Total WhatsApp: {total_whatsapp}\n")
        f.write(f"Total Avisos: {total_notices}\n")
        f.write(f"TOTAL GERAL: {total_records}\n")
    
    print(f"📄 Log salvo em: {log_file}\n")
    
    client.close()
    
    return {
        "tickets": total_tickets,
        "messages": total_messages,
        "users": total_users,
        "departments": total_departments,
        "clients": total_clients,
        "configs": total_configs,
        "whatsapp": total_whatsapp,
        "notices": total_notices,
        "total": total_records
    }

if __name__ == "__main__":
    print("\n🚀 EXECUTE ESTE SCRIPT:")
    print("   1️⃣  ANTES DO DEPLOY → Anote os números")
    print("   2️⃣  APÓS O DEPLOY → Compare os números")
    print("   ✅ Números devem ser IGUAIS ou MAIORES\n")
    
    asyncio.run(verify_data_persistence())
