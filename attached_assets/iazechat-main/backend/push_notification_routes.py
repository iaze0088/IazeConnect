"""
Rotas para Push Notifications
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone
import logging

from push_notification_models import (
    PushSubscription,
    PushNotificationRequest,
    SendNotificationToClient
)
from push_notification_service import push_service

logger = logging.getLogger(__name__)

# Router
push_router = APIRouter(prefix="/push", tags=["push-notifications"])

# MongoDB
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "support_chat")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


@push_router.get("/vapid-public-key")
async def get_vapid_public_key():
    """Retorna a chave pública VAPID para o frontend"""
    return {"publicKey": push_service.get_public_key()}


@push_router.post("/subscribe")
async def subscribe_push(subscription: PushSubscription):
    """Registra uma nova subscription de push para um cliente"""
    try:
        # Verificar se já existe
        existing = await db.push_subscriptions.find_one({
            "client_id": subscription.client_id,
            "subscription_data.endpoint": subscription.subscription_data.get("endpoint")
        })
        
        if existing:
            # Atualizar subscription existente
            await db.push_subscriptions.update_one(
                {"id": existing["id"]},
                {
                    "$set": {
                        "subscription_data": subscription.subscription_data,
                        "is_active": True,
                        "last_used": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            logger.info(f"✅ Subscription atualizada para cliente {subscription.client_id}")
            return {"message": "Subscription atualizada", "id": existing["id"]}
        
        # Criar nova subscription
        subscription_dict = subscription.dict()
        subscription_dict["created_at"] = subscription_dict["created_at"].isoformat()
        subscription_dict["last_used"] = subscription_dict["last_used"].isoformat()
        
        await db.push_subscriptions.insert_one(subscription_dict)
        
        logger.info(f"✅ Nova subscription criada para cliente {subscription.client_id}")
        return {"message": "Subscription criada", "id": subscription.id}
        
    except Exception as e:
        logger.error(f"❌ Erro ao registrar subscription: {e}")
        raise HTTPException(status_code=500, detail="Erro ao registrar subscription")


@push_router.post("/unsubscribe/{client_id}")
async def unsubscribe_push(client_id: str):
    """Remove subscription de push de um cliente"""
    try:
        result = await db.push_subscriptions.update_many(
            {"client_id": client_id},
            {"$set": {"is_active": False}}
        )
        
        logger.info(f"✅ {result.modified_count} subscriptions desativadas para cliente {client_id}")
        return {"message": "Unsubscribed", "count": result.modified_count}
        
    except Exception as e:
        logger.error(f"❌ Erro ao remover subscription: {e}")
        raise HTTPException(status_code=500, detail="Erro ao remover subscription")


@push_router.post("/send-to-client")
async def send_notification_to_client(data: SendNotificationToClient):
    """Envia notificação para um cliente específico"""
    try:
        # Buscar subscriptions ativas do cliente
        subscriptions = await db.push_subscriptions.find({
            "client_id": data.client_id,
            "is_active": True
        }).to_list(length=None)
        
        if not subscriptions:
            logger.warning(f"⚠️ Nenhuma subscription ativa para cliente {data.client_id}")
            return {"message": "Nenhuma subscription ativa", "sent": 0}
        
        # Preparar dados da notificação
        notification_payload = {
            "title": data.notification.title,
            "body": data.notification.body,
            "icon": data.notification.icon or "/logo192.png",
            "badge": data.notification.badge or "/badge72.png",
            "url": data.notification.url or "/",
            "tag": data.notification.tag or "iaze-notification",
            "vibrate": data.notification.vibrate or [200, 100, 200],
            "requireInteraction": data.notification.requireInteraction or False,
            "timestamp": datetime.now(timezone.utc).timestamp() * 1000
        }
        
        # Enviar para todas as subscriptions do cliente
        sent_count = 0
        failed_subscriptions = []
        
        for sub in subscriptions:
            success = await push_service.send_notification(
                subscription_info=sub["subscription_data"],
                notification_data=notification_payload
            )
            
            if success:
                sent_count += 1
                # Atualizar last_used
                await db.push_subscriptions.update_one(
                    {"id": sub["id"]},
                    {"$set": {"last_used": datetime.now(timezone.utc).isoformat()}}
                )
            else:
                failed_subscriptions.append(sub["id"])
        
        # Desativar subscriptions que falharam
        if failed_subscriptions:
            await db.push_subscriptions.update_many(
                {"id": {"$in": failed_subscriptions}},
                {"$set": {"is_active": False}}
            )
        
        logger.info(f"✅ Notificação enviada para {sent_count}/{len(subscriptions)} devices do cliente {data.client_id}")
        return {
            "message": "Notificação enviada",
            "sent": sent_count,
            "failed": len(failed_subscriptions)
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao enviar notificação: {e}")
        raise HTTPException(status_code=500, detail="Erro ao enviar notificação")


@push_router.post("/broadcast/{reseller_id}")
async def broadcast_notification(reseller_id: str, notification: PushNotificationRequest):
    """Envia notificação para todos os clientes de uma revenda"""
    try:
        # Buscar todas as subscriptions ativas da revenda
        subscriptions = await db.push_subscriptions.find({
            "reseller_id": reseller_id,
            "is_active": True
        }).to_list(length=None)
        
        if not subscriptions:
            logger.warning(f"⚠️ Nenhuma subscription ativa para revenda {reseller_id}")
            return {"message": "Nenhuma subscription ativa", "sent": 0}
        
        # Preparar dados da notificação
        notification_payload = {
            "title": notification.title,
            "body": notification.body,
            "icon": notification.icon or "/logo192.png",
            "badge": notification.badge or "/badge72.png",
            "url": notification.url or "/",
            "tag": notification.tag or "iaze-broadcast",
            "vibrate": notification.vibrate or [200, 100, 200],
            "requireInteraction": notification.requireInteraction or False,
            "timestamp": datetime.now(timezone.utc).timestamp() * 1000
        }
        
        # Enviar para todas as subscriptions
        sent_count = 0
        failed_subscriptions = []
        
        for sub in subscriptions:
            success = await push_service.send_notification(
                subscription_info=sub["subscription_data"],
                notification_data=notification_payload
            )
            
            if success:
                sent_count += 1
            else:
                failed_subscriptions.append(sub["id"])
        
        # Desativar subscriptions que falharam
        if failed_subscriptions:
            await db.push_subscriptions.update_many(
                {"id": {"$in": failed_subscriptions}},
                {"$set": {"is_active": False}}
            )
        
        logger.info(f"✅ Broadcast enviado para {sent_count}/{len(subscriptions)} devices da revenda {reseller_id}")
        return {
            "message": "Broadcast enviado",
            "sent": sent_count,
            "failed": len(failed_subscriptions),
            "total": len(subscriptions)
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao enviar broadcast: {e}")
        raise HTTPException(status_code=500, detail="Erro ao enviar broadcast")
