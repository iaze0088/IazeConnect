"""
Modelos para integração WhatsApp Evolution API
Sistema completo de planos e controle anti-banimento
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone

# ==================== PLANOS ====================

class WhatsAppPlan(BaseModel):
    """Planos de WhatsApp"""
    name: str  # "Básico", "Plus", "Pro", "Premium", "Enterprise"
    max_numbers: int  # 1, 2, 3, 5, -1 (ilimitado)
    price: float  # R$ 49, 89, 129, 199, 499

WHATSAPP_PLANS = {
    "basico": WhatsAppPlan(name="Básico", max_numbers=1, price=49.0),
    "plus": WhatsAppPlan(name="Plus", max_numbers=2, price=89.0),
    "pro": WhatsAppPlan(name="Pro", max_numbers=3, price=129.0),
    "premium": WhatsAppPlan(name="Premium", max_numbers=5, price=199.0),
    "enterprise": WhatsAppPlan(name="Enterprise", max_numbers=-1, price=499.0)  # -1 = ilimitado
}

# ==================== CONEXÃO WHATSAPP ====================

class WhatsAppConnection(BaseModel):
    """Conexão WhatsApp de uma revenda"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    reseller_id: str
    instance_name: str  # "lucasrv_1", "lucasrv_2"
    phone_number: Optional[str] = None
    status: str = "disconnected"  # disconnected | connecting | connected | error
    qr_code: Optional[str] = None
    api_key: Optional[str] = None  # API key específica da instância
    
    # Limites configuráveis
    max_received_daily: int = 200  # Mensagens recebidas por dia
    max_sent_daily: int = 200  # Mensagens enviadas por dia
    
    # Contadores
    received_today: int = 0
    sent_today: int = 0
    last_reset: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Rotação
    rotation_order: int = 1  # Ordem na rotação (1, 2, 3...)
    is_active_for_rotation: bool = True
    
    # Metadados
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: Optional[datetime] = None
    connection_attempts: int = 0

class WhatsAppConnectionCreate(BaseModel):
    """Criar nova conexão WhatsApp"""
    name: str  # Nome da conexão (ex: "Suporte Principal")
    reseller_id: Optional[str] = None  # Opcional - será extraído do token se não fornecido
    max_received_daily: int = 200
    max_sent_daily: int = 200

class WhatsAppConnectionUpdate(BaseModel):
    """Atualizar conexão WhatsApp"""
    max_received_daily: Optional[int] = None
    max_sent_daily: Optional[int] = None
    is_active_for_rotation: Optional[bool] = None

# ==================== CONFIGURAÇÕES DA REVENDA ====================

class ResellerWhatsAppConfig(BaseModel):
    """Configurações WhatsApp da revenda"""
    reseller_id: str
    plan: str = "basico"  # basico, plus, pro, premium, enterprise
    
    # Mensagem de transferência (quando rotação acontece)
    transfer_message: str = "⏳ Sua mensagem está sendo transferida para outro atendente. Aguarde um momento..."
    
    # Configurações globais
    enable_rotation: bool = True  # Ativar rotação automática
    rotation_strategy: str = "round_robin"  # round_robin | least_used
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ResellerWhatsAppConfigUpdate(BaseModel):
    """Atualizar configurações WhatsApp"""
    plan: Optional[str] = None
    transfer_message: Optional[str] = None
    enable_rotation: Optional[bool] = None
    rotation_strategy: Optional[str] = None

# ==================== MENSAGENS ====================

class IncomingMessage(BaseModel):
    """Mensagem recebida do WhatsApp"""
    instance_name: str
    from_number: str  # Número do cliente
    message: str
    message_id: str
    timestamp: int
    media_url: Optional[str] = None

class OutgoingMessage(BaseModel):
    """Mensagem para enviar via WhatsApp"""
    reseller_id: str
    to_number: str
    message: str
    instance_name: Optional[str] = None  # Se não especificar, usa rotação

class MessageResponse(BaseModel):
    """Resposta de envio de mensagem"""
    success: bool
    message_id: Optional[str] = None
    instance_used: Optional[str] = None
    error: Optional[str] = None

# ==================== ESTATÍSTICAS ====================

class WhatsAppStats(BaseModel):
    """Estatísticas de uso WhatsApp"""
    reseller_id: str
    total_connections: int
    active_connections: int
    total_received_today: int
    total_sent_today: int
    connections: List[dict]  # Lista de conexões com stats

# ==================== QR CODE ====================

class QRCodeResponse(BaseModel):
    """Resposta com QR Code"""
    qr_code: Optional[str] = None
    instance_name: Optional[str] = None
    status: str
    expires_in: int = 60  # segundos
    message: Optional[str] = None  # Mensagem de erro ou informação

import uuid
