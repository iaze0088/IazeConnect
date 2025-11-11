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
from tenant_helpers import get_tenant_filter, get_request_tenant

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

# Criar dependência de autenticação
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Dependência de autenticação"""
    from server import verify_token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    return verify_token(token)

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
        whatsapp_service = wppconnect_service
    return whatsapp_service

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
        logger.info(f"🚀 Criando conexão WPPConnect para: {connection.name}")
        
        # Gerar nome de sessão
        session_name = connection.name.lower().replace(' ', '_').replace('-', '_')
        connection_id = str(uuid.uuid4())
        
        # Criar sessão no WPPConnect
        result = await wppconnect_service.create_session(session_name)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=f"Erro ao criar instância: {result.get('error', 'Erro desconhecido')}")
        
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
        
        await db.whatsapp_connections.insert_one(connection_data)
        
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
    """Verificar status da conexão WPPConnect"""
    try:
        db = get_db()
        
        # Buscar conexão no banco (admin pode ver todas, reseller apenas suas)
        query = {"id": connection_id}
        if current_user.get("user_type") != "admin" and current_user.get("reseller_id"):
            query["reseller_id"] = current_user["reseller_id"]
        
        connection = await db.whatsapp_connections.find_one(query)
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        # Verificar status no WPPConnect se tiver token
        if connection.get("wppconnect_token"):
            service = get_whatsapp_service()
            result = await service.get_session_status(
                connection["instance_name"],
                connection["wppconnect_token"]
            )
            
            # Atualizar status no banco
            new_status = "connected" if result.get("connected") else "disconnected"
            await db.whatsapp_connections.update_one(
                {"id": connection_id},
                {"$set": {"status": new_status, "is_connected": result.get("connected", False)}}
            )
            
            return {
                "connection_id": connection_id,
                "status": new_status,
                "instance_name": connection["instance_name"],
                "connected": result.get("connected", False)
            }
        else:
            return {
                "connection_id": connection_id,
                "status": connection.get("status", "disconnected"),
                "instance_name": connection["instance_name"],
                "connected": False
            }
        
    except HTTPException:
        raise
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
