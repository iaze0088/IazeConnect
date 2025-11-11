"""
Models para Configuração do Bot de Vendas
"""
from pydantic import BaseModel
from typing import Optional, List

class BotFlowStep(BaseModel):
    """Etapa do fluxo do bot"""
    step_id: str
    step_name: str
    trigger_keywords: List[str]  # Palavras que ativam essa etapa
    bot_message: str  # Mensagem que o bot envia
    next_step: Optional[str] = None  # ID da próxima etapa
    requires_validation: bool = False  # Se precisa validar input
    validation_type: Optional[str] = None  # "whatsapp", "pin", "whatsapp_pin"
    action: Optional[str] = None  # "generate_test", "save_data", etc

class BotFlowConfig(BaseModel):
    """Configuração completa do fluxo do bot"""
    config_id: str
    name: str
    is_active: bool
    initial_message: str
    steps: List[BotFlowStep]
    reseller_id: Optional[str] = None  # Null = global (admin)
    created_at: str
    updated_at: str

class BotFlowStepRequest(BaseModel):
    """Request para criar/editar etapa"""
    step_name: str
    trigger_keywords: List[str]
    bot_message: str
    next_step: Optional[str] = None
    requires_validation: bool = False
    validation_type: Optional[str] = None
    action: Optional[str] = None

class BotFlowConfigRequest(BaseModel):
    """Request para criar/editar configuração"""
    name: str
    is_active: bool
    initial_message: str
    steps: List[BotFlowStepRequest]
