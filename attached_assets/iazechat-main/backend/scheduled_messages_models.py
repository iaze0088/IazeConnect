"""
Sistema de Agendamento de Mensagens
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)

class ScheduledMessage(BaseModel):
    """Modelo para mensagem agendada"""
    id: str
    ticket_id: str
    agent_id: str
    message: str
    scheduled_datetime: str  # ISO format
    created_at: str
    status: str = "pending"  # pending, sent, failed, cancelled
    sent_at: Optional[str] = None
    channel: str  # "whatsapp_evolution", "wa_suporte_pwa", "iaze_internal"

class ScheduleMessageRequest(BaseModel):
    """Request para agendar mensagem"""
    ticket_id: str
    message: str
    schedule_type: str  # "datetime" ou "relative"
    
    # Para agendamento por data/hora
    datetime: Optional[str] = None  # "2025-11-25T14:00:00"
    
    # Para agendamento relativo
    hours: Optional[int] = None
    minutes: Optional[int] = None
