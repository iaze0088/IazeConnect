"""
Serviço de Push Notifications usando Web Push Protocol
"""
from pywebpush import webpush, WebPushException
import json
import logging
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)

# Configurações VAPID (Web Push)
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "BOozFZ70h_Yg9mylQQdpC4eQLape96unxkMAbKdog9IwpMZkhGYxYTlR803Lch0QagjZi2hYTPiNZI1qSEK6oKM")
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
VAPID_CLAIMS = {
    "sub": "mailto:suporte@iaze.com.br"
}

class PushNotificationService:
    """Serviço para envio de push notifications"""
    
    def __init__(self):
        self.vapid_public_key = VAPID_PUBLIC_KEY
        self.vapid_private_key = VAPID_PRIVATE_KEY
        self.vapid_claims = VAPID_CLAIMS
    
    async def send_notification(
        self,
        subscription_info: Dict[str, Any],
        notification_data: Dict[str, Any]
    ) -> bool:
        """
        Envia uma push notification para uma subscription
        
        Args:
            subscription_info: Dados da subscription (endpoint, keys)
            notification_data: Dados da notificação (title, body, etc)
        
        Returns:
            bool: True se enviado com sucesso, False caso contrário
        """
        try:
            # Preparar payload
            payload = json.dumps(notification_data)
            
            logger.info(f"📲 Enviando push notification para {subscription_info.get('endpoint', 'N/A')[:50]}...")
            
            # Enviar via Web Push
            response = webpush(
                subscription_info=subscription_info,
                data=payload,
                vapid_private_key=self.vapid_private_key,
                vapid_claims=self.vapid_claims
            )
            
            logger.info(f"✅ Push notification enviada com sucesso! Status: {response.status_code}")
            return True
            
        except WebPushException as e:
            logger.error(f"❌ Erro ao enviar push notification: {e}")
            
            # Se a subscription expirou (410 Gone), marcar como inativa
            if e.response and e.response.status_code == 410:
                logger.warning("⚠️ Subscription expirou (410 Gone)")
                return False
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao enviar push: {e}")
            return False
    
    def get_public_key(self) -> str:
        """Retorna a chave pública VAPID para o frontend"""
        return self.vapid_public_key


# Instância global do serviço
push_service = PushNotificationService()
