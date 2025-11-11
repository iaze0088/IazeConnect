"""
Script para criar índices únicos no MongoDB
Previne duplicação de IDs, logins, emails, etc.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

async def create_unique_indexes():
    """Criar índices únicos para prevenir duplicatas"""
    
    client = AsyncIOMotorClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
    db = client[os.environ.get("DB_NAME", "support_chat")]
    
    print("=" * 80)
    print("🔒 CRIANDO ÍNDICES ÚNICOS NO MONGODB")
    print("=" * 80)
    
    try:
        # 1. USERS (agents) - username único por reseller
        print("\n👤 1. Índice único para USERS (username + reseller_id)...")
        try:
            await db.users.create_index(
                [("username", 1), ("reseller_id", 1)],
                unique=True,
                name="unique_username_per_reseller"
            )
            print("✅ Índice criado: unique_username_per_reseller")
        except Exception as e:
            print(f"⚠️ Índice já existe ou erro: {e}")
        
        # 2. USERS - ID único global
        print("\n🆔 2. Índice único para USERS (id)...")
        try:
            await db.users.create_index(
                [("id", 1)],
                unique=True,
                name="unique_user_id"
            )
            print("✅ Índice criado: unique_user_id")
        except Exception as e:
            print(f"⚠️ Índice já existe ou erro: {e}")
        
        # 3. RESELLERS - email único
        print("\n📧 3. Índice único para RESELLERS (email)...")
        try:
            await db.resellers.create_index(
                [("email", 1)],
                unique=True,
                name="unique_reseller_email"
            )
            print("✅ Índice criado: unique_reseller_email")
        except Exception as e:
            print(f"⚠️ Índice já existe ou erro: {e}")
        
        # 4. RESELLERS - ID único
        print("\n🆔 4. Índice único para RESELLERS (id)...")
        try:
            await db.resellers.create_index(
                [("id", 1)],
                unique=True,
                name="unique_reseller_id"
            )
            print("✅ Índice criado: unique_reseller_id")
        except Exception as e:
            print(f"⚠️ Índice já existe ou erro: {e}")
        
        # 5. CLIENTS - phone único por reseller
        print("\n📱 5. Índice único para CLIENTS (phone + reseller_id)...")
        try:
            await db.clients.create_index(
                [("phone", 1), ("reseller_id", 1)],
                unique=True,
                name="unique_phone_per_reseller"
            )
            print("✅ Índice criado: unique_phone_per_reseller")
        except Exception as e:
            print(f"⚠️ Índice já existe ou erro: {e}")
        
        # 6. CLIENTS - ID único
        print("\n🆔 6. Índice único para CLIENTS (id)...")
        try:
            await db.clients.create_index(
                [("id", 1)],
                unique=True,
                name="unique_client_id"
            )
            print("✅ Índice criado: unique_client_id")
        except Exception as e:
            print(f"⚠️ Índice já existe ou erro: {e}")
        
        # 7. TICKETS - ID único
        print("\n🆔 7. Índice único para TICKETS (id)...")
        try:
            await db.tickets.create_index(
                [("id", 1)],
                unique=True,
                name="unique_ticket_id"
            )
            print("✅ Índice criado: unique_ticket_id")
        except Exception as e:
            print(f"⚠️ Índice já existe ou erro: {e}")
        
        # 8. DEPARTMENTS - ID único
        print("\n🆔 8. Índice único para DEPARTMENTS (id)...")
        try:
            await db.departments.create_index(
                [("id", 1)],
                unique=True,
                name="unique_department_id"
            )
            print("✅ Índice criado: unique_department_id")
        except Exception as e:
            print(f"⚠️ Índice já existe ou erro: {e}")
        
        # 9. WHATSAPP_CONNECTIONS - instance_name único
        print("\n📱 9. Índice único para WHATSAPP_CONNECTIONS (instance_name)...")
        try:
            await db.whatsapp_connections.create_index(
                [("instance_name", 1)],
                unique=True,
                name="unique_instance_name"
            )
            print("✅ Índice criado: unique_instance_name")
        except Exception as e:
            print(f"⚠️ Índice já existe ou erro: {e}")
        
        # Listar todos os índices criados
        print("\n" + "=" * 80)
        print("📋 ÍNDICES CRIADOS:")
        print("=" * 80)
        
        collections = [
            "users", "resellers", "clients", "tickets", 
            "departments", "whatsapp_connections"
        ]
        
        for collection_name in collections:
            collection = db[collection_name]
            indexes = await collection.index_information()
            print(f"\n🗂️ {collection_name.upper()}:")
            for index_name, index_info in indexes.items():
                if index_name != "_id_":
                    unique = index_info.get("unique", False)
                    keys = index_info.get("key", [])
                    print(f"   {'🔒' if unique else '📌'} {index_name}: {keys}")
        
        print("\n" + "=" * 80)
        print("✅ TODOS OS ÍNDICES ÚNICOS FORAM CRIADOS/VERIFICADOS!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERRO AO CRIAR ÍNDICES: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(create_unique_indexes())
