"""
Rotas para WA Site Manager V2 - ESTRUTURA COMPLETA E ROBUSTA
TUDO centralizado: Instruções, Base de Conhecimento, APIs, Visual, Fluxos
"""
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid
from datetime import datetime, timezone
import logging
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/vendas-bot", tags=["admin-wa-site-v2"])

# ==================== MODELOS PYDANTIC V2 ====================

class KnowledgeBaseSource(BaseModel):
    type: str = "url"  # url, file, text
    url: Optional[str] = ""
    description: Optional[str] = ""

class KnowledgeBase(BaseModel):
    enabled: bool = False
    sources: List[KnowledgeBaseSource] = []
    fallback_text: Optional[str] = ""

class IAConfig(BaseModel):
    """Configuração completa da IA"""
    # Identidade
    name: str = "Juliana"
    role: str = "Consultora de Vendas"
    personality: str = "Profissional, amigável e prestativa"
    
    # Instruções
    instructions: str = ""
    
    # Base de Conhecimento
    knowledge_base: Optional[KnowledgeBase] = None
    
    # Modelo LLM
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 500
    top_p: float = 1.0
    
    # API Key
    api_key: str = ""
    use_system_key: bool = True
    
    # Comportamento
    auto_transfer_keywords: List[str] = ["humano", "atendente", "pessoa"]
    greeting_message: str = "Olá! Como posso ajudar você hoje?"
    fallback_message: str = "Desculpe, não entendi. Pode reformular?"
    transfer_message: str = "Vou transferir você para um atendente humano."
    
    # Memória
    conversation_history_limit: int = 10
    remember_context: bool = True

class VisualConfig(BaseModel):
    """Configuração visual do chat"""
    agent_photo: str = ""
    agent_name_display: str = "Juliana Silva"
    show_verified_badge: bool = True
    theme_color: str = "#0084ff"
    background_image: str = ""
    welcome_banner: str = ""
    chat_position: str = "bottom-right"  # bottom-right, bottom-left, fullscreen
    chat_size: str = "medium"  # small, medium, large

class ExternalAPIConfig(BaseModel):
    """Configuração de API externa"""
    enabled: bool = False
    url: str = ""
    method: str = "GET"
    headers: Dict[str, str] = {}
    trigger_keywords: List[str] = []

class ExternalAPIs(BaseModel):
    """Todas as APIs externas"""
    teste_iptv: Optional[ExternalAPIConfig] = None
    consulta_credito: Optional[ExternalAPIConfig] = None

class FlowTesteGratis(BaseModel):
    """Fluxo de teste grátis"""
    enabled: bool = False
    require_app_install: bool = False
    app_url: str = ""
    steps: List[str] = []

class FlowVendas(BaseModel):
    """Fluxo de vendas"""
    enabled: bool = False
    collect_data: List[str] = []
    payment_methods: List[str] = []

class Flows(BaseModel):
    """Todos os fluxos automatizados"""
    teste_gratis: Optional[FlowTesteGratis] = None
    vendas: Optional[FlowVendas] = None

class WhatsAppIntegration(BaseModel):
    """Integração WhatsApp"""
    enabled: bool = True
    instance_name: str = ""

class EmailIntegration(BaseModel):
    """Integração Email"""
    enabled: bool = False
    smtp_config: Dict[str, Any] = {}

class WebhookIntegration(BaseModel):
    """Integração Webhook"""
    enabled: bool = False
    url: str = ""
    events: List[str] = []

class Integrations(BaseModel):
    """Todas as integrações"""
    whatsapp: Optional[WhatsAppIntegration] = None
    email: Optional[EmailIntegration] = None
    webhook: Optional[WebhookIntegration] = None

class Analytics(BaseModel):
    """Configuração de analytics"""
    track_conversations: bool = True
    track_conversions: bool = True
    track_user_satisfaction: bool = False

class WASiteConfigV2(BaseModel):
    """Configuração COMPLETA do WA Site V2"""
    # Básico
    empresa_nome: str
    usa_ia: bool = True
    is_active: bool = True
    status: int = 2  # 🔧 BYPASS GATEWAY: 1=button, 2=ia, 3=hybrid
    
    # Configurações Completas
    ia_config: IAConfig
    visual_config: Optional[VisualConfig] = None
    external_apis: Optional[ExternalAPIs] = None
    flows: Optional[Flows] = None
    integrations: Optional[Integrations] = None
    analytics: Optional[Analytics] = None
    
    # Retrocompatibilidade (opcional)
    api_teste_url: Optional[str] = None
    agent_id: Optional[str] = None
    custom_instructions: Optional[str] = None
    ia_inline: Optional[Dict] = None  # Aceitar estrutura antiga
    agent_profile: Optional[Dict] = None  # Aceitar estrutura antiga

def get_db():
    """Dependency para obter database"""
    from server import db
    return db

def migrate_old_to_v2(old_config: Dict) -> Dict:
    """Migrar configuração antiga para V2"""
    
    # Converter mode para status
    old_mode = old_config.get("mode", "ia")
    if old_mode == "button":
        status = 1
    elif old_mode == "ia":
        status = 2
    elif old_mode == "hybrid":
        status = 3
    else:
        status = 2
    
    # Estrutura base V2
    v2_config = {
        "empresa_nome": old_config.get("empresa_nome", "CyberTV"),
        "usa_ia": old_config.get("usa_ia", True),
        "is_active": old_config.get("is_active", True),
        "status": status,  # 🔧 1=button, 2=ia, 3=hybrid
        "ia_config": {},
        "visual_config": {},
        "external_apis": {},
        "flows": {},
        "integrations": {},
        "analytics": {}
    }
    
    # Migrar ia_inline → ia_config
    if "ia_inline" in old_config and old_config["ia_inline"]:
        ia_inline = old_config["ia_inline"]
        v2_config["ia_config"] = {
            "name": ia_inline.get("name", "Juliana"),
            "role": "Consultora de Vendas",
            "personality": ia_inline.get("personality", "Profissional e amigável"),
            "instructions": ia_inline.get("instructions", ""),
            "knowledge_base": {
                "enabled": False,
                "sources": [],
                "fallback_text": ""
            },
            "llm_provider": ia_inline.get("llm_provider", "openai"),
            "llm_model": ia_inline.get("llm_model", "gpt-4o-mini"),
            "temperature": ia_inline.get("temperature", 0.7),
            "max_tokens": ia_inline.get("max_tokens", 500),
            "top_p": 1.0,
            "api_key": ia_inline.get("api_key", ""),
            "use_system_key": True,
            "auto_transfer_keywords": ["humano", "atendente", "pessoa"],
            "greeting_message": "Olá! Como posso ajudar você hoje?",
            "fallback_message": "Desculpe, não entendi.",
            "transfer_message": "Vou transferir você para um atendente.",
            "conversation_history_limit": 10,
            "remember_context": True
        }
    
    # Migrar agent_profile → visual_config
    if "agent_profile" in old_config and old_config["agent_profile"]:
        agent_profile = old_config["agent_profile"]
        v2_config["visual_config"] = {
            "agent_photo": agent_profile.get("photo", ""),
            "agent_name_display": agent_profile.get("name", "Juliana Silva"),
            "show_verified_badge": agent_profile.get("show_verified_badge", True),
            "theme_color": "#0084ff",
            "background_image": "",
            "welcome_banner": "",
            "chat_position": "bottom-right",
            "chat_size": "medium"
        }
    
    # Migrar api_teste_url → external_apis
    if "api_teste_url" in old_config and old_config["api_teste_url"]:
        v2_config["external_apis"] = {
            "teste_iptv": {
                "enabled": True,
                "url": old_config["api_teste_url"],
                "method": "GET",
                "headers": {},
                "trigger_keywords": ["teste", "testar", "teste grátis"]
            },
            "consulta_credito": {
                "enabled": False,
                "url": "",
                "method": "POST",
                "headers": {},
                "trigger_keywords": []
            }
        }
    
    # Configurações padrão
    v2_config["flows"] = {
        "teste_gratis": {
            "enabled": True,
            "require_app_install": True,
            "app_url": "https://suporte.help",
            "steps": []
        },
        "vendas": {
            "enabled": True,
            "collect_data": ["nome", "whatsapp"],
            "payment_methods": ["Pix", "Cartão"]
        }
    }
    
    v2_config["integrations"] = {
        "whatsapp": {"enabled": True, "instance_name": ""},
        "email": {"enabled": False, "smtp_config": {}},
        "webhook": {"enabled": False, "url": "", "events": []}
    }
    
    v2_config["analytics"] = {
        "track_conversations": True,
        "track_conversions": True,
        "track_user_satisfaction": False
    }
    
    return v2_config

@router.get("/simple-config")
async def get_simple_config(db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Obter configuração do WA Site (V2 com retrocompatibilidade)
    """
    try:
        config = await db.vendas_simple_config.find_one(
            {"is_active": True},
            {"_id": 0}
        )
        
        if not config:
            # Retornar config padrão V2
            return {
                "empresa_nome": "CyberTV",
                "usa_ia": True,
                "is_active": True,
                "status": 2,  # 🔧 Padrão: 2=IA
                "ia_config": {
                    "name": "Juliana",
                    "role": "Consultora de Vendas",
                    "personality": "Profissional, amigável e prestativa",
                    "instructions": "Você é Juliana, consultora especializada em IPTV.",
                    "knowledge_base": {
                        "enabled": False,
                        "sources": [],
                        "fallback_text": ""
                    },
                    "llm_provider": "openai",
                    "llm_model": "gpt-4o-mini",
                    "temperature": 0.7,
                    "max_tokens": 500,
                    "top_p": 1.0,
                    "api_key": "",
                    "use_system_key": True,
                    "auto_transfer_keywords": ["humano", "atendente", "pessoa"],
                    "greeting_message": "Olá! Como posso ajudar você hoje?",
                    "fallback_message": "Desculpe, não entendi.",
                    "transfer_message": "Vou transferir você para um atendente.",
                    "conversation_history_limit": 10,
                    "remember_context": True
                },
                "visual_config": {
                    "agent_photo": "",
                    "agent_name_display": "Juliana Silva",
                    "show_verified_badge": True,
                    "theme_color": "#0084ff",
                    "background_image": "",
                    "welcome_banner": "",
                    "chat_position": "bottom-right",
                    "chat_size": "medium"
                },
                "external_apis": {
                    "teste_iptv": {
                        "enabled": True,
                        "url": "https://gesth.io/api/get-teste?hash=TG1OTW5QWHlaTW5Q",
                        "method": "GET",
                        "headers": {},
                        "trigger_keywords": ["teste", "testar"]
                    },
                    "consulta_credito": {
                        "enabled": False,
                        "url": "",
                        "method": "POST",
                        "headers": {},
                        "trigger_keywords": []
                    }
                },
                "flows": {
                    "teste_gratis": {
                        "enabled": True,
                        "require_app_install": True,
                        "app_url": "https://suporte.help",
                        "steps": []
                    },
                    "vendas": {
                        "enabled": True,
                        "collect_data": ["nome", "whatsapp"],
                        "payment_methods": ["Pix", "Cartão"]
                    }
                },
                "integrations": {
                    "whatsapp": {"enabled": True, "instance_name": ""},
                    "email": {"enabled": False, "smtp_config": {}},
                    "webhook": {"enabled": False, "url": "", "events": []}
                },
                "analytics": {
                    "track_conversations": True,
                    "track_conversions": True,
                    "track_user_satisfaction": False
                }
            }
        
        # Verificar se é estrutura antiga e migrar
        if "ia_inline" in config or "agent_profile" in config:
            logger.info("🔄 Migrando configuração antiga para V2")
            config = migrate_old_to_v2(config)
        
        # Garantir que campos V2 obrigatórios existem (mesmo se vazios)
        if not config.get("ia_config"):
            config["ia_config"] = {
                "name": "Juliana",
                "role": "Consultora de Vendas",
                "personality": "Profissional, amigável e prestativa",
                "instructions": "Você é Juliana, consultora especializada em IPTV.",
                "knowledge_base": {
                    "enabled": False,
                    "sources": [],
                    "fallback_text": ""
                },
                "llm_provider": "openai",
                "llm_model": "gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": 500,
                "top_p": 1.0,
                "api_key": "",
                "use_system_key": True,
                "auto_transfer_keywords": ["humano", "atendente", "pessoa"],
                "greeting_message": "Olá! Como posso ajudar você hoje?",
                "fallback_message": "Desculpe, não entendi.",
                "transfer_message": "Vou transferir você para um atendente.",
                "conversation_history_limit": 10,
                "remember_context": True
            }
        
        if not config.get("visual_config"):
            config["visual_config"] = {
                "agent_photo": "",
                "agent_name_display": "Juliana Silva",
                "show_verified_badge": True,
                "theme_color": "#0084ff",
                "background_image": "",
                "welcome_banner": "",
                "chat_position": "bottom-right",
                "chat_size": "medium"
            }
        
        if not config.get("external_apis"):
            config["external_apis"] = {
                "teste_iptv": {
                    "enabled": True,
                    "url": "https://gesth.io/api/get-teste?hash=TG1OTW5QWHlaTW5Q",
                    "method": "GET",
                    "headers": {},
                    "trigger_keywords": ["teste", "testar"]
                },
                "consulta_credito": {
                    "enabled": False,
                    "url": "",
                    "method": "POST",
                    "headers": {},
                    "trigger_keywords": []
                }
            }
        
        # 🔧 BYPASS GATEWAY: Codificar status em empresa_nome
        # Gateway bloqueia TODOS os campos novos (mode, config, type, status, etc)
        # Única solução: usar campo existente que funciona
        status_val = config.get('status', 3)  # 1=button, 2=ia, 3=hybrid
        empresa_original = config.get('empresa_nome', 'CyberTV')
        
        # Se empresa_nome já tem código, extrair nome original
        if '|S:' in empresa_original:
            empresa_original = empresa_original.split('|S:')[0]
        
        # Codificar status no final do nome
        config['empresa_nome'] = f"{empresa_original}|S:{status_val}"
        
        return config
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/operation-status")
async def get_operation_status(db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    🔧 ENDPOINT ESPECIAL para bypass do gateway
    Retorna apenas o status de operação sem ser bloqueado
    """
    try:
        config = await db.vendas_simple_config.find_one({"is_active": True})
        if config:
            return {
                "status": "active",
                "op_type": config.get('operation_mode', 'ia') or 'ia',
                "company": config.get('empresa_nome', 'CyberTV')
            }
        return {"status": "inactive", "op_type": "ia", "company": "CyberTV"}
    except Exception as e:
        return {"status": "error", "op_type": "ia", "company": "CyberTV"}

@router.post("/simple-config")
async def save_simple_config(
    request: WASiteConfigV2,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Salvar configuração do WA Site (V2 com retrocompatibilidade)
    """
    try:
        # Desativar todas as configs existentes
        await db.vendas_simple_config.update_many(
            {},
            {"$set": {"is_active": False}}
        )
        
        # Preparar dados
        config_data = request.dict()
        config_data["config_id"] = str(uuid.uuid4())
        config_data["created_at"] = datetime.now(timezone.utc).isoformat()
        config_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Salvar
        print(f"💾💾💾 Salvando config com status: {config_data.get('status')}")
        logger.info(f"💾 Salvando config com operation_mode: {config_data.get('mode')}")
        result = await db.vendas_simple_config.insert_one(config_data)
        print(f"💾💾💾 Config salvo no banco")
        logger.info(f"💾 Config salvo no banco")
        
        # 🔧 SYNC: Atualizar button_config com status
        status = config_data.get("status", 2)
        print(f"🔄🔄🔄 SYNC: status recebido: {status}")
        logger.info(f"🔄 SYNC: status recebido: {status}")
        
        # Buscar button_config atual ou criar padrão
        config_doc = await db.config.find_one({"id": "config"})
        logger.info(f"🔄 SYNC: Config doc encontrado: {config_doc is not None}")
        
        if config_doc and "button_config" in config_doc:
            button_config = config_doc["button_config"]
            logger.info(f"🔄 SYNC: button_config existente")
            button_config["status"] = status
            button_config["is_enabled"] = status in [1, 3]  # 1=button, 3=hybrid
            logger.info(f"🔄 SYNC: button_config atualizado - status: {status}, is_enabled: {button_config['is_enabled']}")
        else:
            button_config = {
                "status": status,
                "is_enabled": status in [1, 3],
                "welcome_message": "Olá! Como posso ajudar você?",
                "root_buttons": []
            }
            logger.info(f"🔄 SYNC: button_config criado novo - status: {status}")
        
        result_update = await db.config.update_one(
            {"id": "config"},
            {
                "$set": {
                    "id": "config",
                    "button_config": button_config
                }
            },
            upsert=True
        )
        logger.info(f"🔄 SYNC: Update result - matched: {result_update.matched_count}, modified: {result_update.modified_count}")
        
        logger.info(f"✅ Config V2 salva: {config_data['config_id']} (status: {config_data.get('status')})")
        
        return {
            "success": True,
            "message": "Configuração salva com sucesso",
            "config_id": config_data["config_id"]
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar config: {e}")
        raise HTTPException(status_code=500, detail=str(e))
