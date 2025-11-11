"""
Models para Sistema de Vendas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class VendasSession(BaseModel):
    """Sessão anônima de vendas"""
    session_id: str  # UUID único
    created_at: str
    whatsapp: Optional[str] = None
    pin: Optional[str] = None
    converted: bool = False  # True quando virar cliente
    iptv_user: Optional[str] = None
    iptv_pass: Optional[str] = None
    iptv_expires_at: Optional[str] = None
    bot_state: str = "initial"  # initial, waiting_whatsapp, waiting_pin, completed
    reseller_id: Optional[str] = None

class VendasMessage(BaseModel):
    """Mensagem no chat de vendas"""
    message_id: str  # UUID
    session_id: str
    from_type: str  # "client" ou "bot" ou "agent"
    text: str
    timestamp: str
    metadata: Optional[dict] = {}

class VendasStartRequest(BaseModel):
    """Request para iniciar sessão"""
    pass

class VendasMessageRequest(BaseModel):
    """Request para enviar mensagem"""
    session_id: str
    text: str

class VendasMessageResponse(BaseModel):
    """Response com mensagens"""
    messages: List[dict]
    bot_state: str
