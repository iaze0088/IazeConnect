"""
Webhook Handler para WPPConnect - Recebe notificações de status
"""
from fastapi import APIRouter, Request, HTTPException, status
from datetime import datetime, timezone
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import os

# Conexão MongoDB (mesma estrutura do server.py)
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'support_chat')]

def get_db():
    return db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/wppconnect/status")
async def wppconnect_status_webhook(request: Request):
    """
    Recebe notificações de status do WPPConnect
    Eventos: connection, disconnection, qrcode, etc.
    """
    try:
        payload = await request.json()
        
        event_type = payload.get("event")
        session_name = payload.get("session")
        data = payload.get("data", {})
        
        print(f"📥 [WEBHOOK] Recebido evento: {event_type} para sessão: {session_name}", flush=True)
        print(f"📊 [WEBHOOK] Dados: {data}", flush=True)
        
        db = get_db()
        
        # Processar evento de conexão
        if event_type in ["qrcode", "connection", "status-find"]:
            state = data.get("state") or data.get("status")
            is_connected = (
                state == "CONNECTED" or 
                state == "isLogged" or
                data.get("connected") == True
            )
            
            # Atualizar status no banco de dados
            result = await db.whatsapp_connections.update_many(
                {"instance_name": session_name},
                {"$set": {
                    "status": "connected" if is_connected else "connecting",
                    "is_connected": is_connected,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "last_webhook_at": datetime.now(timezone.utc).isoformat(),
                    "last_webhook_event": event_type,
                    "phone_number": data.get("phone") or data.get("number")
                }}
            )
            
            print(f"✅ [WEBHOOK] Status atualizado: {is_connected} ({result.modified_count} documentos)", flush=True)
        
        return {"success": True, "message": "Webhook processado"}
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar webhook: {e}")
        print(f"❌ [WEBHOOK] Erro: {e}", flush=True)
        return {"success": False, "error": str(e)}
