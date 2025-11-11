"""
Sistema de Polling para Evolution API - Alternativa ao Webhook
Busca mensagens novas a cada 5 segundos
"""
import asyncio
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
import uuid

EVOLUTION_API_URL = os.environ.get("EVOLUTION_API_URL", "http://45.157.157.69:8080")
EVOLUTION_API_KEY = os.environ.get("EVOLUTION_API_KEY", "B4F8E9A2C5D7F1E3A9B6C8D2E5F7A1B3")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")

# Armazenar IDs de mensagens já processadas
processed_messages = set()

async def fetch_messages(instance_name: str):
    """Buscar mensagens da instância"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{EVOLUTION_API_URL}/chat/fetchMessages/{instance_name}",
                headers={"apikey": EVOLUTION_API_KEY},
                params={"limit": 50}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Erro ao buscar mensagens: {response.status_code}")
                return []
    except Exception as e:
        print(f"❌ Erro ao buscar mensagens: {e}")
        return []

async def process_message(message, connection, db):
    """Processar uma mensagem individual"""
    try:
        # Extrair dados
        message_key = message.get("key", {})
        message_content = message.get("message", {})
        
        # Verificar se é mensagem do bot (ignorar)
        if message_key.get("fromMe"):
            return
        
        # Extrair número e texto
        remote_jid = message_key.get("remoteJid", "")
        phone = remote_jid.replace("@s.whatsapp.net", "").replace("@c.us", "")
        
        message_text = (
            message_content.get("conversation") or
            message_content.get("extendedTextMessage", {}).get("text") or
            ""
        )
        
        push_name = message.get("pushName", phone)
        message_id = message_key.get("id", "")
        
        # Verificar se já processamos
        if message_id in processed_messages:
            return
        
        if not phone or not message_text:
            return
        
        print(f"📥 Nova mensagem: {push_name} ({phone}): {message_text}")
        
        reseller_id = connection["reseller_id"]
        
        # Buscar ou criar departamento
        dept_name = f"WHATSAPP {connection.get('rotation_order', 1)}"
        department = await db.departments.find_one({
            "reseller_id": reseller_id,
            "name": dept_name
        }, {"_id": 0})
        
        if not department:
            department = {
                "id": str(uuid.uuid4()),
                "reseller_id": reseller_id,
                "name": dept_name,
                "description": f"Atendimento WhatsApp - Número {connection.get('rotation_order', 1)}",
                "agent_ids": [],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.departments.insert_one(department)
        
        # Buscar ou criar cliente
        client = await db.clients.find_one({
            "reseller_id": reseller_id,
            "phone": phone
        }, {"_id": 0})
        
        if not client:
            client = {
                "id": str(uuid.uuid4()),
                "reseller_id": reseller_id,
                "name": push_name,
                "email": f"{phone}@whatsapp.temp",
                "phone": phone,
                "whatsapp_origin": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.clients.insert_one(client)
        
        # Buscar ticket aberto
        open_ticket = await db.tickets.find_one({
            "reseller_id": reseller_id,
            "client_id": client["id"],
            "status": {"$in": ["open", "waiting"]}
        }, {"_id": 0})
        
        if not open_ticket:
            ticket_id = str(uuid.uuid4())
            ticket = {
                "id": ticket_id,
                "reseller_id": reseller_id,
                "client_id": client["id"],
                "client_name": client["name"],
                "client_phone": phone,
                "department": dept_name,
                "subject": f"WhatsApp de {push_name}",
                "status": "waiting",
                "priority": "medium",
                "agent_id": None,
                "whatsapp_origin": True,
                "whatsapp_connection_id": connection["id"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            await db.tickets.insert_one(ticket)
            print(f"✅ Ticket criado: {ticket_id}")
        else:
            ticket_id = open_ticket["id"]
        
        # Adicionar mensagem
        message_obj = {
            "id": str(uuid.uuid4()),
            "ticket_id": ticket_id,
            "sender_type": "client",
            "sender_name": push_name,
            "message": message_text,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await db.messages.insert_one(message_obj)
        
        # Incrementar contador
        await db.whatsapp_connections.update_one(
            {"id": connection["id"]},
            {
                "$inc": {"received_today": 1},
                "$set": {"last_activity": datetime.now(timezone.utc).isoformat()}
            }
        )
        
        # Marcar como processada
        processed_messages.add(message_id)
        
        print(f"✅ Mensagem processada: {phone} -> Ticket {ticket_id}")
        
    except Exception as e:
        print(f"❌ Erro ao processar mensagem: {e}")
        import traceback
        traceback.print_exc()

async def poll_instance(connection, db):
    """Polling de uma instância específica"""
    instance_name = connection["instance_name"]
    
    try:
        messages = await fetch_messages(instance_name)
        
        if messages and isinstance(messages, list):
            # Processar apenas mensagens recentes (últimas 10)
            for message in messages[:10]:
                await process_message(message, connection, db)
                
    except Exception as e:
        print(f"❌ Erro no polling de {instance_name}: {e}")

async def main_polling_loop():
    """Loop principal de polling"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.cybertv_db
    
    print("🔄 WhatsApp Polling iniciado...")
    
    while True:
        try:
            # Buscar todas as conexões ativas
            connections = await db.whatsapp_connections.find({
                "status": "connected"
            }, {"_id": 0}).to_list(length=100)
            
            if connections:
                print(f"🔍 Polling {len(connections)} conexão(ões)...")
                
                # Polling de cada conexão
                for conn in connections:
                    await poll_instance(conn, db)
            
            # Aguardar 5 segundos
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"❌ Erro no loop principal: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main_polling_loop())
