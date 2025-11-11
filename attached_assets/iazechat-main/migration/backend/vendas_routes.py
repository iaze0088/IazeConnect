"""
Rotas para Sistema de Vendas CyberTV com IA
"""
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid
from datetime import datetime, timezone
import logging

from vendas_models import (
    VendasStartRequest,
    VendasMessageRequest,
    VendasMessageResponse
)
from vendas_ai_service import vendas_ai_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vendas", tags=["vendas"])

def get_db():
    """Dependency para obter database"""
    from server import db
    return db

@router.post("/start")
async def start_vendas_session(
    request: VendasStartRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Iniciar nova sessão de vendas (anônima)
    Retorna session_id único
    """
    try:
        session_id = str(uuid.uuid4())
        
        # Buscar config
        config = await db.vendas_simple_config.find_one({"is_active": True})
        empresa_nome = config.get("empresa_nome", "CyberTV") if config else "CyberTV"
        
        # Criar sessão no banco
        session_data = {
            "session_id": session_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "empresa_nome": empresa_nome,
            "test_generated": False,
            "iptv_user": None,
            "iptv_pass": None
        }
        
        await db.vendas_sessions.insert_one(session_data)
        
        logger.info(f"✅ Nova sessão de vendas criada: {session_id}")
        
        # Buscar config para IA
        usa_ia = config.get("usa_ia", True) if config else True
        agent_id = config.get("agent_id") if config else None
        custom_instructions = config.get("custom_instructions") if config else None
        
        # Buscar configuração do agente de IA se especificado
        agent_config = None
        
        if agent_id:
            agent = await db.ai_agents.find_one({"id": agent_id}, {"_id": 0})
            if agent:
                agent_config = agent
        elif custom_instructions:
            agent_config = {
                "name": "WA Site Bot",
                "instructions": custom_instructions,
                "temperature": 0.7
            }
        
        # Mensagem inicial vazia ou da IA
        welcome_message_text = ""
        
        if usa_ia and agent_config:
            # IA gera mensagem inicial
            from vendas_ai_service import vendas_ai_service
            welcome_message_text, _, _ = await vendas_ai_service.get_ai_response(
                "Inicie a conversa",
                session_id,
                empresa_nome,
                agent_config=agent_config
            )
        else:
            # Sem IA = mensagem básica
            welcome_message_text = "Olá! Como posso ajudar?"
        
        # Salvar mensagem inicial
        welcome_message_id = str(uuid.uuid4())
        welcome_message = {
            "message_id": welcome_message_id,
            "session_id": session_id,
            "from_type": "bot",
            "text": welcome_message_text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "has_button": False,
            "button_text": None,
            "button_action": None
        }
        
        await db.vendas_messages.insert_one(welcome_message)
        
        return {
            "session_id": session_id,
            "messages": [{
                "message_id": welcome_message_id,
                "from_type": "bot",
                "text": welcome_message["text"],
                "timestamp": welcome_message["timestamp"],
                "has_button": False
            }]
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar sessão de vendas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/message")
async def send_vendas_message(
    request: VendasMessageRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Enviar mensagem no chat de vendas
    IA responde automaticamente
    """
    try:
        # Buscar sessão
        session = await db.vendas_sessions.find_one(
            {"session_id": request.session_id},
            {"_id": 0}
        )
        
        if not session:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        
        # Buscar config
        config = await db.vendas_simple_config.find_one({"is_active": True})
        usa_ia = config.get("usa_ia", True) if config else True
        empresa_nome = config.get("empresa_nome", "CyberTV") if config else "CyberTV"
        api_teste_url = config.get("api_teste_url") if config else "https://gesth.io/api/get-teste?hash=TG1OTW5QWHlaTW5Q"
        agent_id = config.get("agent_id") if config else None
        custom_instructions = config.get("custom_instructions") if config else None
        
        logger.info(f"📋 Config vendas: usa_ia={usa_ia}, agent_id={agent_id}, custom_instructions={'Sim' if custom_instructions else 'Não'}")
        
        # Buscar configuração do agente de IA se especificado
        agent_config = None
        
        if agent_id:
            agent = await db.ai_agents.find_one({"id": agent_id}, {"_id": 0})
            if agent:
                agent_config = agent
                logger.info(f"✅ Agente encontrado: {agent.get('name')} - Instruções: {agent.get('instructions')[:100] if agent.get('instructions') else 'Nenhuma'}...")
            else:
                logger.warning(f"⚠️ Agente {agent_id} não encontrado!")
        elif custom_instructions:
            # Criar config fake do agente com instruções customizadas
            agent_config = {
                "name": "WA Site Bot",
                "instructions": custom_instructions,
                "temperature": 0.7
            }
            logger.info(f"✅ Usando instruções customizadas do WA Site")
        else:
            logger.info("ℹ️ Nenhum agente ou instruções configuradas, usando prompt padrão")
        
        # Salvar mensagem do cliente
        client_message_id = str(uuid.uuid4())
        client_message = {
            "message_id": client_message_id,
            "session_id": request.session_id,
            "from_type": "client",
            "text": request.text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "has_button": False
        }
        
        await db.vendas_messages.insert_one(client_message)
        
        messages_to_return = [{
            "message_id": client_message_id,
            "from_type": "client",
            "text": request.text,
            "timestamp": client_message["timestamp"],
            "has_button": False
        }]
        
        # Obter resposta da IA
        if usa_ia:
            bot_text, should_show_button, button_action = await vendas_ai_service.get_ai_response(
                request.text,
                request.session_id,
                empresa_nome,
                agent_config=agent_config
            )
        else:
            bot_text = "Obrigado pela mensagem! Um atendente irá responder em breve."
            should_show_button = False
            button_action = None
        
        # Salvar mensagem do bot
        bot_message_id = str(uuid.uuid4())
        bot_message = {
            "message_id": bot_message_id,
            "session_id": request.session_id,
            "from_type": "bot",
            "text": bot_text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "has_button": should_show_button,
            "button_text": "🎁 CRIAR TESTE GRÁTIS" if should_show_button else None,
            "button_action": button_action
        }
        
        await db.vendas_messages.insert_one(bot_message)
        
        messages_to_return.append({
            "message_id": bot_message_id,
            "from_type": "bot",
            "text": bot_text,
            "timestamp": bot_message["timestamp"],
            "has_button": should_show_button,
            "button_text": "🎁 CRIAR TESTE GRÁTIS" if should_show_button else None,
            "button_action": button_action
        })
        
        return {"messages": messages_to_return}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao processar mensagem de vendas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/button-action")
async def handle_button_action(
    request: dict,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Processar ação de botão (ex: gerar teste)
    """
    try:
        session_id = request.get("session_id")
        action = request.get("action")
        
        if not session_id or not action:
            raise HTTPException(status_code=400, detail="session_id e action são obrigatórios")
        
        # Buscar sessão
        session = await db.vendas_sessions.find_one({"session_id": session_id})
        
        if not session:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        
        # Verificar se já gerou teste
        if session.get("test_generated"):
            return {
                "success": False,
                "message": "Você já gerou um teste! ⚠️"
            }
        
        # Buscar config
        config = await db.vendas_simple_config.find_one({"is_active": True})
        api_teste_url = config.get("api_teste_url") if config else "https://gesth.io/api/get-teste?hash=TG1OTW5QWHlaTW5Q"
        
        if action == "GERAR_TESTE":
            # Gerar teste via API
            result = await vendas_ai_service.generate_iptv_test(api_teste_url)
            
            if result["success"]:
                # Atualizar sessão
                await db.vendas_sessions.update_one(
                    {"session_id": session_id},
                    {"$set": {
                        "test_generated": True,
                        "iptv_user": result.get("usuario"),
                        "iptv_pass": result.get("senha")
                    }}
                )
                
                # Salvar mensagem com resultado
                bot_message_id = str(uuid.uuid4())
                bot_message = {
                    "message_id": bot_message_id,
                    "session_id": session_id,
                    "from_type": "bot",
                    "text": result["message"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "has_button": False
                }
                
                await db.vendas_messages.insert_one(bot_message)
                
                return {
                    "success": True,
                    "message": {
                        "message_id": bot_message_id,
                        "from_type": "bot",
                        "text": result["message"],
                        "timestamp": bot_message["timestamp"],
                        "has_button": False
                    }
                }
            else:
                return {
                    "success": False,
                    "message": result["message"]
                }
        
        raise HTTPException(status_code=400, detail="Ação inválida")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao processar ação de botão: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/save-contact")
async def save_contact(
    request: dict,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Salvar WhatsApp e PIN do cliente
    """
    try:
        session_id = request.get("session_id")
        whatsapp = request.get("whatsapp")
        pin = request.get("pin")
        
        if not session_id or not whatsapp or not pin:
            raise HTTPException(status_code=400, detail="Dados incompletos")
        
        # Atualizar sessão
        await db.vendas_sessions.update_one(
            {"session_id": session_id},
            {"$set": {
                "whatsapp": whatsapp,
                "pin": pin,
                "contact_saved": True,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        logger.info(f"✅ Contato salvo: {whatsapp} / PIN: {pin}")
        
        return {"success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao salvar contato: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages/{session_id}")
async def get_vendas_messages(
    session_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Obter todas as mensagens de uma sessão
    """
    try:
        messages = await db.vendas_messages.find(
            {"session_id": session_id},
            {"_id": 0}
        ).sort("timestamp", 1).to_list(length=None)
        
        return {"messages": messages}
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar mensagens: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session/{session_id}")
async def get_vendas_session(
    session_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Obter dados da sessão
    """
    try:
        session = await db.vendas_sessions.find_one(
            {"session_id": session_id},
            {"_id": 0}
        )
        
        if not session:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao buscar sessão: {e}")
        raise HTTPException(status_code=500, detail=str(e))
