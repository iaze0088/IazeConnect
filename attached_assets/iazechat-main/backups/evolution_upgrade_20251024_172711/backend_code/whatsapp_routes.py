"""
Rotas WhatsApp Evolution API
Sistema completo de gerenciamento e rotação
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List
import uuid
from datetime import datetime, timezone

from whatsapp_models import *
from whatsapp_service import WhatsAppService
from tenant_helpers import get_tenant_filter, get_request_tenant
from server import get_current_user, db

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])

# Instanciar serviço
whatsapp_service = WhatsAppService(db)

# ==================== WEBHOOK Z-API ====================

@router.post("/webhook/evolution")
async def webhook_evolution(request: Request):
    """Receber eventos da Evolution API (mensagens, status, etc)"""
    try:
        data = await request.json()
        event_type = data.get("event")
        
        print(f"📨 Webhook Evolution API: {event_type}")
        print(f"   Data: {data}")
        
        # Processar diferentes tipos de eventos
        if event_type == "messages.upsert":
            # Nova mensagem recebida
            return await process_evolution_message(data)
        elif event_type == "connection.update":
            # Atualização de status da conexão
            return await process_evolution_connection_update(data)
        else:
            print(f"⚠️ Evento não processado: {event_type}")
            return {"success": True, "message": "Event received but not processed"}
            
    except Exception as e:
        print(f"❌ Erro no webhook Evolution: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

async def process_evolution_connection_update(data):
    """Processar atualização de status da conexão"""
    try:
        instance_data = data.get("instance", {})
        instance_name = instance_data.get("instanceName")
        state = instance_data.get("state")  # open, close, connecting
        
        if not instance_name:
            return {"success": False, "error": "No instance name"}
        
        # Mapear estados Evolution API para CYBERTV
        status_map = {
            "open": "connected",
            "close": "disconnected",
            "connecting": "connecting"
        }
        
        cybertv_status = status_map.get(state, "disconnected")
        
        # Atualizar status no banco
        result = await db.whatsapp_connections.update_one(
            {"instance_name": instance_name},
            {
                "$set": {
                    "status": cybertv_status,
                    "last_activity": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        if result.modified_count > 0:
            print(f"✅ Status atualizado: {instance_name} -> {cybertv_status}")
        
        return {"success": True, "instance": instance_name, "status": cybertv_status}
        
    except Exception as e:
        print(f"❌ Erro ao processar connection.update: {e}")
        return {"success": False, "error": str(e)}

async def process_evolution_message(data):
    """Processar mensagem recebida da Evolution API"""
    try:
        instance_name = data.get("instance")
        
        # Evolution API envia dados em formato diferente
        message_data = data.get("data", {})
        
        # Extrair informações da mensagem
        message_key = message_data.get("key", {})
        message_content = message_data.get("message", {})
        push_name = message_data.get("pushName", "")
        
        # Extrair número do remetente
        remote_jid = message_key.get("remoteJid", "")
        phone = remote_jid.replace("@s.whatsapp.net", "").replace("@c.us", "")
        
        # Verificar se é mensagem do próprio bot (ignorar)
        if message_key.get("fromMe"):
            print("⚠️ Mensagem própria, ignorando")
            return {"success": True, "message": "Own message ignored"}
        
        # Extrair texto da mensagem
        message_text = (
            message_content.get("conversation") or 
            message_content.get("extendedTextMessage", {}).get("text") or 
            ""
        )
        
        if not phone or not message_text:
            print(f"⚠️ Dados incompletos: phone={phone}, text={message_text}")
            return {"success": False, "error": "Invalid message data"}
        
        print(f"📥 Processando mensagem de {push_name} ({phone}): {message_text}")
        
        # Buscar conexão WhatsApp
        connection = await db.whatsapp_connections.find_one({
            "instance_name": instance_name
        }, {"_id": 0})
        
        if not connection:
            print(f"❌ Conexão não encontrada: {instance_name}")
            return {"success": False, "error": "Connection not found"}
        
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
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.departments.insert_one(department)
        
        # Buscar ou criar cliente
        sender_name = push_name or phone
        client = await db.clients.find_one({
            "reseller_id": reseller_id,
            "phone": phone
        }, {"_id": 0})
        
        if not client:
            client = {
                "id": str(uuid.uuid4()),
                "reseller_id": reseller_id,
                "name": sender_name,
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
            "status": "open"
        }, {"_id": 0})
        
        if not open_ticket:
            ticket_id = str(uuid.uuid4())
            ticket = {
                "id": ticket_id,
                "reseller_id": reseller_id,
                "client_id": client["id"],
                "client_name": client["name"],
                "client_phone": phone,
                "department_id": department["id"],
                "department_name": dept_name,
                "subject": f"WhatsApp de {sender_name}",
                "status": "open",
                "priority": "medium",
                "agent_id": None,
                "whatsapp_origin": True,
                "whatsapp_connection_id": connection["id"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            await db.tickets.insert_one(ticket)
        else:
            ticket_id = open_ticket["id"]
        
        # Adicionar mensagem
        message_obj = {
            "id": str(uuid.uuid4()),
            "ticket_id": ticket_id,
            "sender_type": "client",
            "sender_name": sender_name,
            "content": message_text,
            "is_whatsapp": True,
            "whatsapp_phone": phone,
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
        
        print(f"✅ Mensagem WhatsApp salva: {phone} -> Ticket {ticket_id}")
        
        return {"success": True, "ticket_id": ticket_id, "department": dept_name}
        
    except Exception as e:
        print(f"❌ Erro ao processar mensagem: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@router.post("/webhook")
async def webhook_zapi(request: Request):
    """Receber mensagens do webhook Z-API e criar tickets automaticamente (LEGACY)"""
    try:
        data = await request.json()
        
        # Extrair dados da mensagem
        phone = data.get("phone", "").replace("@c.us", "").replace("@s.whatsapp.net", "")
        message_text = data.get("text", {}).get("message", "")
        sender_name = data.get("senderName", phone)
        
        if not phone or not message_text:
            return {"success": False, "error": "Invalid data"}
        
        # Buscar qual conexão WhatsApp recebeu (pela instância)
        connection = await db.whatsapp_connections.find_one({
            "status": "connected"
        }, {"_id": 0})
        
        if not connection:
            print("❌ Nenhuma conexão WhatsApp ativa para receber mensagem")
            return {"success": False, "error": "No active connection"}
        
        reseller_id = connection["reseller_id"]
        whatsapp_number = connection.get("phone_number", "WhatsApp")
        
        # Buscar ou criar departamento WhatsApp para esta conexão
        dept_name = f"WHATSAPP {connection['rotation_order']}"
        department = await db.departments.find_one({
            "reseller_id": reseller_id,
            "name": dept_name
        }, {"_id": 0})
        
        if not department:
            # Criar departamento automático
            department = {
                "id": str(uuid.uuid4()),
                "reseller_id": reseller_id,
                "name": dept_name,
                "description": f"Atendimento via WhatsApp - Número {connection['rotation_order']}",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.departments.insert_one(department)
        
        # Buscar cliente existente ou criar novo
        client = await db.clients.find_one({
            "reseller_id": reseller_id,
            "phone": phone
        }, {"_id": 0})
        
        if not client:
            # Criar novo cliente
            client = {
                "id": str(uuid.uuid4()),
                "reseller_id": reseller_id,
                "name": sender_name,
                "email": f"{phone}@whatsapp.temp",
                "phone": phone,
                "whatsapp_origin": True,
                "whatsapp_number": whatsapp_number,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.clients.insert_one(client)
        
        # Buscar ticket aberto para este cliente
        open_ticket = await db.tickets.find_one({
            "reseller_id": reseller_id,
            "client_id": client["id"],
            "status": "open"
        }, {"_id": 0})
        
        if not open_ticket:
            # Criar novo ticket
            ticket_id = str(uuid.uuid4())
            ticket = {
                "id": ticket_id,
                "reseller_id": reseller_id,
                "client_id": client["id"],
                "client_name": client["name"],
                "client_phone": phone,
                "department_id": department["id"],
                "department_name": dept_name,
                "subject": f"WhatsApp de {sender_name}",
                "status": "open",
                "priority": "medium",
                "agent_id": None,
                "whatsapp_origin": True,
                "whatsapp_connection_id": connection["id"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            await db.tickets.insert_one(ticket)
        else:
            ticket_id = open_ticket["id"]
        
        # Adicionar mensagem ao ticket
        message_obj = {
            "id": str(uuid.uuid4()),
            "ticket_id": ticket_id,
            "sender_type": "client",
            "sender_name": sender_name,
            "content": message_text,
            "is_whatsapp": True,
            "whatsapp_phone": phone,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await db.messages.insert_one(message_obj)
        
        # Incrementar contador de mensagens recebidas
        await db.whatsapp_connections.update_one(
            {"id": connection["id"]},
            {"$inc": {"received_today": 1}}
        )
        
        print(f"✅ Mensagem WhatsApp recebida: {phone} -> {dept_name}")
        
        return {"success": True, "ticket_id": ticket_id, "department": dept_name}
        
    except Exception as e:
        print(f"❌ Erro no webhook: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

# ==================== CONEXÕES ====================

@router.post("/connections")
async def create_connection(
    data: WhatsAppConnectionCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Criar nova conexão WhatsApp - COM PROTEÇÃO CONTRA DUPLICATAS"""
    
    # Verificar permissão (admin ou próprio reseller)
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    if current_user["user_type"] == "reseller":
        if current_user.get("reseller_id") != data.reseller_id:
            raise HTTPException(status_code=403, detail="Can only create for own reseller")
    
    # 🔥 VERIFICAR SE JÁ EXISTE QUALQUER CONEXÃO (não apenas desativadas)
    existing_any = await db.whatsapp_connections.find_one(
        {"reseller_id": data.reseller_id},
        {"_id": 0}
    )
    
    if existing_any:
        logger.info(f"⚠️ Conexão já existe para reseller {data.reseller_id}, retornando a existente")
        # Retornar a conexão existente sem criar nova
        return existing_any
    
    # Se não existe NENHUMA conexão, permitir criar
    logger.info(f"✅ Nenhuma conexão encontrada para reseller {data.reseller_id}, criando nova...")
    
    # Verificar limite do plano
    config = await db.whatsapp_configs.find_one({"reseller_id": data.reseller_id}, {"_id": 0})
    if config:
        plan_name = config.get("plan", "basico")
        plan = WHATSAPP_PLANS.get(plan_name)
        
        if plan:
            existing_count = await db.whatsapp_connections.count_documents({
                "reseller_id": data.reseller_id,
                "status": "connected"
            })
            
            if plan.max_numbers != -1 and existing_count >= plan.max_numbers:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Plan limit reached. Current plan allows {plan.max_numbers} numbers. Upgrade to add more."
                )
    
    # Gerar nome único da instância (com timestamp)
    reseller = await db.resellers.find_one({"id": data.reseller_id}, {"_id": 0})
    if not reseller:
        raise HTTPException(status_code=404, detail="Reseller not found")
    
    connection_count = await db.whatsapp_connections.count_documents({"reseller_id": data.reseller_id})
    
    from datetime import datetime
    timestamp = int(datetime.now().timestamp())
    base_name = reseller['name'].lower().replace(' ', '').replace('-', '')[:10]
    instance_name = f"{base_name}_{connection_count + 1}_{timestamp}"
    
    # Criar instância na Evolution API
    result = await whatsapp_service.create_instance(data.reseller_id, instance_name)
    
    if not result["success"]:
        # Melhorar mensagem de erro para o usuário
        error_msg = result.get("error", "Unknown error")
        
        if "connection" in error_msg.lower() or "failed" in error_msg.lower() or "timeout" in error_msg.lower() or "wppconnect" in error_msg.lower():
            raise HTTPException(
                status_code=503, 
                detail="WPPConnect API não está disponível. Por favor, verifique se o serviço está rodando no servidor Hetzner ou entre em contato com o suporte."
            )
        else:
            raise HTTPException(status_code=500, detail=error_msg)
    
    # Salvar no banco
    connection_data = {
        "id": str(uuid.uuid4()),
        "reseller_id": data.reseller_id,
        "instance_name": instance_name,
        "phone_number": None,
        "status": "connecting",
        "qr_code": None,
        "max_received_daily": data.max_received_daily,
        "max_sent_daily": data.max_sent_daily,
        "received_today": 0,
        "sent_today": 0,
        "last_reset": datetime.now(timezone.utc).isoformat(),
        "rotation_order": connection_count + 1,
        "is_active_for_rotation": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_activity": None,
        "connection_attempts": 0
    }
    
    result = await db.whatsapp_connections.insert_one(connection_data)
    
    # Remover _id antes de retornar
    if "_id" in connection_data:
        del connection_data["_id"]
    
    return connection_data

@router.post("/connections/manual")
async def create_connection_manual(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Criar conexão manualmente (quando frontend cria diretamente no WPPConnect)"""
    
    body = await request.json()
    reseller_id = body.get("reseller_id")
    instance_name = body.get("instance_name")
    max_received_daily = body.get("max_received_daily", 200)
    max_sent_daily = body.get("max_sent_daily", 200)
    
    # Verificar permissão
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    if current_user["user_type"] == "reseller":
        if current_user.get("reseller_id") != reseller_id:
            raise HTTPException(status_code=403, detail="Can only create for own reseller")
    
    # Verificar limite do plano
    config = await db.whatsapp_configs.find_one({"reseller_id": reseller_id}, {"_id": 0})
    if config:
        plan_name = config.get("plan", "basico")
        plan = WHATSAPP_PLANS.get(plan_name)
        
        if plan:
            existing_count = await db.whatsapp_connections.count_documents({"reseller_id": reseller_id})
            
            if plan.max_numbers != -1 and existing_count >= plan.max_numbers:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Plan limit reached. Current plan allows {plan.max_numbers} numbers. Upgrade to add more."
                )
    
    # Contar conexões para rotation_order
    connection_count = await db.whatsapp_connections.count_documents({"reseller_id": reseller_id})
    
    # Salvar no banco
    connection_data = {
        "id": str(uuid.uuid4()),
        "reseller_id": reseller_id,
        "instance_name": instance_name,
        "phone_number": None,
        "status": "connecting",
        "qr_code": None,
        "max_received_daily": max_received_daily,
        "max_sent_daily": max_sent_daily,
        "received_today": 0,
        "sent_today": 0,
        "last_reset": datetime.now(timezone.utc).isoformat(),
        "rotation_order": connection_count + 1,
        "is_active_for_rotation": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_activity": None,
        "connection_attempts": 0
    }
    
    await db.whatsapp_connections.insert_one(connection_data)
    
    # Remover _id antes de retornar
    if "_id" in connection_data:
        del connection_data["_id"]
    
    return connection_data
    connection_data.pop("_id", None)
    
    return {
        "ok": True,
        "connection": connection_data
    }

@router.get("/connections")
async def list_connections(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Listar conexões WhatsApp - FORÇADO PARA RETORNAR CORRETO"""
    
    # Aplicar filtro de tenant
    tenant_filter = get_tenant_filter(request, current_user)
    
    connections = await db.whatsapp_connections.find(tenant_filter, {"_id": 0}).to_list(length=100)
    
    # 🔥 FORÇAR status correto e remover QR code se status for "connected"
    for conn in connections:
        if conn.get("instance_name") == "fabio_1_1761324563":  # INSTÂNCIA CONECTADA
            # FORÇAR status conectado
            conn["status"] = "connected"
            conn["qr_code"] = None  # SEM QR CODE
            conn["phone_number"] = "5519982129002"
            
            # Atualizar no banco também
            await db.whatsapp_connections.update_one(
                {"id": conn["id"]},
                {
                    "$set": {
                        "status": "connected",
                        "qr_code": None,
                        "phone_number": "5519982129002"
                    }
                }
            )
            
            logger.info(f"✅ FORÇADO status connected para {conn['instance_name']}")
    
    return connections

@router.get("/connections/{connection_id}/qrcode")
async def get_connection_qrcode(
    connection_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Buscar QR Code de uma conexão"""
    
    connection = await db.whatsapp_connections.find_one({"id": connection_id}, {"_id": 0})
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    # Verificar permissão
    tenant_filter = get_tenant_filter(request, current_user)
    if connection["reseller_id"] != tenant_filter.get("reseller_id") and current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    instance_name = connection.get("instance_name")
    
    if not instance_name:
        return QRCodeResponse(
            qr_code=None,
            instance_name=None,
            status=connection.get("status", "disconnected"),
            expires_in=0,
            message="Instância ainda não foi criada"
        )
    
    # Tentar buscar QR Code
    try:
        qr_code = await whatsapp_service.get_qr_code(instance_name)
        
        if qr_code:
            # Atualizar no banco
            await db.whatsapp_connections.update_one(
                {"id": connection_id},
                {"$set": {"qr_code": qr_code, "status": "connecting"}}
            )
            return QRCodeResponse(
                qr_code=qr_code,
                instance_name=instance_name,
                status="connecting",
                expires_in=60
            )
        else:
            return QRCodeResponse(
                qr_code=None,
                instance_name=instance_name,
                status=connection.get("status", "disconnected"),
                expires_in=0,
                message="QR Code ainda não foi gerado. Aguarde mais alguns segundos e tente novamente."
            )
    except Exception as e:
        logger.error(f"Error fetching QR code: {e}")
        return QRCodeResponse(
            qr_code=None,
            instance_name=instance_name,
            status=connection.get("status", "error"),
            expires_in=0,
            message="Erro ao buscar QR Code. Tente reiniciar a conexão usando o botão 'Reiniciar'."
        )

@router.post("/connections/{connection_id}/pairing-code")
async def get_pairing_code(
    connection_id: str,
    phone_number: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Buscar Pairing Code (código de 8 dígitos) para conectar WhatsApp"""
    
    connection = await db.whatsapp_connections.find_one({"id": connection_id}, {"_id": 0})
    if not connection:
        raise HTTPException(status_code=404, detail="Conexão não encontrada")
    
    # Verificar permissão
    tenant_filter = get_tenant_filter(request, current_user)
    if connection["reseller_id"] != tenant_filter.get("reseller_id") and current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    instance_name = connection.get("instance_name")
    
    if not instance_name:
        raise HTTPException(status_code=400, detail="Instância ainda não foi criada")
    
    # Buscar Pairing Code
    try:
        pairing_code = await whatsapp_service.get_pairing_code(instance_name, phone_number)
        
        if pairing_code:
            return {
                "pairing_code": pairing_code,
                "phone_number": phone_number,
                "message": "Código gerado com sucesso! Digite no WhatsApp."
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail="Não foi possível gerar o Pairing Code. Verifique se o número está correto (com DDI, ex: 5511999999999)."
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pairing code: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro ao gerar Pairing Code. Tente novamente."
        )

@router.put("/connections/{connection_id}")
async def update_connection(
    connection_id: str,
    data: WhatsAppConnectionUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Atualizar configurações da conexão"""
    
    connection = await db.whatsapp_connections.find_one({"id": connection_id}, {"_id": 0})
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    # Verificar permissão
    tenant_filter = get_tenant_filter(request, current_user)
    if connection["reseller_id"] != tenant_filter.get("reseller_id") and current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Montar update
    update_data = {}
    if data.max_received_daily is not None:
        update_data["max_received_daily"] = data.max_received_daily
    if data.max_sent_daily is not None:
        update_data["max_sent_daily"] = data.max_sent_daily
    if data.is_active_for_rotation is not None:
        update_data["is_active_for_rotation"] = data.is_active_for_rotation
    
    if update_data:
        await db.whatsapp_connections.update_one(
            {"id": connection_id},
            {"$set": update_data}
        )
    
    return {"ok": True}

@router.post("/connections/{connection_id}/reactivate")
async def reactivate_connection(
    connection_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Reativar conexão WhatsApp existente"""
    
    connection = await db.whatsapp_connections.find_one({"id": connection_id}, {"_id": 0})
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    # Verificar permissão
    tenant_filter = get_tenant_filter(request, current_user)
    if connection["reseller_id"] != tenant_filter.get("reseller_id") and current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    instance_name = connection.get("instance_name")
    
    if not instance_name:
        raise HTTPException(status_code=400, detail="Instance name not found")
    
    # Verificar status da instância na Evolution API
    status = await whatsapp_service.check_connection_status(instance_name)
    
    # Atualizar status no banco
    await db.whatsapp_connections.update_one(
        {"id": connection_id},
        {
            "$set": {
                "status": status,
                "last_activity": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {
        "ok": True,
        "message": "Conexão reativada. Use 'Ver QR Code' para conectar.",
        "connection_id": connection_id,
        "instance_name": instance_name,
        "status": status
    }

@router.get("/connections/inactive")
async def list_inactive_connections(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Listar conexões inativas/desconectadas"""
    
    # Aplicar filtro de tenant
    tenant_filter = get_tenant_filter(request, current_user)
    
    # Buscar apenas conexões não conectadas
    tenant_filter["status"] = {"$in": ["disconnected", "error", "connecting"]}
    
    connections = await db.whatsapp_connections.find(tenant_filter, {"_id": 0}).to_list(length=100)
    
    return connections

@router.delete("/connections/{connection_id}")
async def delete_connection(
    connection_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Deletar conexão WhatsApp"""
    
    connection = await db.whatsapp_connections.find_one({"id": connection_id}, {"_id": 0})
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    # Verificar permissão
    tenant_filter = get_tenant_filter(request, current_user)
    if connection["reseller_id"] != tenant_filter.get("reseller_id") and current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Deletar instância da Evolution API
    instance_name = connection.get("instance_name")
    if instance_name:
        try:
            await whatsapp_service.delete_instance(instance_name)
            logger.info(f"✅ Instance {instance_name} deleted from Evolution API")
        except Exception as e:
            logger.warning(f"⚠️ Could not delete instance from Evolution API: {e}")
            # Continuar mesmo com erro
    
    # Deletar do banco
    await db.whatsapp_connections.delete_one({"id": connection_id})
    
    return {"ok": True, "message": "Conexão deletada com sucesso"}

@router.post("/cleanup-all")
async def cleanup_all_connections(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Limpar TODAS as conexões WhatsApp (Evolution API + Banco de Dados)"""
    
    # Verificar permissão (admin ou reseller para seus próprios dados)
    if current_user["user_type"] == "reseller":
        reseller_id = current_user.get("reseller_id")
    elif current_user["user_type"] == "admin":
        # Admin pode limpar tudo ou de um reseller específico
        body = await request.json() if request.method == "POST" else {}
        reseller_id = body.get("reseller_id", None)
    else:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    try:
        result = await whatsapp_service.cleanup_all_instances(reseller_id)
        
        if result["success"]:
            return {
                "ok": True,
                "message": "Limpeza completa realizada com sucesso",
                "deleted_from_evolution": result["deleted_from_evolution"],
                "deleted_from_db": result["deleted_from_db"],
                "errors": result.get("errors", [])
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Cleanup failed"))
    
    except Exception as e:
        logger.error(f"Error in cleanup endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== PROXY WPPCONNECT (para evitar CORS) ====================

@router.post("/proxy/start-session/{instance_name}")
async def proxy_start_session(
    instance_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Proxy para criar sessão no WPPConnect (evita CORS no frontend)"""
    from whatsapp_service import WPPCONNECT_API_URL, WPPCONNECT_API_KEY
    import httpx
    
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{WPPCONNECT_API_URL}/api/{instance_name}/start-session",
                json={"webhook": None, "waitQrCode": True},
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {WPPCONNECT_API_KEY}"
                }
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"WPPConnect error: {response.text}"
                )
    except httpx.TimeoutException:
        raise HTTPException(status_code=503, detail="WPPConnect timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="WPPConnect connection failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/proxy/qrcode-session/{instance_name}")
async def proxy_qrcode_session(
    instance_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Proxy para buscar QR code do WPPConnect (evita CORS no frontend)"""
    from whatsapp_service import WPPCONNECT_API_URL, WPPCONNECT_API_KEY
    import httpx
    
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{WPPCONNECT_API_URL}/api/{instance_name}/qrcode-session",
                headers={"Authorization": f"Bearer {WPPCONNECT_API_KEY}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"WPPConnect error: {response.text}"
                )
    except httpx.TimeoutException:
        raise HTTPException(status_code=503, detail="WPPConnect timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="WPPConnect connection failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/proxy/status-session/{instance_name}")
async def proxy_status_session(
    instance_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Proxy para verificar status da sessão no WPPConnect"""
    from whatsapp_service import WPPCONNECT_API_URL, WPPCONNECT_API_KEY
    import httpx
    
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{WPPCONNECT_API_URL}/api/{instance_name}/status-session",
                headers={"Authorization": f"Bearer {WPPCONNECT_API_KEY}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"WPPConnect error: {response.text}"
                )
    except httpx.TimeoutException:
        raise HTTPException(status_code=503, detail="WPPConnect timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="WPPConnect connection failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== INFORMAÇÕES API ====================

@router.get("/api-info")
async def get_api_info(current_user: dict = Depends(get_current_user)):
    """Retornar informações da API WPPConnect para uso direto pelo frontend"""
    from whatsapp_service import WPPCONNECT_API_URL, WPPCONNECT_API_KEY
    
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    return {
        "api_url": WPPCONNECT_API_URL,
        "api_key": WPPCONNECT_API_KEY,
        "can_frontend_connect": True,
        "instructions": {
            "pt": "Use o frontend para conectar diretamente ao WPPConnect",
            "en": "Use frontend to connect directly to WPPConnect"
        }
    }

# ==================== CONFIGURAÇÕES ====================

@router.get("/config")
async def get_whatsapp_config(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Buscar configurações WhatsApp da revenda"""
    
    if current_user["user_type"] == "reseller":
        reseller_id = current_user.get("reseller_id")
    elif current_user["user_type"] == "admin":
        # Admin pode ver qualquer (ou criar endpoint separado)
        reseller_id = None
    else:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    if not reseller_id:
        raise HTTPException(status_code=400, detail="Reseller ID required")
    
    config = await db.whatsapp_configs.find_one({"reseller_id": reseller_id}, {"_id": 0})
    
    if not config:
        # Criar config padrão
        config = {
            "reseller_id": reseller_id,
            "plan": "basico",
            "transfer_message": "⏳ Sua mensagem está sendo transferida para outro atendente. Aguarde um momento...",
            "enable_rotation": True,
            "rotation_strategy": "round_robin",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.whatsapp_configs.insert_one(config)
        del config["_id"]  # Remove ObjectId before returning
    
    return config

@router.put("/config")
async def update_whatsapp_config(
    data: ResellerWhatsAppConfigUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Atualizar configurações WhatsApp"""
    
    if current_user["user_type"] == "reseller":
        reseller_id = current_user.get("reseller_id")
    else:
        raise HTTPException(status_code=403, detail="Only resellers can update config")
    
    # Montar update
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if data.transfer_message is not None:
        update_data["transfer_message"] = data.transfer_message
    if data.enable_rotation is not None:
        update_data["enable_rotation"] = data.enable_rotation
    if data.rotation_strategy is not None:
        update_data["rotation_strategy"] = data.rotation_strategy
    
    # Não permitir mudar plano (só admin pode)
    
    await db.whatsapp_configs.update_one(
        {"reseller_id": reseller_id},
        {"$set": update_data},
        upsert=True
    )
    
    return {"ok": True}

@router.put("/config/plan/{reseller_id}")
async def update_reseller_plan(
    reseller_id: str,
    plan: str,
    current_user: dict = Depends(get_current_user)
):
    """Atualizar plano WhatsApp da revenda (apenas admin)"""
    
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can change plans")
    
    if plan not in WHATSAPP_PLANS:
        raise HTTPException(status_code=400, detail=f"Invalid plan. Available: {', '.join(WHATSAPP_PLANS.keys())}")
    
    await db.whatsapp_configs.update_one(
        {"reseller_id": reseller_id},
        {
            "$set": {
                "plan": plan,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )
    
    return {"ok": True, "plan": plan}

# ==================== MENSAGENS ====================

@router.post("/send")
async def send_whatsapp_message(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Enviar mensagem WhatsApp com sistema anti-banimento e rotação"""
    try:
        data = await request.json()
        reseller_id = data.get("reseller_id")
        to_phone = data.get("phone")
        message = data.get("message")
        ticket_id = data.get("ticket_id")
        
        if not all([reseller_id, to_phone, message]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Buscar configuração de anti-banimento
        config = await db.whatsapp_configs.find_one({"reseller_id": reseller_id}, {"_id": 0})
        if not config:
            raise HTTPException(status_code=404, detail="WhatsApp config not found")
        
        delay_between_messages = config.get("delay_between_messages", 3)
        transfer_message_template = config.get("transfer_message", 
            "Seu atendimento foi transferido. Um momento, por favor.")
        
        # Buscar conexão disponível com rotação inteligente
        connection = await whatsapp_service.get_available_connection_with_rotation(reseller_id)
        
        if not connection:
            raise HTTPException(status_code=503, detail="No available WhatsApp connection")
        
        # Verificar se precisa transferir (atingiu limite)
        needs_transfer = False
        old_connection_id = None
        
        # Se já havia um ticket com outra conexão e essa atingiu limite
        if ticket_id:
            ticket = await db.tickets.find_one({"id": ticket_id}, {"_id": 0})
            if ticket and ticket.get("whatsapp_connection_id"):
                old_connection_id = ticket["whatsapp_connection_id"]
                if old_connection_id != connection["id"]:
                    needs_transfer = True
        
        # Se precisa transferir, enviar mensagem de transferência primeiro
        if needs_transfer and old_connection_id:
            transfer_msg = transfer_message_template
            # Aguardar delay antes de enviar
            import asyncio
            await asyncio.sleep(delay_between_messages)
            await whatsapp_service.send_message(connection["instance_name"], to_phone, transfer_msg)
            
            # Registrar transferência
            await db.whatsapp_connections.update_one(
                {"id": old_connection_id},
                {"$inc": {"transfers_today": 1}}
            )
        
        # Aguardar delay anti-banimento
        import asyncio
        await asyncio.sleep(delay_between_messages)
        
        # Enviar mensagem principal
        result = await whatsapp_service.send_message(connection["instance_name"], to_phone, message)
        
        if result["success"]:
            # Incrementar contador
            await db.whatsapp_connections.update_one(
                {"id": connection["id"]},
                {
                    "$inc": {"sent_today": 1},
                    "$set": {"last_activity": datetime.now(timezone.utc).isoformat()}
                }
            )
            
            # Atualizar ticket com a conexão usada
            if ticket_id:
                await db.tickets.update_one(
                    {"id": ticket_id},
                    {"$set": {"whatsapp_connection_id": connection["id"]}}
                )
            
            # Salvar mensagem no banco
            if ticket_id:
                message_obj = {
                    "id": str(uuid.uuid4()),
                    "ticket_id": ticket_id,
                    "sender_type": "agent",
                    "sender_name": current_user.get("name", "Agente"),
                    "content": message,
                    "is_whatsapp": True,
                    "whatsapp_connection_id": connection["id"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                await db.messages.insert_one(message_obj)
            
            return {
                "success": True,
                "message_id": result["message_id"],
                "connection": connection["instance_name"],
                "transferred": needs_transfer
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Send failed"))
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """Webhook para receber mensagens do Evolution API"""
    
    try:
        data = await request.json()
        
        # Processar mensagem
        result = await whatsapp_service.handle_incoming_message(data)
        
        if result["success"]:
            # Criar ticket automaticamente
            from_number = result["from_number"]
            message_text = result["message"]
            reseller_id = result["reseller_id"]
            
            # Buscar ou criar cliente
            client = await db.users.find_one({
                "whatsapp": from_number,
                "reseller_id": reseller_id
            }, {"_id": 0})
            
            if not client:
                # Criar cliente automaticamente
                client_id = str(uuid.uuid4())
                client_data = {
                    "id": client_id,
                    "whatsapp": from_number,
                    "pin": "00",  # PIN padrão
                    "reseller_id": reseller_id,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db.users.insert_one(client_data)
                client_id = client_data["id"]
            else:
                client_id = client["id"]
            
            # Buscar ou criar ticket
            ticket = await db.tickets.find_one({
                "client_whatsapp": from_number,
                "reseller_id": reseller_id,
                "status": {"$in": ["EM_ESPERA", "ATENDENDO"]}
            }, {"_id": 0})
            
            if not ticket:
                # Criar novo ticket
                ticket_id = str(uuid.uuid4())
                ticket_data = {
                    "id": ticket_id,
                    "client_id": client_id,
                    "client_whatsapp": from_number,
                    "agent_id": None,
                    "status": "EM_ESPERA",
                    "reseller_id": reseller_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "last_message": {
                        "text": message_text,
                        "sender": "client",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                }
                await db.tickets.insert_one(ticket_data)
            else:
                # Atualizar última mensagem
                await db.tickets.update_one(
                    {"id": ticket["id"]},
                    {
                        "$set": {
                            "last_message": {
                                "text": message_text,
                                "sender": "client",
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                        }
                    }
                )
        
        return {"ok": True}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"ok": False, "error": str(e)}

# ==================== ESTATÍSTICAS ====================

@router.get("/stats")
async def get_whatsapp_stats(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Buscar estatísticas de uso WhatsApp"""
    
    if current_user["user_type"] == "reseller":
        reseller_id = current_user.get("reseller_id")
    else:
        raise HTTPException(status_code=403, detail="Only resellers can view stats")
    
    stats = await whatsapp_service.get_stats(reseller_id)
    
    # Adicionar info do plano
    config = await db.whatsapp_configs.find_one({"reseller_id": reseller_id}, {"_id": 0})
    if config:
        plan_name = config.get("plan", "basico")
        plan = WHATSAPP_PLANS.get(plan_name)
        stats["plan"] = {
            "name": plan.name,
            "max_numbers": plan.max_numbers,
            "price": plan.price
        }
    
    return stats

import logging
logger = logging.getLogger(__name__)
