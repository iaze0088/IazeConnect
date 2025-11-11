"""
Sistema de Lembretes de Vencimento por Email
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class ClientEmail(BaseModel):
    """Modelo para email de cliente"""
    id: str
    office_credential_id: str  # De qual Office veio
    usuario: str  # Usuário IPTV
    email: EmailStr
    nome: Optional[str] = None
    created_at: str
    active: bool = True

class ReminderConfig(BaseModel):
    """Configuração de lembretes"""
    id: str = "reminder_config"
    enabled: bool = True
    days_before: List[int] = [3, 2, 1]  # Enviar 3, 2 e 1 dia antes
    send_expired: bool = True  # Enviar para já vencidos
    send_time: str = "09:00"  # Horário de envio (HH:MM)
    
    # Configuração SMTP
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = ""
    from_name: str = "Atendimento"

class AddClientEmailRequest(BaseModel):
    """Request para adicionar email de cliente"""
    usuario: str
    email: EmailStr
    nome: Optional[str] = None
    office_credential_id: Optional[str] = None

class ReminderConfigUpdate(BaseModel):
    """Update de configuração"""
    enabled: Optional[bool] = None
    days_before: Optional[List[int]] = None
    send_expired: Optional[bool] = None
    send_time: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None
