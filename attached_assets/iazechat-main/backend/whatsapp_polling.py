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

EVOLUTION_API_URL = os.environ.get("EVOLUTION_API_URL", "https://447b612f69089c1ba2a9ac26b36266e2.serveo.net")
EVOLUTION_API_KEY = os.environ.get("EVOLUTION_API_KEY", "B4F8E9A2C5D7F1E3A9B6C8D2E5F7A1B3")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "support_chat")

# Armazenar IDs de mensagens já processadas
processed_messages = set()

async def check_connection_status(instance_name: str, api_key: str = None):
    """Verificar status da conexão na Evolution API"""
    try:
        apikey_header = api_key if api_key else EVOLUTION_API_KEY
        
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            # PRIMEIRO: Verificar se a instância existe
            check_response = await client.get(
                f"{EVOLUTION_API_URL}/instance/fetchInstances",
                headers={
                    "apikey": apikey_header,
                    "ngrok-skip-browser-warning": "true"
                }
            )
            
            if check_response.status_code == 200:
                instances = check_response.json()
                instance_exists = any(
                    inst.get("instance", {}).get("instanceName") == instance_name
                    for inst in instances
                )
                
                if not instance_exists:
                    print(f"⚠️ Instância {instance_name} NÃO EXISTE mais na Evolution API")
                    return "deleted"
            
            # SE EXISTE: Verificar connectionState
            response = await client.get(
                f"{EVOLUTION_API_URL}/instance/connectionState/{instance_name}",
                headers={
                    "apikey": apikey_header,
                    "ngrok-skip-browser-warning": "true"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                # Evolution API v1.8.5 retorna: {"instance": {"state": "open"}}
                instance_data = data.get("instance", {})
                state = instance_data.get("state", "").lower()
                
                # Evolution API estados: open, connecting, close
                if state == "open":
                    return "connected"
                elif state == "connecting":
                    return "connecting"
                else:
                    return "disconnected"
            elif response.status_code == 404:
                print(f"⚠️ Instância {instance_name} retornou 404 (deletada)")
                return "deleted"
            else:
                print(f"❌ Erro ao verificar status: {response.status_code}")
                return "error"
                
    except Exception as e:
        print(f"❌ Erro ao verificar status: {type(e).__name__}: {e}")
        return "error"

async def fetch_messages(instance_name: str, api_key: str = None):
    """Buscar mensagens da instância"""
    try:
        # Usar API key específica ou global
        apikey_header = api_key if api_key else EVOLUTION_API_KEY
        
        print(f"🔗 Tentando conectar: {EVOLUTION_API_URL}/chat/findMessages/{instance_name}")
        
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.post(
                f"{EVOLUTION_API_URL}/chat/findMessages/{instance_name}",
                headers={
                    "apikey": apikey_header,
                    "Content-Type": "application/json",
                    "ngrok-skip-browser-warning": "true"
                },
                json={"limit": 10}  # Limitar a 10 mensagens por vez
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Erro ao buscar mensagens: {response.status_code} - {response.text[:200]}")
                return []
    except httpx.TimeoutException as e:
        print(f"⏱️ Timeout ao conectar Evolution API: {e}")
        return []
    except httpx.ConnectError as e:
        print(f"🔌 Erro de conexão Evolution API: {e}")
        return []
    except Exception as e:
        print(f"❌ Erro inesperado ao buscar mensagens: {type(e).__name__}: {e}")
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
            "status": {"$in": ["open", "EM_ESPERA", "waiting"]}
        }, {"_id": 0})
        
        if not open_ticket:
            ticket_id = str(uuid.uuid4())
            ticket = {
                "id": ticket_id,
                "reseller_id": reseller_id,
                "client_id": client["id"],
                "client_name": client["name"],
                "client_phone": phone,
                "client_whatsapp": phone,  # Adicionar campo client_whatsapp
                "department": dept_name,
                "department_id": department["id"],  # IMPORTANTE: Adicionar department_id
                "department_name": dept_name,  # Adicionar department_name
                "subject": f"WhatsApp de {push_name}",
                "status": "open",  # Usar "open" para compatibilidade
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
        
        # ENVIAR NOTIFICAÇÃO VIA WEBSOCKET PARA AGENTES
        try:
            # Import WebSocket manager aqui para evitar problemas circulares
            # Enviar broadcast para todos os agentes da mesma revenda
            from server import manager
            await manager.broadcast_to_agents({
                "type": "new_message",
                "message": {
                    "id": message_obj["id"],
                    "ticket_id": ticket_id,
                    "from_type": "client",
                    "text": message_text,
                    "created_at": message_obj["timestamp"]
                }
            })
            print(f"✅ Notificação WebSocket enviada para agentes")
        except Exception as ws_error:
            print(f"⚠️ Erro ao enviar WebSocket (não crítico): {ws_error}")
        
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
    api_key = connection.get("api_key")  # Pegar API key específica
    connection_id = connection.get("id")
    
    try:
        # Verificar status da conexão
        status = await check_connection_status(instance_name, api_key)
        
        # SE INSTÂNCIA FOI DELETADA, RECRIAR
        if status == "deleted":
            print(f"🔄 Instância {instance_name} foi deletada, RECRIANDO...")
            
            # Recriar instância
            async with httpx.AsyncClient(timeout=30.0) as client:
                create_response = await client.post(
                    f"{EVOLUTION_API_URL}/instance/create",
                    json={
                        "instanceName": instance_name,
                        "qrcode": True
                    },
                    headers={
                        "Content-Type": "application/json",
                        "apikey": EVOLUTION_API_KEY
                    }
                )
                
                if create_response.status_code in [200, 201]:
                    print(f"✅ Instância {instance_name} RECRIADA")
                    
                    # Buscar novo QR Code
                    await asyncio.sleep(2)  # Aguardar instância inicializar
                    
                    qr_response = await client.get(
                        f"{EVOLUTION_API_URL}/instance/connect/{instance_name}",
                        headers={"apikey": EVOLUTION_API_KEY}
                    )
                    
                    if qr_response.status_code == 200:
                        qr_data = qr_response.json()
                        new_qr = qr_data.get('base64') or qr_data.get('code')
                        
                        # Atualizar QR Code no banco
                        await db.whatsapp_connections.update_one(
                            {"id": connection_id},
                            {
                                "$set": {
                                    "qr_code": new_qr,
                                    "status": "connecting",
                                    "connected": False,
                                    "updated_at": datetime.now(timezone.utc).isoformat()
                                }
                            }
                        )
                        print(f"✅ Novo QR Code atualizado para {instance_name}")
                    
                    return  # Sair do polling após recriar
                else:
                    print(f"❌ Erro ao recriar instância: {create_response.status_code}")
        
        # Atualizar status no banco se mudou
        current_status = connection.get("status", "disconnected")
        if status != current_status and status != "deleted":
            print(f"🔄 Status mudou de {current_status} -> {status} para {instance_name}")
            await db.whatsapp_connections.update_one(
                {"id": connection_id},
                {
                    "$set": {
                        "status": status,
                        "connected": status == "connected",
                        "last_activity": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
        
        # Se não está conectado, não buscar mensagens
        if status != "connected":
            return
        
        messages = await fetch_messages(instance_name, api_key)
        
        if messages and isinstance(messages, list):
            # Processar apenas mensagens recentes (últimas 10)
            for message in messages[:10]:
                await process_message(message, connection, db)
                
    except Exception as e:
        print(f"❌ Erro no polling de {instance_name}: {e}")

async def main_polling_loop():
    """Loop principal de polling"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("🔄 WhatsApp Polling iniciado...")
    print(f"📊 Conectado ao banco: {DB_NAME}")
    print(f"🔗 Evolution API URL: {EVOLUTION_API_URL}")
    
    while True:
        try:
            # Buscar TODAS as conexões (para verificar e atualizar status)
            connections = await db.whatsapp_connections.find({}, {"_id": 0}).to_list(length=100)
            
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
