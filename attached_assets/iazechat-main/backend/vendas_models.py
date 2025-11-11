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
    
    # Novos campos para integração com sistema de atendimento
    ai_active: bool = True  # Se IA está ativa nesta conversa
    department_id: Optional[str] = None  # Departamento atribuído (quando redirecionado)
    agent_id: Optional[str] = None  # ID do atendente (quando assumido por humano)
    redirected_to_human: bool = False  # Se foi redirecionado para humano
    redirected_at: Optional[str] = None  # Quando foi redirecionado

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
    whatsapp: Optional[str] = None  # WhatsApp do cliente (opcional)
    name: Optional[str] = None  # Nome do cliente (opcional)

class VendasMessageRequest(BaseModel):
    """Request para enviar mensagem"""
    session_id: str
    text: str

class VendasMessageResponse(BaseModel):
    """Response com mensagens"""
    messages: List[dict]
    bot_state: str

class AIConversationMemory(BaseModel):
    """Memória de conversa da IA (temporária - 60 dias)"""
    session_id: str
    messages: List[dict]  # [{role: "user"/"assistant", content: str, timestamp: str}]
    metadata: Optional[dict] = {}  # Dispositivo, apps recomendados, etc
    created_at: str
    expires_at: str  # 60 dias depois
    
class AILearningFeedback(BaseModel):
    """Feedback de aprendizado (acertos/erros) - PERMANENTE"""
    id: str  # UUID
    session_id: str
    tipo: str  # "acerto" | "erro"
    categoria: str  # "recomendacao_app" | "problema_tecnico" | "vendas" | "outro"
    contexto: dict  # {cliente_pergunta, ia_resposta, dispositivo, etc}
    resultado: str  # Descrição do resultado
    marcado_por: str  # "sistema" | "atendente" | agent_id
    aprovado_admin: bool = False  # Se foi aprovado pelo admin/revenda
    agent_id: Optional[str] = None  # ID do agente IA relacionado
    created_at: str
    
class AIKnowledgePattern(BaseModel):
    """Padrão de conhecimento extraído do aprendizado"""
    id: str  # UUID
    agent_id: str  # ID do agente IA
    categoria: str
    padrao_sucesso: str  # Descrição do padrão
    exemplo_conversa: str
    vezes_usado_sucesso: int = 0
    vezes_usado_erro: int = 0
    taxa_sucesso: float = 0.0  # Calculado automaticamente
    criado_em: str
    atualizado_em: str
