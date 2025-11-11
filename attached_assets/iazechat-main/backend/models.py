from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum

class TicketStatus(str, Enum):
    EM_ESPERA = "EM_ESPERA"
    ATENDENDO = "ATENDENDO"
    FINALIZADAS = "FINALIZADAS"

class MessageKind(str, Enum):
    text = "text"
    image = "image"
    video = "video"
    audio = "audio"
    file = "file"
    pix = "pix"

class UserType(str, Enum):
    client = "client"
    agent = "agent"

# Notice recipient types
class NoticeRecipientType(str, Enum):
    ALL = "all"  # Todos (equipe + clientes)
    TEAM = "team"  # Apenas equipe (agentes)
    CLIENTS = "clients"  # Apenas clientes

# User Models
class UserBase(BaseModel):
    whatsapp: str
    display_name: Optional[str] = ""
    avatar: Optional[str] = ""
    custom_avatar: Optional[str] = ""
    gender: Optional[str] = ""
    pinned_user: Optional[str] = ""  # Credenciais PRIVADAS do cliente
    pinned_pass: Optional[str] = ""  # Credenciais PRIVADAS do cliente
    whatsapp_confirmed: Optional[str] = ""  # WhatsApp confirmado pelo cliente
    whatsapp_asked_at: Optional[str] = ""  # Última vez que perguntou WhatsApp
    name_asked_at: Optional[str] = ""  # Última vez que perguntou o nome
    reseller_id: Optional[str] = None  # Tenant isolation

class UserCreate(BaseModel):
    whatsapp: str
    pin: str

class UserLogin(BaseModel):
    whatsapp: str
    pin: str

class UserInDB(UserBase):
    id: str
    pin_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserResponse(UserBase):
    id: str
    created_at: datetime

class UserMeResponse(BaseModel):
    """Response model for /users/me endpoint"""
    id: str
    whatsapp: str
    display_name: str = ""
    avatar: str = ""
    custom_avatar: str = ""  # 🆕 Campo explícito  
    user_image: str = ""  # 🔬 Bypass gateway filter
    gender: str = ""
    pinned_user: str = ""
    pinned_pass: str = ""

# Agent Models
class AgentBase(BaseModel):
    name: str
    login: str
    avatar: Optional[str] = ""
    custom_avatar: Optional[str] = ""
    department_ids: List[str] = []  # Lista de departamentos que o atendente pode acessar
    reseller_id: Optional[str] = None  # Tenant isolation

class AgentCreate(BaseModel):
    name: str
    login: str
    password: str
    avatar: Optional[str] = ""
    department_ids: List[str] = []  # Departamentos do atendente

class AgentLogin(BaseModel):
    login: str
    password: str

class AgentInDB(AgentBase):
    id: str
    pass_hash: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AgentResponse(AgentBase):
    id: str
    created_at: datetime

# Ticket Models
class TicketBase(BaseModel):
    client_id: str
    status: TicketStatus = TicketStatus.EM_ESPERA
    department_id: Optional[str] = None  # Departamento do ticket
    awaiting_department_choice: bool = True  # Se está aguardando cliente escolher departamento
    department_choice_sent_at: Optional[str] = None  # Quando enviou a escolha de departamento
    unread_count: int = 0  # Contador de mensagens não lidas
    reseller_id: Optional[str] = None  # Tenant isolation
    whatsapp_instance: Optional[str] = None  # Nome da instância WhatsApp (se vier do WhatsApp)

class TicketInDB(TicketBase):
    id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TicketResponse(TicketBase):
    id: str
    created_at: datetime
    updated_at: datetime

# Message Models  
class MessageBase(BaseModel):
    ticket_id: str
    text: str
    kind: MessageKind = MessageKind.text
    from_type: str  # 'client', 'agent', or 'ai'
    from_id: str
    attachment_url: Optional[str] = None
    reseller_id: Optional[str] = None  # Tenant isolation
    read: bool = False  # Se a mensagem foi lida
    whatsapp_message_id: Optional[str] = None  # ID original da mensagem do WhatsApp

class MessageCreate(BaseModel):
    ticket_id: str
    text: str
    kind: MessageKind = MessageKind.text
    from_type: str
    from_id: str  # ID do remetente
    to_type: Optional[str] = None  # ✅ ADICIONAR to_type
    to_id: Optional[str] = None  # ✅ ADICIONAR to_id
    file_url: Optional[str] = None  # ✅ ADICIONAR file_url (estava como attachment_url)
    attachment_url: Optional[str] = None

class MessageInDB(MessageBase):
    id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MessageResponse(MessageBase):
    id: str
    created_at: datetime

# Config Models
class QuickBlock(BaseModel):
    name: str = ""  # Nome do bloco
    text: str       # Texto da mensagem

class AutoReply(BaseModel):
    keyword: str
    message: str

class IPTVApp(BaseModel):
    id: str
    name: str
    type: str  # 'SSIPTV', 'IPTV_SMARTERS', etc.
    config_url: str
    url_template: str
    fields: List[str]  # ['usuario', 'senha', 'dns']
    instructions: str

class AIAgent(BaseModel):
    name: str = "Assistente IA"
    personality: str = ""
    instructions: str = ""
    llm_provider: str = "openai"
    llm_model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 500
    mode: str = "standby"
    active_hours: str = "24/7"
    enabled: bool = False
    can_access_credentials: bool = True
    knowledge_base: str = ""

class AllowedData(BaseModel):
    cpfs: List[str] = []
    emails: List[str] = []
    phones: List[str] = []
    random_keys: List[str] = []
    allowed_messages: List[str] = []

class APIIntegration(BaseModel):
    api_url: str = ""
    api_token: str = ""
    api_enabled: bool = False

class ConfigData(BaseModel):
    quick_blocks: List[QuickBlock] = []
    auto_reply: List[AutoReply] = []
    apps: List[IPTVApp] = []
    support_avatar: Optional[str] = ""
    pix_key: str = ""
    manual_away_mode: bool = False  # Modo ausente manual
    away_message: str = "Estamos ausentes no momento. Por favor, aguarde que retornaremos em breve."  # Mensagem de ausência
    allowed_data: AllowedData = Field(default_factory=AllowedData)
    api_integration: APIIntegration = Field(default_factory=APIIntegration)
    ai_agent: AIAgent = Field(default_factory=AIAgent)
    ai_globally_enabled: bool = True  # 🆕 Controle global da IA (default: ativado)

# Notice Models
class NoticeBase(BaseModel):
    title: str
    message: str
    recipient_type: NoticeRecipientType = NoticeRecipientType.ALL  # Tipo de destinatário
    reseller_id: Optional[str] = None  # Tenant isolation

class NoticeCreate(BaseModel):
    title: str
    message: str
    recipient_type: NoticeRecipientType = NoticeRecipientType.ALL
    media_url: Optional[str] = None  # URL da mídia (foto/vídeo/áudio)
    media_type: Optional[str] = 'none'  # Tipo: 'none', 'photo', 'video', 'audio'

class NoticeInDB(NoticeBase):
    id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class NoticeResponse(NoticeBase):
    id: str
    created_at: datetime

# Department Models (AI Agents)
class DepartmentBase(BaseModel):
    name: str
    description: Optional[str] = ""
    ai_enabled: bool = False
    ai_config: Optional[dict] = None  # Pode conter: api_key, model, temperature, instructions, ai_memory_cleanup_days
    assigned_agents: List[str] = []  # Lista de agent_ids atribuídos
    ai_agent_id: Optional[str] = None  # ID do agente IA associado
    is_default: bool = False  # Se é o departamento padrão
    timeout_seconds: int = 300  # Timeout em segundos
    agent_ids: List[str] = []  # IDs dos agentes atribuídos (compatibilidade)
    origin: Optional[str] = "wa_suporte"  # Origem: "wa_suporte", "whatsapp_starter", "ia"
    reseller_id: Optional[str] = None  # Tenant isolation

class DepartmentCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    ai_enabled: bool = False
    ai_config: Optional[dict] = None
    assigned_agents: List[str] = []
    ai_agent_id: Optional[str] = None  # ID do agente IA associado
    is_default: bool = False  # Se é o departamento padrão
    timeout_seconds: int = 300  # Timeout em segundos
    agent_ids: List[str] = []  # IDs dos agentes atribuídos
    origin: Optional[str] = "wa_suporte"  # Origem do departamento

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    ai_enabled: Optional[bool] = None
    ai_config: Optional[dict] = None
    assigned_agents: Optional[List[str]] = None
    ai_agent_id: Optional[str] = None
    is_default: Optional[bool] = None
    timeout_seconds: Optional[int] = None
    agent_ids: Optional[List[str]] = None
    origin: Optional[str] = None

class DepartmentInDB(DepartmentBase):
    id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DepartmentResponse(DepartmentBase):
    id: str
    created_at: datetime

# Alias para compatibilidade
Department = DepartmentResponse

# Reseller Models
class ResellerBase(BaseModel):
    name: str
    email: str
    domain: str  # Domínio gerado automaticamente (ex: revenda1.suporte.help)
    custom_domain: Optional[str] = ""  # Domínio customizado (ex: ajuda.vip)
    is_active: bool = True
    parent_id: Optional[str] = None  # ID do revendedor pai (hierarquia)
    level: int = 1  # Nível na hierarquia (1 = raiz, 2 = filho, 3 = neto, etc)
    client_logo_url: Optional[str] = ""  # Logo personalizado para o cliente ver

class ResellerCreate(BaseModel):
    name: str
    email: str
    password: str
    custom_domain: Optional[str] = ""
    parent_id: Optional[str] = None

class ResellerLogin(BaseModel):
    email: str
    password: str

class ResellerInDB(ResellerBase):
    id: str
    pass_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ResellerResponse(ResellerBase):
    id: str
    created_at: datetime

# Admin Models
class AdminLogin(BaseModel):
    password: str

class TokenResponse(BaseModel):
    token: str
    user_type: str
    user_data: dict

# Transfer Models
class ResellerTransfer(BaseModel):
    reseller_id: str
    new_parent_id: Optional[str] = None

# AI Agent Models (Full)
class AIAgentCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    is_active: bool = False
    llm_provider: str = "openai"
    llm_model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 500
    instructions: str = ""
    knowledge_base: str = ""
    personality: str = ""
    schedule_start_time: Optional[str] = None  # Formato "HH:MM" ex: "08:00"
    schedule_end_time: Optional[str] = None    # Formato "HH:MM" ex: "18:00"

class AIAgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    api_key: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    instructions: Optional[str] = None
    knowledge_base: Optional[str] = None
    personality: Optional[str] = None
    schedule_start_time: Optional[str] = None  # Formato "HH:MM" ex: "08:00"
    schedule_end_time: Optional[str] = None    # Formato "HH:MM" ex: "18:00"
    # Campos adicionais para configuração detalhada
    who_is: Optional[str] = None
    what_does: Optional[str] = None
    objective: Optional[str] = None
    how_respond: Optional[str] = None
    avoid_topics: Optional[str] = None
    avoid_words: Optional[str] = None
    allowed_links: Optional[str] = None
    custom_rules: Optional[str] = None
    auto_detect_language: Optional[bool] = None
    knowledge_restriction: Optional[bool] = None
    timezone: Optional[str] = None
    linked_agents: Optional[List[str]] = None

class AIAgentFull(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    is_active: bool = False
    llm_provider: str = "openai"
    llm_model: str = "gpt-4"
    api_key: Optional[str] = ""
    temperature: float = 0.7
    max_tokens: int = 500
    instructions: str = ""
    knowledge_base: str = ""
    personality: str = ""
    schedule_start_time: Optional[str] = None  # Formato "HH:MM" ex: "08:00"
    schedule_end_time: Optional[str] = None    # Formato "HH:MM" ex: "18:00"
    # Campos adicionais para configuração detalhada
    who_is: Optional[str] = ""
    what_does: Optional[str] = ""
    objective: Optional[str] = ""
    how_respond: Optional[str] = ""
    avoid_topics: Optional[str] = ""
    avoid_words: Optional[str] = ""
    allowed_links: Optional[str] = ""
    custom_rules: Optional[str] = ""
    auto_detect_language: Optional[bool] = True
    knowledge_restriction: Optional[bool] = False
    timezone: Optional[str] = "America/Sao_Paulo"
    linked_agents: Optional[List[str]] = []
    reseller_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None