#!/bin/bash
# Script de Migração COMPLETA para WPPConnect
# Remove Evolution API e configura WPPConnect

set -e

echo "="
echo "🚀 MIGRAÇÃO EVOLUTION API → WPPCONNECT"
echo "="
echo ""

echo "📍 Passo 1: Backup do .env atual"
cp /app/backend/.env /app/backend/.env.backup.evolution
echo "✅ Backup criado em .env.backup.evolution"
echo ""

echo "📍 Passo 2: Atualizar .env para WPPConnect"
cat > /app/backend/.env << 'EOF'
# MongoDB
MONGO_URL="mongodb://iaze_mongodb:27017/support_chat"

# JWT
JWT_SECRET_KEY="iaze-super-secret-key-2025-v2"

# WPPConnect-Server Configuration
WPPCONNECT_URL="http://151.243.218.223:21465"
WPPCONNECT_SECRET_KEY="iaze-wppconnect-2025-secure-key"

# Backend URL (para webhooks)
REACT_APP_BACKEND_URL="https://suporte.help"

# REMOVIDO: EVOLUTION_API_URL
# REMOVIDO: EVOLUTION_API_KEY
EOF
echo "✅ .env atualizado para WPPConnect"
echo ""

echo "📍 Passo 3: Atualizar whatsapp_routes.py para usar WPPConnect"
cat > /app/backend/whatsapp_routes.py << 'ROUTES_EOF'
"""
Rotas WhatsApp WPPConnect-Server
Sistema completo de gerenciamento
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Header
from typing import List, Optional
import uuid
import os
import json
import logging
from datetime import datetime, timezone

from whatsapp_models import *
from whatsapp_service_wppconnect import WhatsAppServiceWPPConnect
from tenant_helpers import get_tenant_filter, get_request_tenant

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])

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

# Instanciar serviço
whatsapp_service = None

def get_whatsapp_service():
    global whatsapp_service
    if whatsapp_service is None:
        from server import db
        whatsapp_service = WhatsAppServiceWPPConnect(db)
    return whatsapp_service

# ==================== WEBHOOK WPPCONNECT ====================

@router.post("/webhook/wppconnect")
async def webhook_wppconnect(request: Request):
    """Receber eventos do WPPConnect-Server"""
    try:
        data = await request.json()
        event_type = data.get("event")
        
        logger.info(f"📨 Webhook WPPConnect: {event_type}")
        logger.info(f"   Data: {data}")
        
        # Processar mensagens recebidas
        if event_type == "message:any":
            service = get_whatsapp_service()
            return await service.handle_incoming_message(data)
        else:
            logger.info(f"⚠️ Evento não processado: {event_type}")
            return {"success": True, "message": "Event received but not processed"}
            
    except Exception as e:
        logger.error(f"❌ Erro no webhook WPPConnect: {e}")
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
        db = get_db()
        service = get_whatsapp_service()
        
        # Gerar ID e nome da sessão
        connection_id = str(uuid.uuid4())
        session_name = f"{connection.name.lower().replace(' ', '_')}_{connection_id[:8]}"
        
        # Criar sessão no WPPConnect
        result = await service.create_session(current_user["reseller_id"], session_name)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Salvar no banco
        connection_data = {
            "id": connection_id,
            "reseller_id": current_user["reseller_id"],
            "name": connection.name,
            "instance_name": session_name,
            "status": "connecting",
            "connected": False,
            "qr_code": result.get("qr_code"),
            "phone_number": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.whatsapp_connections.insert_one(connection_data)
        
        # Remover _id do MongoDB antes de retornar
        connection_data.pop("_id", None)
        
        return connection_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connections")
async def list_connections(current_user: dict = Depends(get_current_user)):
    """Listar conexões WhatsApp"""
    try:
        db = get_db()
        connections = await db.whatsapp_connections.find(
            {"reseller_id": current_user["reseller_id"]},
            {"_id": 0}
        ).to_list(length=100)
        
        return connections
        
    except Exception as e:
        logger.error(f"Error listing connections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connections/{connection_id}/check-status")
async def check_connection_status(
    connection_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Verificar status da conexão"""
    try:
        db = get_db()
        service = get_whatsapp_service()
        
        # Buscar conexão
        connection = await db.whatsapp_connections.find_one(
            {"id": connection_id, "reseller_id": current_user["reseller_id"]}
        )
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        # Verificar status no WPPConnect
        status = await service.check_session_status(connection["instance_name"])
        
        # Atualizar status no banco
        await db.whatsapp_connections.update_one(
            {"id": connection_id},
            {
                "$set": {
                    "status": status,
                    "connected": (status == "connected"),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        # Se conectado, obter QR code atualizado
        qr_code = None
        if status == "connecting":
            qr_code = await service.get_qr_code(connection["instance_name"])
            if qr_code:
                await db.whatsapp_connections.update_one(
                    {"id": connection_id},
                    {"$set": {"qr_code": qr_code}}
                )
        
        return {
            "connection_id": connection_id,
            "status": status,
            "qr_code": qr_code
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/connections/{connection_id}")
async def delete_connection(
    connection_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Deletar conexão WhatsApp"""
    try:
        db = get_db()
        service = get_whatsapp_service()
        
        # Buscar conexão
        connection = await db.whatsapp_connections.find_one(
            {"id": connection_id, "reseller_id": current_user["reseller_id"]}
        )
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        # Deletar do WPPConnect
        await service.delete_session(connection["instance_name"])
        
        # Deletar do banco
        await db.whatsapp_connections.delete_one({"id": connection_id})
        
        return {"message": "Connection deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup-all")
async def cleanup_all_connections(current_user: dict = Depends(get_current_user)):
    """Limpar TODAS as conexões (apenas admin)"""
    try:
        service = get_whatsapp_service()
        
        # Se for admin, limpar tudo; se for reseller, apenas suas conexões
        reseller_id = None if current_user.get("user_type") == "admin" else current_user["reseller_id"]
        
        result = await service.cleanup_all_sessions(reseller_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))
ROUTES_EOF
echo "✅ whatsapp_routes.py atualizado"
echo ""

echo "📍 Passo 4: Reiniciar backend"
sudo supervisorctl restart backend
sleep 3
echo "✅ Backend reiniciado"
echo ""

echo "📍 Passo 5: Verificar status"
sudo supervisorctl status backend
echo ""

echo "🎉 MIGRAÇÃO CONCLUÍDA!"
echo ""
echo "✅ Evolution API → WPPConnect"
echo "✅ Configurações atualizadas"
echo "✅ Backend reiniciado"
echo ""
echo "📝 Próximos passos:"
echo "1. Acesse suporte.help/admin"
echo "2. Vá para aba WhatsApp"
echo "3. Clique em 'Nova Conexão'"
echo "4. QR Code deve aparecer corretamente"
echo ""
echo "🔧 Logs do backend:"
echo "tail -f /var/log/supervisor/backend.*.log"
