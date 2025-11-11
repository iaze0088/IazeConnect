"""
Rotas WhatsApp Evolution API
Sistema completo de gerenciamento e rotação
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List
import uuid
import os
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
    """Processar atualização de status da conexão - v2.2.3"""
    try:
        # Na v2.2.3, 'instance' é uma STRING com o nome da instância
        # e 'data' contém as informações do estado
        instance_name = data.get("instance")  # STRING diretamente
        connection_data = data.get("data", {})  # Objeto com state e statusReason
        state = connection_data.get("state")  # open, close, connecting
        
        if not instance_name:
            return {"success": False, "error": "No instance name"}
        
        # Mapear estados Evolution API para IAZE
        status_map = {
            "open": "connected",
            "close": "disconnected",
            "connecting": "connecting"
        }
        
        iaze_status = status_map.get(state, "disconnected")
        
        # Atualizar status no banco
        result = await db.whatsapp_connections.update_one(
            {"instance_name": instance_name},
            {
                "$set": {
                    "status": iaze_status,
                    "connected": (state == "open"),
                    "last_activity": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        if result.modified_count > 0:
            print(f"✅ Status atualizado: {instance_name} -> {iaze_status}")
        
        return {"success": True, "instance": instance_name, "status": iaze_status}
        
    except Exception as e:
        print(f"❌ Erro ao processar connection.update: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

async def process_evolution_message(data):
    """Processar mensagem recebida da Evolution API - VERSÃO MELHORADA COM LOGS"""
    print("=" * 80)
    print("🔔 WEBHOOK RECEBIDO - INICIANDO PROCESSAMENTO")
    print("=" * 80)
    
    try:
        instance_name = data.get("instance")
        print(f"📍 Instance: {instance_name}")
        
        # Evolution API envia dados em formato diferente
        message_data = data.get("data", {})
        print(f"📦 Message Data Keys: {list(message_data.keys())}")
        
        # Extrair informações da mensagem
        message_key = message_data.get("key", {})
        message_content = message_data.get("message", {})
        push_name = message_data.get("pushName", "")
        
        print(f"🔑 Message Key: {message_key}")
        print(f"📝 Message Content Keys: {list(message_content.keys())}")
        print(f"👤 Push Name: {push_name}")
        
        # Extrair número do remetente
        remote_jid = message_key.get("remoteJid", "")
        phone = remote_jid.replace("@s.whatsapp.net", "").replace("@c.us", "")
        
        print(f"📱 Remote JID: {remote_jid}")
        print(f"📞 Phone Number: {phone}")
        
        # Verificar se é mensagem do próprio bot (ignorar)
        if message_key.get("fromMe"):
            print("⚠️ Mensagem própria detectada - IGNORANDO")
            return {"success": True, "message": "Own message ignored"}
        
        # Extrair texto da mensagem
        message_text = (
            message_content.get("conversation") or 
            message_content.get("extendedTextMessage", {}).get("text") or 
            ""
        )
        
        print(f"💬 Message Text: {message_text[:100]}..." if len(message_text) > 100 else f"💬 Message Text: {message_text}")
        
        # VALIDAÇÃO ROBUSTA
        if not instance_name:
            print("❌ ERRO: instance_name está vazio!")
            return {"success": False, "error": "Missing instance_name"}
            
        if not phone or not message_text:
            print(f"❌ ERRO: Dados incompletos detectados!")
            print(f"   - Phone válido: {bool(phone)}")
            print(f"   - Message válida: {bool(message_text)}")
            return {"success": False, "error": "Invalid message data"}
        
        print(f"✅ Validação inicial passou - Processando mensagem de {push_name} ({phone})")
        
        # Buscar conexão WhatsApp
        print(f"🔍 Buscando conexão WhatsApp: {instance_name}")
        connection = await db.whatsapp_connections.find_one({
            "instance_name": instance_name
        }, {"_id": 0})
        
        if not connection:
            print(f"❌ ERRO CRÍTICO: Conexão não encontrada para instance: {instance_name}")
            print(f"   Verificar se a instância está cadastrada no banco de dados!")
            return {"success": False, "error": "Connection not found"}
        
        print(f"✅ Conexão encontrada: ID={connection.get('id')}, Reseller={connection.get('reseller_id')}")
        reseller_id = connection["reseller_id"]
        
        # Buscar ou criar departamento automático (para backup/fallback)
        dept_name = f"WHATSAPP {connection.get('rotation_order', 1)}"
        print(f"🏢 Buscando/criando departamento automático: {dept_name}")
        
        department = await db.departments.find_one({
            "reseller_id": reseller_id,
            "name": dept_name,
            "origin": "whatsapp_starter"
        }, {"_id": 0})
        
        if not department:
            print(f"⚠️ Departamento não existe - CRIANDO novo")
            department = {
                "id": str(uuid.uuid4()),
                "reseller_id": reseller_id,
                "name": dept_name,
                "description": f"Atendimento WhatsApp - Número {connection.get('rotation_order', 1)}",
                "origin": "whatsapp_starter",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            result = await db.departments.insert_one(department)
            print(f"✅ Departamento criado: {department['id']}")
        else:
            print(f"✅ Departamento encontrado: {department['id']}")
        
        # Buscar ou criar cliente
        sender_name = push_name or phone
        print(f"👤 Buscando/criando cliente: {sender_name} ({phone})")
        
        client = await db.clients.find_one({
            "reseller_id": reseller_id,
            "phone": phone
        }, {"_id": 0})
        
        if not client:
            print(f"⚠️ Cliente não existe - CRIANDO novo")
            client = {
                "id": str(uuid.uuid4()),
                "reseller_id": reseller_id,
                "name": sender_name,
                "email": f"{phone}@whatsapp.temp",
                "phone": phone,
                "whatsapp_origin": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            result = await db.clients.insert_one(client)
            print(f"✅ Cliente criado: {client['id']}")
        else:
            print(f"✅ Cliente encontrado: {client['id']}")
        
        # Buscar ticket aberto
        print(f"🎫 Buscando ticket aberto para cliente: {client['id']}")
        open_ticket = await db.tickets.find_one({
            "reseller_id": reseller_id,
            "client_id": client["id"],
            "status": "open"
        }, {"_id": 0})
        
        if not open_ticket:
            ticket_id = str(uuid.uuid4())
            print(f"⚠️ Ticket não existe - CRIANDO novo: {ticket_id}")
            ticket = {
                "id": ticket_id,
                "reseller_id": reseller_id,
                "client_id": client["id"],
                "client_name": client["name"],
                "client_phone": phone,
                "client_whatsapp": phone,
                "department_id": None,  # SEM departamento ainda - cliente escolhe
                "department_name": None,
                "subject": f"WhatsApp de {sender_name}",
                "status": "open",
                "priority": "medium",
                "agent_id": None,
                "whatsapp_origin": True,
                "whatsapp_connection_id": connection["id"],
                "whatsapp_instance": instance_name,  # Nome da instância
                "ticket_origin": "whatsapp_starter",  # ORIGEM: WhatsApp Starter
                "awaiting_department_choice": True,  # Aguardando escolha do cliente
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            try:
                result = await db.tickets.insert_one(ticket)
                if result.inserted_id:
                    print(f"✅ Ticket criado com sucesso! Inserted ID: {result.inserted_id}")
                    
                    # **ENVIAR SELEÇÃO DE DEPARTAMENTO PARA O CLIENTE**
                    from server import send_department_selection
                    await send_department_selection(
                        ticket_id=ticket_id,
                        client_id=client["id"],
                        reseller_id=reseller_id,
                        ticket_origin="whatsapp_starter"
                    )
                    print(f"✅ Mensagem de seleção de departamento enviada!")
                else:
                    print(f"❌ ERRO: insert_one não retornou inserted_id!")
            except Exception as insert_error:
                print(f"❌ ERRO CRÍTICO ao inserir ticket no banco: {insert_error}")
                import traceback
                traceback.print_exc()
                raise
        else:
            ticket_id = open_ticket["id"]
            print(f"✅ Ticket existente encontrado: {ticket_id}")
        
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
        print(f"💾 Salvando mensagem no ticket: {ticket_id}")
        result = await db.messages.insert_one(message_obj)
        print(f"✅ Mensagem salva: {message_obj['id']}")
        
        # **ENVIAR VIA WEBSOCKET PARA AGENTES EM TEMPO REAL**
        try:
            from server import manager
            await manager.broadcast_to_agents({
                "type": "new_message",
                "ticket_id": ticket_id,
                "message": {
                    "id": message_obj["id"],
                    "ticket_id": ticket_id,
                    "from_type": "client",
                    "from_id": client["id"],
                    "text": message_text,
                    "kind": "text",
                    "created_at": message_obj["timestamp"]
                }
            })
            print(f"✅ Notificação WebSocket enviada para agentes!")
        except Exception as ws_error:
            print(f"⚠️ Erro ao enviar WebSocket (não crítico): {ws_error}")
        
        # Incrementar contador
        print(f"📊 Atualizando contadores da conexão")
        await db.whatsapp_connections.update_one(
            {"id": connection["id"]},
            {
                "$inc": {"received_today": 1},
                "$set": {"last_activity": datetime.now(timezone.utc).isoformat()}
            }
        )
        
        print(f"=" * 80)
        print(f"🎉 SUCESSO TOTAL!")
        print(f"✅ Ticket ID: {ticket_id}")
        print(f"✅ Departamento: {dept_name}")
        print(f"✅ Cliente: {client['name']} ({phone})")
        print(f"✅ Mensagem salva e pronta para visualização no dashboard!")
        print(f"=" * 80)
        
        return {"success": True, "ticket_id": ticket_id, "department": dept_name}
        
    except Exception as e:
        print(f"=" * 80)
        print(f"❌❌❌ ERRO CRÍTICO NO PROCESSAMENTO ❌❌❌")
        print(f"Erro: {e}")
        print(f"=" * 80)
        import traceback
        traceback.print_exc()
        print(f"=" * 80)
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
    """Criar nova conexão WhatsApp"""
    
    try:
        print(f"🔧 [DEBUG] create_connection chamado")
        print(f"🔧 [DEBUG] current_user: {current_user}")
        print(f"🔧 [DEBUG] data.reseller_id (antes): {data.reseller_id}")
        
        # Verificar permissão (admin ou próprio reseller)
        if current_user["user_type"] not in ["admin", "reseller"]:
            print(f"❌ [DEBUG] Permission denied - user_type: {current_user['user_type']}")
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # Se reseller_id não fornecido, extrair do token ou usar None para admin master
        if not data.reseller_id:
            if current_user["user_type"] == "reseller":
                data.reseller_id = current_user.get("reseller_id")
            elif current_user["user_type"] == "admin":
                # Admin master pode criar conexão sem reseller_id (para uso próprio)
                data.reseller_id = current_user.get("reseller_id")  # None para admin master
            else:
                raise HTTPException(status_code=400, detail="reseller_id required")
        
        print(f"🔧 [DEBUG] data.reseller_id (depois): {data.reseller_id}")
        
        # Verificar se reseller está tentando criar para outro reseller
        if current_user["user_type"] == "reseller":
            if current_user.get("reseller_id") != data.reseller_id:
                raise HTTPException(status_code=403, detail="Can only create for own reseller")
        
        # Verificar limite do plano (não aplicável para admin master)
        if data.reseller_id:  # Apenas verificar se não for admin master
            config = await db.whatsapp_configs.find_one({"reseller_id": data.reseller_id}, {"_id": 0})
            if config:
                plan_name = config.get("plan", "basico")
                plan = WHATSAPP_PLANS.get(plan_name)
                
                if plan:
                    existing_count = await db.whatsapp_connections.count_documents({
                        "reseller_id": data.reseller_id
                    })
                    
                    if plan.max_numbers != -1 and existing_count >= plan.max_numbers:
                        raise HTTPException(
                            status_code=400, 
                            detail=f"Limite do plano atingido. Plano atual permite {plan.max_numbers} números. Faça upgrade para adicionar mais."
                        )
        
        # Gerar nome único da instância (com timestamp)
        # Se for admin master (reseller_id = None), usar "admin" como nome base
        if data.reseller_id:
            reseller = await db.resellers.find_one({"id": data.reseller_id}, {"_id": 0})
            if not reseller:
                raise HTTPException(status_code=404, detail="Revenda não encontrada")
            instance_base_name = reseller.get("custom_domain", f"reseller_{data.reseller_id[:8]}")
        else:
            # Admin master
            instance_base_name = "admin"
        
        connection_count = await db.whatsapp_connections.count_documents({"reseller_id": data.reseller_id})
        
        from datetime import datetime
        timestamp = int(datetime.now().timestamp())
        
        # Criar nome base da instância
        if data.reseller_id and reseller:
            base_name = reseller['name'].lower().replace(' ', '').replace('-', '')[:10]
        else:
            # Admin master
            base_name = "admin"
        
        instance_name = f"{base_name}_{connection_count + 1}_{timestamp}"
        
        print(f"🆕 Criando nova instância: {instance_name}")
        
        # Criar instância na Evolution API
        result = await whatsapp_service.create_instance(data.reseller_id, instance_name)
        
        if not result["success"]:
            error_msg = result.get("error", "Erro desconhecido ao criar instância")
            print(f"❌ Erro ao criar instância: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Erro na Evolution API: {error_msg}")
        
        print(f"✅ Instância criada na Evolution API: {instance_name}")
        
        # Extrair dados da resposta
        evolution_data = result.get("data", {})
        
        # Garantir que evolution_data é um dict
        if isinstance(evolution_data, str):
            import json
            try:
                evolution_data = json.loads(evolution_data)
            except:
                evolution_data = {}
        
        instance_info = evolution_data.get("instance", {}) if isinstance(evolution_data, dict) else {}
        qr_info = evolution_data.get("qrcode", {}) or evolution_data.get("qr", {}) if isinstance(evolution_data, dict) else {}
        
        # Pegar API Key
        api_key = None
        if isinstance(instance_info, dict):
            api_key = instance_info.get("apikey")
        if not api_key and isinstance(evolution_data, dict):
            hash_data = evolution_data.get("hash", {})
            if isinstance(hash_data, dict):
                api_key = hash_data.get("apikey")
        
        # Buscar QR Code via endpoint /instance/connect
        qr_code = None
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                qr_response = await client.get(
                    f"{os.environ.get('EVOLUTION_API_URL')}/instance/connect/{instance_name}",
                    headers={"apikey": os.environ.get('EVOLUTION_API_KEY')}
                )
                if qr_response.status_code == 200:
                    qr_data = qr_response.json()
                    qr_code = qr_data.get('base64') or qr_data.get('code')
                    print(f"✅ QR Code obtido via /connect ({len(qr_code) if qr_code else 0} chars)")
        except Exception as e:
            print(f"⚠️ Erro ao buscar QR Code: {e}")
        
        print(f"📝 QR Code: {'✅ Recebido' if qr_code else '❌ Não recebido'}")
        print(f"📝 API Key: {'✅ Recebido' if api_key else '❌ Não recebido'}")
        
        # Salvar no banco
        connection_data = {
            "id": str(uuid.uuid4()),
            "reseller_id": data.reseller_id,
            "instance_name": instance_name,
            "phone_number": None,
            "status": "connecting",
            "qr_code": qr_code,
            "api_key": api_key,
            "max_received_daily": data.max_received_daily,
            "max_sent_daily": data.max_sent_daily,
            "received_today": 0,
            "sent_today": 0,
            "last_reset": datetime.now(timezone.utc).isoformat(),
            "rotation_order": connection_count + 1,
            "is_active_for_rotation": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_activity": datetime.now(timezone.utc).isoformat(),
            "connection_attempts": 0,
            "connected": False,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.whatsapp_connections.insert_one(connection_data)
        print(f"✅ Conexão salva no banco: {connection_data['id']}")
        
        # Remover _id antes de retornar
        connection_data.pop("_id", None)
        
        return connection_data
    
    except HTTPException:
        # Re-raise HTTPException para manter status code e detail
        raise
    except Exception as e:
        # Capturar qualquer outro erro e logar
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ ERRO CRÍTICO ao criar conexão WhatsApp:")
        print(error_trace)
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao criar conexão WhatsApp: {str(e)}"
        )

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
    """Listar conexões WhatsApp"""
    
    # Aplicar filtro de tenant
    tenant_filter = get_tenant_filter(request, current_user)
    
    connections = await db.whatsapp_connections.find(tenant_filter, {"_id": 0}).to_list(length=100)
    
    return connections

@router.post("/connections/sync")
async def sync_evolution_instances(
    current_user: dict = Depends(get_current_user)
):
    """🔥 SINCRONIZAÇÃO ROBUSTA - Limpa órfãs e sincroniza tudo"""
    
    try:
        import httpx
        
        evolution_url = os.environ.get("EVOLUTION_API_URL", "http://evolution.suporte.help:8080")
        evolution_key = os.environ.get("EVOLUTION_API_KEY", "iaze-evolution-2025-secure-key")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1. Buscar instâncias na Evolution API
            response = await client.get(
                f"{evolution_url}/instance/fetchInstances",
                headers={"apikey": evolution_key}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Erro ao buscar instâncias da Evolution API")
            
            evolution_instances = response.json()
            evolution_instance_names = set()
            evolution_map = {}
            
            # Mapear instâncias Evolution com seus estados
            for inst in evolution_instances:
                inst_data = inst.get('instance', {})
                inst_name = inst_data.get('instanceName')
                
                if inst_name:
                    evolution_instance_names.add(inst_name)
                    
                    # Verificar connectionState
                    state_response = await client.get(
                        f"{evolution_url}/instance/connectionState/{inst_name}",
                        headers={"apikey": evolution_key}
                    )
                    
                    state = "disconnected"
                    if state_response.status_code == 200:
                        state_data = state_response.json()
                        raw_state = state_data.get('instance', {}).get('state', '').lower()
                        if raw_state == 'open':
                            state = "connected"
                        elif raw_state == 'connecting':
                            state = "connecting"
                    
                    evolution_map[inst_name] = {
                        'status': state,
                        'api_key': inst_data.get('apikey', evolution_key)
                    }
            
            # 2. Buscar conexões no banco IAZE
            iaze_connections = await db.whatsapp_connections.find({}, {"_id": 0}).to_list(length=100)
            iaze_instance_names = {conn['instance_name'] for conn in iaze_connections}
            
            # 3. LIMPAR conexões órfãs
            orphaned = iaze_instance_names - evolution_instance_names
            if orphaned:
                await db.whatsapp_connections.delete_many({"instance_name": {"$in": list(orphaned)}})
            
            # 4. ADICIONAR instâncias faltantes
            missing = evolution_instance_names - iaze_instance_names
            for inst_name in missing:
                evo_data = evolution_map.get(inst_name, {})
                status = evo_data.get('status', 'disconnected')
                api_key = evo_data.get('api_key', evolution_key)
                
                reseller_id = current_user.get("id", "admin")
                
                new_connection = {
                    "id": str(uuid.uuid4()),
                    "reseller_id": reseller_id,
                    "instance_name": inst_name,
                    "phone_number": None,
                    "status": status,
                    "qr_code": None,
                    "api_key": api_key,
                    "max_received_daily": 200,
                    "max_sent_daily": 200,
                    "received_today": 0,
                    "sent_today": 0,
                    "last_reset": datetime.now(timezone.utc).isoformat(),
                    "rotation_order": 1,
                    "is_active_for_rotation": True,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "last_activity": datetime.now(timezone.utc).isoformat(),
                    "connection_attempts": 0,
                    "connected": status == "connected",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                
                await db.whatsapp_connections.insert_one(new_connection)
            
            # 5. ATUALIZAR status das existentes
            updated = 0
            for inst_name in evolution_instance_names & iaze_instance_names:
                evo_data = evolution_map.get(inst_name, {})
                new_status = evo_data.get('status', 'disconnected')
                
                current = next((c for c in iaze_connections if c['instance_name'] == inst_name), None)
                
                if current and current.get('status') != new_status:
                    await db.whatsapp_connections.update_one(
                        {"instance_name": inst_name},
                        {
                            "$set": {
                                "status": new_status,
                                "connected": new_status == "connected",
                                "last_activity": datetime.now(timezone.utc).isoformat(),
                                "updated_at": datetime.now(timezone.utc).isoformat()
                            }
                        }
                    )
                    updated += 1
            
            return {
                "success": True,
                "removed": len(orphaned),
                "added": len(missing),
                "updated": updated,
                "message": f"✅ Sincronizado: {len(orphaned)} removidas, {len(missing)} adicionadas, {updated} atualizadas"
            }
            
    except Exception as e:
        print(f"❌ Erro na sincronização: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/connections/{connection_id}/refresh-qr")
async def refresh_qr_code(
    connection_id: str,
    current_user: dict = Depends(get_current_user)
):
    """🔄 Gerar novo QR Code para uma conexão"""
    
    try:
        # Buscar conexão
        connection = await db.whatsapp_connections.find_one({"id": connection_id}, {"_id": 0})
        
        if not connection:
            raise HTTPException(status_code=404, detail="Conexão não encontrada")
        
        instance_name = connection['instance_name']
        evolution_url = os.environ.get("EVOLUTION_API_URL", "http://evolution.suporte.help:8080")
        evolution_key = os.environ.get("EVOLUTION_API_KEY", "iaze-evolution-2025-secure-key")
        
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Buscar novo QR Code
            qr_response = await client.get(
                f"{evolution_url}/instance/connect/{instance_name}",
                headers={"apikey": evolution_key}
            )
            
            if qr_response.status_code == 200:
                qr_data = qr_response.json()
                new_qr = qr_data.get('base64') or qr_data.get('code')
                
                if new_qr:
                    # Atualizar no banco
                    await db.whatsapp_connections.update_one(
                        {"id": connection_id},
                        {
                            "$set": {
                                "qr_code": new_qr,
                                "updated_at": datetime.now(timezone.utc).isoformat()
                            }
                        }
                    )
                    
                    return {
                        "success": True,
                        "qr_code": new_qr,
                        "message": "✅ Novo QR Code gerado"
                    }
                else:
                    raise HTTPException(status_code=500, detail="QR Code não encontrado na resposta")
            else:
                raise HTTPException(status_code=500, detail=f"Erro ao buscar QR Code: {qr_response.status_code}")
                
    except Exception as e:
        print(f"❌ Erro ao gerar novo QR Code: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/connections/{connection_id}/restart-session")
async def restart_session(
    connection_id: str,
    current_user: dict = Depends(get_current_user)
):
    """🔄 Reiniciar sessão WhatsApp (deletar e recriar instância)"""
    
    try:
        # Buscar conexão
        connection = await db.whatsapp_connections.find_one({"id": connection_id}, {"_id": 0})
        
        if not connection:
            raise HTTPException(status_code=404, detail="Conexão não encontrada")
        
        instance_name = connection['instance_name']
        evolution_url = os.environ.get("EVOLUTION_API_URL", "http://evolution.suporte.help:8080")
        evolution_key = os.environ.get("EVOLUTION_API_KEY", "iaze-evolution-2025-secure-key")
        
        import httpx
        import asyncio
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. Tentar deletar instância (ignorar erro se não existir)
            try:
                delete_response = await client.delete(
                    f"{evolution_url}/instance/delete/{instance_name}",
                    headers={"apikey": evolution_key}
                )
                print(f"🗑️ Instância deletada: {delete_response.status_code}")
            except Exception as e:
                print(f"⚠️ Erro ao deletar (ignorado): {e}")
            
            # Aguardar 5 segundos antes de recriar
            print("⏳ Aguardando 5 segundos antes de recriar...")
            await asyncio.sleep(5)
            
            # 2. Recriar instância com configurações otimizadas E WEBHOOK
            backend_url = os.environ.get("REACT_APP_BACKEND_URL", "https://wppconnect-fix.preview.emergentagent.com")
            webhook_url = f"{backend_url}/api/whatsapp/webhook/evolution"
            
            create_payload = {
                "instanceName": instance_name,
                "qrcode": True,
                "integration": "WHATSAPP-BAILEYS",
                "webhook": {
                    "url": webhook_url,
                    "webhookByEvents": True,
                    "events": [
                        "MESSAGES_UPSERT",
                        "CONNECTION_UPDATE",
                        "QRCODE_UPDATED"
                    ]
                }
            }
            
            print(f"🔄 Recriando instância: {instance_name}")
            print(f"🔗 Webhook: {webhook_url}")
            create_response = await client.post(
                f"{evolution_url}/instance/create",
                json=create_payload,
                headers={
                    "Content-Type": "application/json",
                    "apikey": evolution_key
                }
            )
            
            print(f"📊 Status da recriação: {create_response.status_code}")
            print(f"📄 Resposta: {create_response.text[:200]}")
            
            if create_response.status_code in [200, 201]:
                print(f"✅ Instância recriada: {instance_name}")
                
                # Aguardar 3 segundos
                await asyncio.sleep(3)
                
                # 3. Buscar novo QR Code
                qr_response = await client.get(
                    f"{evolution_url}/instance/connect/{instance_name}",
                    headers={"apikey": evolution_key}
                )
                
                new_qr = None
                if qr_response.status_code == 200:
                    qr_data = qr_response.json()
                    new_qr = qr_data.get('base64') or qr_data.get('code')
                    print(f"✅ QR Code obtido: {len(new_qr) if new_qr else 0} chars")
                
                # Atualizar no banco
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
                
                return {
                    "success": True,
                    "qr_code": new_qr,
                    "message": "✅ Sessão reiniciada com sucesso"
                }
            elif create_response.status_code == 403:
                raise HTTPException(
                    status_code=400, 
                    detail="⚠️ Aguarde 10 segundos antes de tentar novamente. A Evolution API está bloqueando requisições muito rápidas."
                )
            else:
                error_detail = create_response.text
                raise HTTPException(
                    status_code=500, 
                    detail=f"Erro ao recriar instância: {create_response.status_code}. Detalhes: {error_detail[:200]}"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erro ao reiniciar sessão: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connections/{connection_id}/qrcode")
async def get_connection_qrcode(
    connection_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Buscar QR Code de uma conexão - COM ISOLAMENTO MULTI-TENANT"""
    
    # SEGURANÇA: Buscar com filtro de tenant PRIMEIRO
    tenant_filter = get_tenant_filter(request, current_user)
    query = {**tenant_filter, "id": connection_id}
    
    connection = await db.whatsapp_connections.find_one(query, {"_id": 0})
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
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
            # Atualizar no banco (com filtro de tenant)
            await db.whatsapp_connections.update_one(
                query,
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
    """Buscar Pairing Code (código de 8 dígitos) - COM ISOLAMENTO MULTI-TENANT"""
    
    # SEGURANÇA: Buscar com filtro de tenant PRIMEIRO
    tenant_filter = get_tenant_filter(request, current_user)
    query = {**tenant_filter, "id": connection_id}
    
    connection = await db.whatsapp_connections.find_one(query, {"_id": 0})
    if not connection:
        raise HTTPException(status_code=404, detail="Conexão não encontrada")
    
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
    """Atualizar configurações da conexão - COM ISOLAMENTO MULTI-TENANT"""
    
    # SEGURANÇA: Buscar com filtro de tenant PRIMEIRO
    tenant_filter = get_tenant_filter(request, current_user)
    query = {**tenant_filter, "id": connection_id}
    
    connection = await db.whatsapp_connections.find_one(query, {"_id": 0})
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
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
            query,
            {"$set": update_data}
        )
    
    return {"ok": True}

@router.post("/connections/{connection_id}/refresh-status")
async def refresh_connection_status(
    connection_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Atualizar status da conexão consultando Evolution API"""
    
    # SEGURANÇA: Buscar com filtro de tenant
    tenant_filter = get_tenant_filter(request, current_user)
    query = {**tenant_filter, "id": connection_id}
    
    connection = await db.whatsapp_connections.find_one(query, {"_id": 0})
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    instance_name = connection.get("instance_name")
    if not instance_name:
        raise HTTPException(status_code=400, detail="Instance name not found")
    
    # Verificar status real na Evolution API
    status = await whatsapp_service.check_connection_status(instance_name)
    
    # Atualizar no banco
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
    
    return {
        "ok": True,
        "status": status,
        "connected": status == "connected",
        "instance_name": instance_name
    }

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
                "connected": status == "connected",
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
    """Deletar conexão WhatsApp - COM ISOLAMENTO MULTI-TENANT"""
    
    # SEGURANÇA: Buscar com filtro de tenant PRIMEIRO
    tenant_filter = get_tenant_filter(request, current_user)
    query = {**tenant_filter, "id": connection_id}
    
    connection = await db.whatsapp_connections.find_one(query, {"_id": 0})
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    # Deletar instância da Evolution API
    instance_name = connection.get("instance_name")
    if instance_name:
        try:
            await whatsapp_service.delete_instance(instance_name)
            logger.info(f"✅ Instance {instance_name} deleted from Evolution API")
        except Exception as e:
            logger.warning(f"⚠️ Could not delete instance from Evolution API: {e}")
            # Continuar mesmo com erro
    
    # Deletar do banco (com filtro de tenant)
    await db.whatsapp_connections.delete_one(query)
    
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
