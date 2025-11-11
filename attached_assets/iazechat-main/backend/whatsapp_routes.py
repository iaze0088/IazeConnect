"""
Rotas WhatsApp Evolution API V2
Sistema completo de gerenciamento de instâncias WhatsApp
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Header
from typing import List, Optional
import uuid
import os
import json
import logging
from datetime import datetime, timezone

from whatsapp_models import *
from whatsapp_service_wppconnect_v2 import wppconnect_service
from whatsapp_service_mock import get_mock_service

# Verificar se deve usar mock
USE_MOCK = os.environ.get("WPPCONNECT_MOCK", "false").lower() == "true"
print(f"🔧 [CONFIG] WPPCONNECT_MOCK={os.environ.get('WPPCONNECT_MOCK', 'not set')}, USE_MOCK={USE_MOCK}", flush=True)
from tenant_helpers import get_tenant_filter, get_request_tenant

router = APIRouter(tags=["whatsapp"])

# Criar dependência de autenticação
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Dependência de autenticação"""
    try:
        print(f"🔐 [AUTH] Verificando autenticação... Header: {authorization[:50] if authorization else 'None'}", flush=True)
        from server import verify_token
        if not authorization or not authorization.startswith("Bearer "):
            print(f"❌ [AUTH] Token ausente ou inválido", flush=True)
            raise HTTPException(status_code=401, detail="Not authenticated")
        token = authorization.split(" ")[1]
        print(f"🔐 [AUTH] Token extraído, verificando...", flush=True)
        user = verify_token(token)
        print(f"✅ [AUTH] Usuário autenticado: {user.get('email') if isinstance(user, dict) else 'N/A'}", flush=True)
        return user
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [AUTH] Erro na autenticação: {type(e).__name__}: {e}", flush=True)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")

# Logger
logger = logging.getLogger(__name__)

# Importar DB de forma lazy
def get_db():
    from server import db
    return db

# Instanciar serviço WPPConnect
whatsapp_service = None

def get_whatsapp_service():
    global whatsapp_service
    if whatsapp_service is None:
        if USE_MOCK:
            print("🔧 [MOCK] Usando WhatsApp Mock Service", flush=True)
            whatsapp_service = get_mock_service()
        else:
            print("🔗 [WPPCONNECT] Usando WPPConnect Service", flush=True)
            whatsapp_service = wppconnect_service
    return whatsapp_service

# ==================== TEST ENDPOINT (NO AUTH) ====================

@router.get("/test-no-auth")
async def test_endpoint_no_auth(request: Request):
    """Endpoint de teste SEM autenticação"""
    import socket
    import os
    hostname = socket.gethostname()
    pid = os.getpid()
    
    # Ler instance ID se existir
    instance_id = "unknown"
    try:
        with open("/tmp/backend_instance_id.txt", "r") as f:
            instance_id = f.read().strip()
    except:
        pass
    
    print(f"✅ [TEST] Endpoint de teste acessado! Host: {hostname}, PID: {pid}, Client: {request.client.host if request.client else 'N/A'}", flush=True)
    
    # Listar rotas do router atual
    routes = []
    for route in router.routes:
        routes.append(f"{list(route.methods)} {route.path}")
    
    return {
        "status": "success", 
        "message": "WhatsApp routes working!", 
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "backend_hostname": hostname,
        "backend_pid": pid,
        "instance_id": instance_id,
        "client_ip": request.client.host if request.client else "unknown",
        "registered_routes": routes[:10]  # Primeiras 10 rotas
    }

# ==================== WEBHOOK EVOLUTION API ====================

@router.post("/webhook/evolution")
async def webhook_evolution(request: Request):
    """Receber eventos da Evolution API V2"""
    try:
        data = await request.json()
        event = data.get("event")
        
        logger.info(f"📨 Webhook Evolution API: {event}")
        logger.info(f"   Data: {json.dumps(data, indent=2)[:500]}")
        
        # Processar eventos de conexão
        if event == "connection.update":
            instance_name = data.get("instance")
            state = data.get("data", {}).get("state")
            
            if state:
                # Atualizar status no banco
                db = get_db()
                status_map = {
                    "open": "connected",
                    "connecting": "connecting",
                    "close": "disconnected"
                }
                status = status_map.get(state, "connecting")
                
                await db.whatsapp_connections.update_one(
                    {"instance_name": instance_name},
                    {
                        "$set": {
                            "status": status,
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
                
                logger.info(f"✅ Status atualizado: {instance_name} → {status}")
        
        # Processar QR code updates
        elif event == "qrcode.updated":
            instance_name = data.get("instance")
            qr_code = data.get("data", {}).get("qrcode", {}).get("code")
            qr_code_base64 = data.get("data", {}).get("qrcode", {}).get("base64")
            
            if qr_code or qr_code_base64:
                db = get_db()
                await db.whatsapp_connections.update_one(
                    {"instance_name": instance_name},
                    {
                        "$set": {
                            "qr_code": qr_code,
                            "qr_code_base64": qr_code_base64,
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
                
                logger.info(f"✅ QR code atualizado: {instance_name}")
        
        # Processar mensagens recebidas
        elif event == "messages.upsert":
            logger.info("📨 Recebendo mensagem do WhatsApp QR Code")
            
            try:
                db = get_db()
                instance_name = data.get("instance")
                messages_data = data.get("data", {}).get("messages", [])
                
                logger.info(f"   Instance: {instance_name}")
                logger.info(f"   Mensagens: {len(messages_data)}")
                
                # Buscar departamento WHATSAPP STARTER
                department = await db.departments.find_one({"name": "WHATSAPP STARTER", "type": "whatsapp"})
                
                if not department:
                    logger.error("❌ Departamento 'WHATSAPP STARTER' não encontrado!")
                    return {"success": False, "error": "Department not found"}
                
                logger.info(f"   ✅ Departamento encontrado: {department['id']}")
                
                for msg in messages_data:
                    message_key = msg.get("key", {})
                    message_info = msg.get("message", {})
                    from_me = message_key.get("fromMe", False)
                    
                    # Ignorar mensagens enviadas pelo bot
                    if from_me:
                        logger.info("   ⏭️ Mensagem enviada pelo bot, ignorando...")
                        continue
                    
                    # Extrair número do remetente
                    remote_jid = message_key.get("remoteJid", "")
                    phone_number = remote_jid.split("@")[0] if "@" in remote_jid else remote_jid
                    
                    # Extrair texto da mensagem
                    text = ""
                    if "conversation" in message_info:
                        text = message_info["conversation"]
                    elif "extendedTextMessage" in message_info:
                        text = message_info["extendedTextMessage"].get("text", "")
                    
                    logger.info(f"   📱 De: {phone_number}")
                    logger.info(f"   💬 Mensagem: {text[:50]}...")
                    
                    # Buscar ou criar ticket
                    ticket = await db.tickets.find_one({
                        "whatsapp": phone_number,
                        "status": {"$in": ["open", "waiting", "attending"]}
                    })
                    
                    if not ticket:
                        # Criar novo ticket
                        ticket_id = str(uuid.uuid4())
                        ticket = {
                            "id": ticket_id,
                            "whatsapp": phone_number,
                            "status": "open",
                            "department": department["id"],
                            "agent_id": None,
                            "whatsapp_origin": True,
                            "whatsapp_instance": instance_name,
                            "is_whatsapp": True,
                            "ticket_origin": "whatsapp_qr",
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }
                        
                        await db.tickets.insert_one(ticket)
                        logger.info(f"   ✅ Ticket criado: {ticket_id}")
                    else:
                        ticket_id = ticket["id"]
                        logger.info(f"   ✅ Ticket existente: {ticket_id}")
                    
                    # Salvar mensagem
                    message_id = str(uuid.uuid4())
                    message = {
                        "id": message_id,
                        "ticket_id": ticket_id,
                        "whatsapp": phone_number,
                        "message": text,
                        "from_type": "client",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    
                    await db.messages.insert_one(message)
                    logger.info(f"   ✅ Mensagem salva: {message_id}")
                
                logger.info("✅ Processamento de mensagens concluído!")
                
            except Exception as e:
                logger.error(f"❌ Erro ao processar mensagem: {e}")
                import traceback
                traceback.print_exc()
        
        return {"success": True, "message": "Webhook received"}
        
    except Exception as e:
        logger.error(f"❌ Erro no webhook Evolution: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

# ==================== ROTAS DE GERENCIAMENTO ====================

@router.post("/connections")
async def create_connection(
    connection: WhatsAppConnectionCreate,
    current_user: dict = Depends(get_current_user)
):
    """Criar nova conexão WhatsApp WPPConnect"""
    try:
        print(f"🚀 [WHATSAPP] Criando conexão para: {connection.name}", flush=True)
        logger.info(f"🚀 Criando conexão WPPConnect para: {connection.name}")
        
        # Gerar nome de sessão
        session_name = connection.name.lower().replace(' ', '_').replace('-', '_')
        connection_id = str(uuid.uuid4())
        
        print(f"📝 [WHATSAPP] Session name: {session_name}, Connection ID: {connection_id}", flush=True)
        
        # Criar sessão no WPPConnect com webhook
        # URL do webhook será: https://suporte.help/api/webhooks/wppconnect/status
        webhook_url = os.environ.get("BACKEND_PUBLIC_URL", "https://suporte.help") + "/api/webhooks/wppconnect/status"
        
        print(f"🔗 [WHATSAPP] Criando sessão com webhook: {webhook_url}", flush=True)
        result = await wppconnect_service.create_session(session_name, webhook_url=webhook_url)
        
        print(f"📦 [WHATSAPP] Resultado: {result}", flush=True)
        
        if not result.get("success"):
            error_msg = f"Erro ao criar instância: {result.get('error', 'Erro desconhecido')}"
            print(f"❌ [WHATSAPP] {error_msg}", flush=True)
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Salvar no banco
        db = get_db()
        connection_data = {
            "id": connection_id,
            "name": connection.name,
            "instance_name": session_name,
            "status": "connecting",
            "is_connected": False,
            "qr_code_base64": result.get("qr_code"),
            "wppconnect_token": result.get("token"),
            "reseller_id": current_user.get("reseller_id"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        print(f"💾 [WHATSAPP] Salvando no banco...", flush=True)
        await db.whatsapp_connections.insert_one(connection_data)
        
        print(f"✅ [WHATSAPP] Conexão criada: {connection_id}", flush=True)
        logger.info(f"✅ Conexão WPPConnect criada: {connection_id}")
        
        # Retornar resultado
        return {
            "id": connection_id,
            "name": connection.name,
            "instance_name": session_name,
            "status": "connecting",
            "connected": False,
            "qr_code_base64": result.get("qr_code"),
            "created_at": connection_data["created_at"],
            "updated_at": connection_data["updated_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [WHATSAPP] ERRO CRÍTICO: {type(e).__name__}: {e}", flush=True)
        import traceback
        traceback.print_exc()
        logger.error(f"❌ Error creating connection: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connections")
async def list_connections(current_user: dict = Depends(get_current_user)):
    """Listar conexões WhatsApp WPPConnect"""
    try:
        db = get_db()
        
        # Buscar conexões do usuário no banco (admin vê todas, reseller apenas suas)
        query = {}
        if current_user.get("user_type") != "admin" and current_user.get("reseller_id"):
            query["reseller_id"] = current_user["reseller_id"]
        
        connections = await db.whatsapp_connections.find(query).to_list(None)
        
        # Converter ObjectId para string e remover _id
        result = []
        for conn in connections:
            conn_data = {k: v for k, v in conn.items() if k != '_id'}
            result.append(conn_data)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error listing connections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connections/{connection_id}/check-status")
async def check_connection_status(
    connection_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Verificar status de conexão específica com FALLBACK"""
    try:
        db = get_db()
        
        # Buscar conexão no banco
        query = {"id": connection_id}
        if current_user.get("user_type") != "admin" and current_user.get("reseller_id"):
            query["reseller_id"] = current_user["reseller_id"]
        
        connection = await db.whatsapp_connections.find_one(query)
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        # Preparar último status conhecido para fallback
        last_known_status = {
            "success": True,
            "status": connection.get("status", "connecting"),
            "connected": connection.get("is_connected", False),
            "phone": connection.get("phone_number"),
            "from_cache": True
        }
        
        # Verificar status real no WPPConnect com fallback
        if connection.get("wppconnect_token") and connection.get("instance_name"):
            service = get_whatsapp_service()
            result = await service.get_session_status(
                connection["instance_name"],
                connection["wppconnect_token"],
                last_known_status=last_known_status
            )
            
            # Se API respondeu (não é cache), atualizar banco
            if not result.get("from_cache"):
                new_status = "connected" if result.get("connected") else "connecting"
                await db.whatsapp_connections.update_one(
                    {"id": connection_id},
                    {"$set": {
                        "status": new_status,
                        "is_connected": result.get("connected", False),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
            
            return {
                "success": True,
                "status": result.get("status", "connecting"),
                "connected": result.get("connected", False),
                "from_cache": result.get("from_cache", False)
            }
        else:
            return last_known_status
        
    except Exception as e:
        logger.error(f"❌ Error checking status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connections/{connection_id}/qr")
async def get_qr_code(
    connection_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obter QR code de uma conexão WPPConnect"""
    try:
        db = get_db()
        
        # Buscar conexão no banco (admin pode ver todas, reseller apenas suas)
        query = {"id": connection_id}
        if current_user.get("user_type") != "admin" and current_user.get("reseller_id"):
            query["reseller_id"] = current_user["reseller_id"]
        
        connection = await db.whatsapp_connections.find_one(query)
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        # Retornar QR code salvo no banco
        qr_code_base64 = connection.get("qr_code_base64")
        
        if not qr_code_base64:
            raise HTTPException(status_code=404, detail="QR code not available")
        
        return {
            "connection_id": connection_id,
            "qr_code_base64": qr_code_base64,
            "status": connection.get("status", "connecting"),
            "instance_name": connection.get("instance_name")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting QR code: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/connections/{connection_id}/refresh-qr")
async def refresh_qr_code(
    connection_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Gerar novo QR code para uma conexão WPPConnect"""
    try:
        print(f"🔄 [WHATSAPP] Refresh QR code para: {connection_id}", flush=True)
        print(f"🔍 [DEBUG] current_user: {current_user}", flush=True)
        logger.info(f"🔄 Refresh QR code para: {connection_id}")
        
        db = get_db()
        
        # Buscar conexão no banco (admin pode ver todas, reseller apenas suas)
        query = {"id": connection_id}
        if current_user.get("user_type") != "admin" and current_user.get("reseller_id"):
            query["reseller_id"] = current_user["reseller_id"]
        
        connection = await db.whatsapp_connections.find_one(query)
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        # Obter instance_name e token da conexão
        instance_name = connection.get("instance_name")
        wppconnect_token = connection.get("wppconnect_token")
        
        if not instance_name:
            raise HTTPException(status_code=400, detail="Instance name not found")
        
        # Gerar novo QR code via WPPConnect
        print(f"🔗 [WHATSAPP] Gerando novo QR code para sessão: {instance_name}", flush=True)
        result = await wppconnect_service.create_session(instance_name)
        
        if not result.get("success"):
            error_msg = f"Erro ao gerar QR code: {result.get('error', 'Erro desconhecido')}"
            print(f"❌ [WHATSAPP] {error_msg}", flush=True)
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Atualizar QR code no banco
        new_qr_code = result.get("qr_code")
        new_token = result.get("token")
        
        update_data = {
            "qr_code_base64": new_qr_code,
            "status": "connecting",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if new_token:
            update_data["wppconnect_token"] = new_token
        
        await db.whatsapp_connections.update_one(
            {"id": connection_id},
            {"$set": update_data}
        )
        
        print(f"✅ [WHATSAPP] QR code atualizado para: {connection_id}", flush=True)
        logger.info(f"✅ QR code atualizado para: {connection_id}")
        
        return {
            "success": True,
            "connection_id": connection_id,
            "qr_code_base64": new_qr_code,
            "status": "connecting",
            "message": "QR code gerado com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [WHATSAPP] ERRO ao refresh QR: {type(e).__name__}: {e}", flush=True)
        logger.error(f"❌ Error refreshing QR code: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/connections/{connection_id}/restart-session")
async def restart_session(
    connection_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Reiniciar sessão WhatsApp WPPConnect"""
    try:
        print(f"🔄 [WHATSAPP] Reiniciando sessão para: {connection_id}", flush=True)
        logger.info(f"🔄 Reiniciando sessão para: {connection_id}")
        
        db = get_db()
        
        # Buscar conexão no banco (admin pode ver todas, reseller apenas suas)
        query = {"id": connection_id}
        if current_user.get("user_type") != "admin" and current_user.get("reseller_id"):
            query["reseller_id"] = current_user["reseller_id"]
        
        connection = await db.whatsapp_connections.find_one(query)
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        instance_name = connection.get("instance_name")
        wppconnect_token = connection.get("wppconnect_token")
        
        if not instance_name:
            raise HTTPException(status_code=400, detail="Instance name not found")
        
        # Fechar sessão atual (se existir token)
        if wppconnect_token:
            print(f"🔗 [WHATSAPP] Fechando sessão atual: {instance_name}", flush=True)
            close_result = await wppconnect_service.close_session(instance_name, wppconnect_token)
            print(f"📦 [WHATSAPP] Resultado close: {close_result}", flush=True)
        
        # Criar nova sessão e obter novo QR code
        print(f"🔗 [WHATSAPP] Criando nova sessão: {instance_name}", flush=True)
        result = await wppconnect_service.create_session(instance_name)
        
        if not result.get("success"):
            error_msg = f"Erro ao reiniciar sessão: {result.get('error', 'Erro desconhecido')}"
            print(f"❌ [WHATSAPP] {error_msg}", flush=True)
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Atualizar no banco
        update_data = {
            "qr_code_base64": result.get("qr_code"),
            "wppconnect_token": result.get("token"),
            "status": "connecting",
            "is_connected": False,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.whatsapp_connections.update_one(
            {"id": connection_id},
            {"$set": update_data}
        )
        
        print(f"✅ [WHATSAPP] Sessão reiniciada para: {connection_id}", flush=True)
        logger.info(f"✅ Sessão reiniciada para: {connection_id}")
        
        return {
            "success": True,
            "connection_id": connection_id,
            "qr_code_base64": result.get("qr_code"),
            "status": "connecting",
            "message": "Sessão reiniciada com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [WHATSAPP] ERRO ao reiniciar sessão: {type(e).__name__}: {e}", flush=True)
        logger.error(f"❌ Error restarting session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/connections/{connection_id}/refresh-status")
async def refresh_status(
    connection_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Atualizar status de uma conexão específica consultando o WPPConnect"""
    try:
        print(f"🔄 [REFRESH-STATUS] Para conexão: {connection_id}", flush=True)
        db = get_db()
        
        # Buscar conexão no banco
        query = {"id": connection_id}
        if current_user.get("user_type") != "admin" and current_user.get("reseller_id"):
            query["reseller_id"] = current_user["reseller_id"]
        
        connection = await db.whatsapp_connections.find_one(query)
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        # Verificar status no WPPConnect
        if connection.get("wppconnect_token") and connection.get("instance_name"):
            service = get_whatsapp_service()
            result = await service.get_session_status(
                connection["instance_name"],
                connection["wppconnect_token"]
            )
            
            print(f"📱 [REFRESH-STATUS] Status: {result.get('status', 'UNKNOWN')}", flush=True)
            
            # Atualizar status no banco
            new_status = "connected" if result.get("connected") else "disconnected"
            await db.whatsapp_connections.update_one(
                {"id": connection_id},
                {"$set": {
                    "status": new_status,
                    "is_connected": result.get("connected", False),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            return {
                "success": True,
                "connected": result.get("connected", False),
                "status": new_status,
                "phone_number": result.get("phone", connection.get("phone_number"))
            }
        else:
            return {
                "success": False,
                "connected": False,
                "status": "disconnected",
                "message": "Missing token or instance name"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error refreshing status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/connections/{connection_id}")
async def delete_connection(
    connection_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Deletar conexão WhatsApp WPPConnect"""
    try:
        db = get_db()
        
        # Buscar conexão no banco (admin pode ver todas, reseller apenas suas)
        query = {"id": connection_id}
        if current_user.get("user_type") != "admin" and current_user.get("reseller_id"):
            query["reseller_id"] = current_user["reseller_id"]
        
        connection = await db.whatsapp_connections.find_one(query)
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        # Fechar sessão no WPPConnect
        if connection.get("wppconnect_token"):
            await wppconnect_service.close_session(
                connection["instance_name"],
                connection["wppconnect_token"]
            )
        
        # Deletar do banco
        await db.whatsapp_connections.delete_one({"id": connection_id})
        
        logger.info(f"✅ Conexão WPPConnect deletada: {connection_id}")
        
        return {"message": "Connection deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ENDPOINTS DE CONFIGURAÇÃO ====================

@router.get("/config")
async def get_whatsapp_config(current_user: dict = Depends(get_current_user)):
    """Obter configurações do WhatsApp"""
    try:
        db = get_db()
        
        # Buscar configuração do reseller/admin
        query = {}
        if current_user.get("user_type") != "admin" and current_user.get("reseller_id"):
            query["reseller_id"] = current_user["reseller_id"]
        
        # Buscar configuração no banco (ou criar uma padrão)
        config = await db.whatsapp_config.find_one(query)
        
        if not config:
            # Criar configuração padrão
            config = {
                "reseller_id": current_user.get("reseller_id"),
                "transfer_message": "Transferindo para atendente humano...",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.whatsapp_config.insert_one(config)
        
        # Remover _id para evitar erro de serialização
        config = {k: v for k, v in config.items() if k != '_id'}
        
        return config
        
    except Exception as e:
        logger.error(f"❌ Error getting WhatsApp config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/config")
async def update_whatsapp_config(
    data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Atualizar configurações do WhatsApp"""
    try:
        db = get_db()
        
        # Buscar configuração do reseller/admin
        query = {}
        if current_user.get("user_type") != "admin" and current_user.get("reseller_id"):
            query["reseller_id"] = current_user["reseller_id"]
        
        # Atualizar ou criar configuração
        update_data = {
            "transfer_message": data.get("transfer_message", ""),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = await db.whatsapp_config.update_one(
            query,
            {"$set": update_data},
            upsert=True
        )
        
        logger.info(f"✅ Configuração WhatsApp atualizada para: {current_user.get('email', 'N/A')}")
        
        return {"message": "Configuration updated successfully"}
        
    except Exception as e:
        logger.error(f"❌ Error updating WhatsApp config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_whatsapp_stats(current_user: dict = Depends(get_current_user)):
    """Obter estatísticas das conexões WhatsApp"""
    try:
        db = get_db()
        
        # Buscar conexões do reseller/admin
        query = {}
        if current_user.get("user_type") != "admin" and current_user.get("reseller_id"):
            query["reseller_id"] = current_user["reseller_id"]
        
        # Contar conexões
        all_connections = await db.whatsapp_connections.find(query).to_list(None)
        
        active_count = sum(1 for conn in all_connections if conn.get("is_connected"))
        inactive_count = len(all_connections) - active_count
        
        # Contar mensagens recebidas/enviadas (exemplo)
        total_received = 0
        total_sent = 0
        
        stats = {
            "total_connections": len(all_connections),
            "active_connections": active_count,
            "inactive_connections": inactive_count,
            "total_received_today": total_received,
            "total_sent_today": total_sent,
            "plan": "BASICO"  # Placeholder - pode ser dinamizado
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Error getting WhatsApp stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync-all-status")
async def sync_all_connection_status(current_user: dict = Depends(get_current_user)):
    """Sincronizar status de todas as conexões com o WPPConnect"""
    try:
        print(f"🔄 [SYNC] Sincronizando status de todas as conexões...", flush=True)
        db = get_db()
        
        # Buscar todas as conexões
        query = {}
        if current_user.get("user_type") != "admin" and current_user.get("reseller_id"):
            query["reseller_id"] = current_user["reseller_id"]
        
        connections = await db.whatsapp_connections.find(query).to_list(None)
        print(f"📊 [SYNC] Encontradas {len(connections)} conexões no banco", flush=True)
        
        synced_count = 0
        updated_connections = []
        
        for conn in connections:
            if conn.get("wppconnect_token") and conn.get("instance_name"):
                try:
                    service = get_whatsapp_service()
                    result = await service.get_session_status(
                        conn["instance_name"],
                        conn["wppconnect_token"]
                    )
                    
                    print(f"📱 [SYNC] {conn['instance_name']}: {result.get('status', 'UNKNOWN')}", flush=True)
                    
                    # Atualizar status no banco
                    new_status = "connected" if result.get("connected") else "disconnected"
                    await db.whatsapp_connections.update_one(
                        {"id": conn["id"]},
                        {"$set": {
                            "status": new_status,
                            "is_connected": result.get("connected", False),
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    
                    synced_count += 1
                    updated_connections.append({
                        "id": conn["id"],
                        "instance_name": conn["instance_name"],
                        "old_status": conn.get("status"),
                        "new_status": new_status,
                        "connected": result.get("connected", False)
                    })
                    
                except Exception as e:
                    print(f"❌ [SYNC] Erro ao verificar {conn['instance_name']}: {e}", flush=True)
        
        print(f"✅ [SYNC] Sincronizadas {synced_count}/{len(connections)} conexões", flush=True)
        
        return {
            "success": True,
            "total_connections": len(connections),
            "synced": synced_count,
            "updated_connections": updated_connections
        }
        
    except Exception as e:
        logger.error(f"❌ Error syncing connection status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
