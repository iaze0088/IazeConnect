"""
Modelos para Push Notifications
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid

class PushSubscription(BaseModel):
    """Subscription de push notification de um cliente"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str  # ID do cliente
    reseller_id: str  # ID da revenda
    subscription_data: dict  # Dados completos da subscription (endpoint, keys)
    user_agent: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_used: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PushNotificationRequest(BaseModel):
    """Request para enviar notificação"""
    title: str
    body: str
    icon: Optional[str] = None
    badge: Optional[str] = None
    url: Optional[str] = None  # URL para abrir ao clicar
    tag: Optional[str] = None  # Tag para agrupar notificações
    vibrate: Optional[list] = [200, 100, 200]  # Padrão de vibração
    requireInteraction: Optional[bool] = False  # Manter notificação visível

class SendNotificationToClient(BaseModel):
    """Request para enviar notificação para um cliente específico"""
    client_id: str
    notification: PushNotificationRequest
