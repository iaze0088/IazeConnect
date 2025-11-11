"""
Rotas para Sistema de Vendas CyberTV com IA
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid
from datetime import datetime, timezone
import logging

from vendas_models import (
    VendasStartRequest,
    VendasMessageRequest,
    VendasMessageResponse
)
from vendas_ai_humanized import humanized_vendas_ai  # 🆕 IA HUMANIZADA REAL
from vendas_ai_service import vendas_ai_service  # Fallback para Flow 12
from vendas_buttons_service import ButtonsService  # 🆕 Sistema de Botões

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
        
        # Buscar config (CORRIGIDO: buscar primeiro documento)
        config = await db.vendas_simple_config.find_one({})
        
        if not config:
            logger.warning("⚠️ Nenhuma configuração encontrada, usando valores padrão")
            config = {}
        
        empresa_nome = config.get("empresa_nome", "CyberTV")
        
        # 🆕 SISTEMA DE BOTÕES: Buscar configuração de botões
        buttons_service = ButtonsService(db)
        button_config = await buttons_service.get_config()
        logger.info(f"🔘 Button config loaded - enabled: {button_config.is_enabled}, mode: {button_config.status}, buttons: {len(button_config.root_buttons)}")
        
        # Criar sessão no banco
        session_data = {
            "session_id": session_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_message_at": datetime.now(timezone.utc).isoformat(),
            "empresa_nome": empresa_nome,
            "test_generated": False,
            "iptv_user": None,
            "iptv_pass": None,
            "ai_active": True,  # IA ativa por padrão
            "status": "active",  # Sessão ativa
            "whatsapp": request.whatsapp if request.whatsapp else None,  # Salvar WhatsApp se fornecido
            "client_name": request.name if request.name else None  # Salvar Nome se fornecido
        }
        
        await db.vendas_sessions.insert_one(session_data)
        
        # Log do WhatsApp e Nome se fornecidos
        if request.whatsapp:
            logger.info(f"📱 WhatsApp associado à sessão: {request.whatsapp}")
        if request.name:
            logger.info(f"👤 Nome associado à sessão: {request.name}")
        
        logger.info(f"✅ Nova sessão de vendas criada: {session_id}")
        
        # Buscar config para IA
        usa_ia = config.get("usa_ia", True)
        agent_id = config.get("agent_id")
        custom_instructions = config.get("custom_instructions")
        ia_inline = config.get("ia_inline")  # 🆕 Config inline da IA
        
        logger.info(f"📋 Config /start: usa_ia={usa_ia}, agent_id={agent_id}, ia_inline={'Sim' if ia_inline else 'Não'}")
        
        # Buscar configuração do agente de IA
        agent_config = None
        
        # PRIORIDADE 1: ia_inline (mais recente)
        if ia_inline and (ia_inline.get('instructions') or ia_inline.get('instructions_file') or ia_inline.get('instructions_url')):
            agent_config = {
                "name": ia_inline.get('name', 'WA Site Bot'),
                "instructions": ia_inline.get('instructions', ''),
                "instructions_file": ia_inline.get('instructions_file', ''),
                "instructions_url": ia_inline.get('instructions_url', ''),
                "personality": ia_inline.get('personality', ''),
                "temperature": ia_inline.get('temperature', 0.7),
                "llm_model": ia_inline.get('llm_model', 'gpt-4o-mini'),
                "api_key": ia_inline.get('api_key', '')
            }
            logger.info(f"✅ /start usando IA INLINE: {agent_config.get('name')}")
        
        # PRIORIDADE 2: agent_id
        elif agent_id:
            agent = await db.ai_agents.find_one({"id": agent_id}, {"_id": 0})
            if agent:
                agent_config = agent
                logger.info("✅ /start usando AGENT_ID")
        
        # PRIORIDADE 3: custom_instructions (legado)
        elif custom_instructions:
            agent_config = {
                "name": "WA Site Bot",
                "instructions": custom_instructions,
                "temperature": 0.7
            }
            logger.info("✅ /start usando CUSTOM_INSTRUCTIONS")
        
        # Mensagem inicial vazia ou da IA
        welcome_message_text = ""
        
        if usa_ia and agent_config:
            # 🚀 OTIMIZAÇÃO: Usar mensagem de boas-vindas configurada em vez de chamar IA
            # Chamar IA na primeira mensagem do usuário para economizar tempo/tokens
            welcome_message_text = agent_config.get('greeting_message', config.get('initial_message', 'Olá! Como posso ajudar você hoje?'))
            logger.info("✅ /start usando mensagem de boas-vindas pré-configurada (otimização)")
        else:
            # Sem IA = mensagem básica
            welcome_message_text = config.get('initial_message', "Olá! Como posso ajudar?")
        
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
        
        # 🔧 BYPASS GATEWAY V3: Dividir button_config em múltiplas mensagens "sistema"
        # Gateway bloqueia TUDO: campos customizados E conteúdo dentro de text
        # Única solução: criar mensagens "sistema" invisíveis que o gateway não filtra
        import json
        import base64
        
        print(f"🔍 button_config.is_enabled: {button_config.is_enabled}")
        print(f"🔍 button_config.status: {button_config.status}")
        print(f"🔍 button_config.root_buttons: {len(button_config.root_buttons)}")
        
        # ✅ SOLUÇÃO FINAL: Retornar apenas mensagem de boas-vindas
        # Button config será buscado via endpoint separado /api/vendas/config
        
        first_message = {
            "message_id": welcome_message_id,
            "from_type": "bot",
            "text": welcome_message["text"],
            "timestamp": welcome_message["timestamp"],
            "has_button": False
        }
        
        response_data = {
            "session_id": session_id,
            "messages": [first_message]
        }
        
        logger.info(f"✅ Sessão criada: {session_id}")
        
        return response_data
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar sessão de vendas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config")
async def get_vendas_config(db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    🆕 ENDPOINT SEPARADO: Obter configuração de botões do WA Site
    Solução para bypass do API Gateway que filtra campos customizados
    """
    try:
        # Buscar configuração de botões
        buttons_service = ButtonsService(db)
        button_config = await buttons_service.get_config()
        
        logger.info(f"📋 Config solicitada - status: {button_config.status}, enabled: {button_config.is_enabled}")
        
        # Preparar resposta completa
        config_response = {
            "status": button_config.status,  # 1=button, 2=ia, 3=hybrid
            "is_enabled": button_config.is_enabled,
            "welcome_message": button_config.welcome_message,
            "buttons": [b.dict() for b in button_config.root_buttons] if button_config.root_buttons else [],
            # 🆕 Personalização do bot
            "bot_name": button_config.bot_name if hasattr(button_config, 'bot_name') else "Assistente Virtual",
            "bot_avatar_url": button_config.bot_avatar_url if hasattr(button_config, 'bot_avatar_url') else None
        }
        
        logger.info(f"✅ Retornando config com {len(config_response['buttons'])} botões")
        
        return config_response
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar config: {e}")
        # Retornar config padrão em caso de erro
        return {
            "status": 2,  # IA por padrão
            "is_enabled": False,
            "welcome_message": "Olá! Como posso ajudar você?",
            "buttons": []
        }

@router.post("/message")
async def send_vendas_message(
    request: VendasMessageRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Enviar mensagem no chat de vendas
    IA responde automaticamente
    """
    # DEBUG: Gravar em arquivo temporário
    with open("/tmp/vendas_debug.log", "a") as f:
        f.write(f"🚀 /MESSAGE CHAMADA! Sessão: {request.session_id}, Texto: {request.text}\n")
    
    print(f"🚀🚀🚀 /MESSAGE CHAMADA! Sessão: {request.session_id}, Texto: {request.text}")
    logger.info(f"🚀 /MESSAGE CHAMADA! Sessão: {request.session_id}, Texto: {request.text}")
    try:
        print("CHECKPOINT A: Dentro do try")
        # Buscar sessão
        print("CHECKPOINT B: Antes de buscar sessão")
        session = await db.vendas_sessions.find_one(
            {"session_id": request.session_id},
            {"_id": 0}
        )
        
        print("CHECKPOINT C: Sessão buscada")
        
        if not session:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        
        print("CHECKPOINT D: Sessão válida")
        # Buscar config (CORRIGIDO: buscar primeiro documento, não por is_active)
        config = await db.vendas_simple_config.find_one({})
        print("CHECKPOINT E: Config buscada")
        
        if not config:
            logger.error("❌ NENHUMA CONFIGURAÇÃO ENCONTRADA NO BANCO!")
            config = {}
        
        usa_ia = config.get("usa_ia", True)
        agent_id = config.get("agent_id")
        custom_instructions = config.get("custom_instructions")
        ia_inline = config.get("ia_inline")  # 🆕 Config inline da IA
        
        logger.info(f"📋 Config encontrada: _id={config.get('_id')}")
        logger.info(f"📋 Config vendas: usa_ia={usa_ia}, agent_id={agent_id}, ia_inline={'Sim' if ia_inline else 'Não'}")
        
        # Buscar configuração do agente de IA
        agent_config = None
        
        # PRIORIDADE 1: ia_inline (mais recente)
        if ia_inline and (ia_inline.get('instructions') or ia_inline.get('instructions_file') or ia_inline.get('instructions_url')):
            agent_config = {
                "name": ia_inline.get('name', 'WA Site Bot'),
                "instructions": ia_inline.get('instructions', ''),
                "instructions_file": ia_inline.get('instructions_file', ''),  # 🆕 Arquivo .txt
                "instructions_url": ia_inline.get('instructions_url', ''),    # 🆕 URL externa
                "personality": ia_inline.get('personality', ''),
                "temperature": ia_inline.get('temperature', 0.7),
                "llm_model": ia_inline.get('llm_model', 'gpt-4o-mini'),
                "api_key": ia_inline.get('api_key', '')  # 🔑 API Key inline
            }
            logger.info(f"✅ Usando IA INLINE: {agent_config.get('name')} - API Key: {'Configurada' if agent_config.get('api_key') else 'FALTANDO'}")
            logger.info(f"📋 Fontes configuradas - File: {ia_inline.get('instructions_file')}, URL: {ia_inline.get('instructions_url')}")
        
        # PRIORIDADE 2: agent_id (agente criado na aba Agentes IA)
        elif agent_id:
            agent = await db.ai_agents.find_one({"id": agent_id}, {"_id": 0})
            if agent:
                agent_config = agent
                logger.info(f"✅ Agente encontrado: {agent.get('name')} - Instruções: {agent.get('instructions')[:100] if agent.get('instructions') else 'Nenhuma'}...")
            else:
                logger.warning(f"⚠️ Agente {agent_id} não encontrado!")
        
        # PRIORIDADE 3: custom_instructions (legado)
        elif custom_instructions:
            # Criar config fake do agente com instruções customizadas
            agent_config = {
                "name": "WA Site Bot",
                "instructions": custom_instructions,
                "temperature": 0.7
            }
            logger.info("✅ Usando instruções customizadas do WA Site (legado)")
        else:
            logger.info("ℹ️ Nenhum agente ou instruções configuradas, usando prompt padrão")
        
        # 🆕 VERIFICAR SISTEMA DE BOTÕES ANTES DE PROCESSAR (VERSÃO SIMPLIFICADA)
        button_config_doc = await db.config.find_one({"id": "config"}, {"button_config": 1})
        
        # Valores padrão
        button_enabled = False
        status = 2
        
        if button_config_doc and "button_config" in button_config_doc:
            btn_cfg = button_config_doc["button_config"]
            button_enabled = btn_cfg.get("is_enabled", False)
            status = btn_cfg.get("mode", "ia")
        
        print(f"🔘🔘🔘 Button config - Enabled: {button_enabled}, Mode: {status}")
        logger.info(f"🔘 Button config - Enabled: {button_enabled}, Mode: {status}")
        
        # Se modo = "button" (apenas botões), NÃO processar como mensagem de texto normal
        # Espera-se que o frontend envie via /api/vendas/button-click
        if button_enabled and status == 1:
            logger.warning(f"🚫 MODO BUTTON ATIVO - IA BLOQUEADA! Cliente tentou enviar texto: '{request.text}'")
            
            # Salvar mensagem do cliente mesmo assim
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
            
            # Retornar mensagem pedindo para usar os botões
            bot_text = "Por favor, utilize os botões abaixo para continuar. 😊"
            
            bot_message_id = str(uuid.uuid4())
            bot_message = {
                "message_id": bot_message_id,
                "session_id": request.session_id,
                "from_type": "bot",
                "text": bot_text,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "has_button": False
            }
            await db.vendas_messages.insert_one(bot_message)
            
            # Retornar botões atuais (buscar do config)
            if button_config_doc and "button_config" in button_config_doc:
                current_buttons = button_config_doc["button_config"].get("root_buttons", [])
            else:
                current_buttons = []
            
            return {
                "messages": [
                    {
                        "message_id": client_message_id,
                        "from_type": "client",
                        "text": request.text,
                        "timestamp": client_message["timestamp"],
                        "has_button": False
                    },
                    {
                        "message_id": bot_message_id,
                        "from_type": "bot",
                        "text": bot_text,
                        "timestamp": bot_message["timestamp"],
                        "has_button": False
                    }
                ],
                "bot_state": "active",
                "buttons": current_buttons
            }
        
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
        
        # Atualizar last_message_at da sessão
        await db.vendas_sessions.update_one(
            {"session_id": request.session_id},
            {"$set": {"last_message_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        messages_to_return = [{
            "message_id": client_message_id,
            "from_type": "client",
            "text": request.text,
            "timestamp": client_message["timestamp"],
            "has_button": False
        }]
        
        # 🆕 VERIFICAR SE IA ESTÁ PERMITIDA (modo "ia" ou "hybrid", NÃO "button")
        ia_permitida = (
            status in [2, 3] and 
            usa_ia and 
            session.get('ai_active', True)
        )
        
        # Obter resposta da IA HUMANIZADA REAL (APENAS se IA estiver permitida)
        if ia_permitida:
            logger.info(f"🚀 Usando IA HUMANIZADA - Modo: {status}")
            
            # Buscar instruções
            instructions = ""
            if agent_config and agent_config.get('instructions'):
                instructions = agent_config.get('instructions', '')
                logger.info(f"✅ Instruções carregadas: {len(instructions)} chars")
            else:
                logger.warning("⚠️ Nenhuma instrução configurada!")
                instructions = "Você é uma atendente amigável e prestativa."
            
            # Pegar API key personalizada (se configurada)
            custom_api_key = agent_config.get('api_key') if agent_config else None
            
            # Chamar IA humanizada
            bot_text = await humanized_vendas_ai.get_response(
                user_message=request.text,
                session_id=request.session_id,
                instructions=instructions,
                db=db,
                custom_api_key=custom_api_key  # 🔑 Chave personalizada
            )
            
            # Definir variáveis padrão para sistema simples
            human_requested = False
            
            # Se cliente pediu humano, desativar IA e redirecionar
            if human_requested:
                logger.info(f"🚨 REDIRECIONANDO PARA HUMANO: {request.session_id}")
                
                # 1. Desativar IA na sessão
                await db.vendas_sessions.update_one(
                    {"session_id": request.session_id},
                    {
                        "$set": {
                            "ai_active": False,
                            "redirected_to_human": True,
                            "redirected_at": datetime.now(timezone.utc).isoformat(),
                            "department_id": "suporte"  # Redirecionar para departamento Suporte
                        }
                    }
                )
                
                # 2. Criar ticket no sistema de atendimento (se necessário)
                # TODO: Integrar com sistema de tickets existente
                
                logger.info(f"✅ Sessão {request.session_id} redirecionada para Suporte")
        else:
            bot_text = "Obrigado pela mensagem! Um atendente irá responder em breve."
        
        # Criar mensagem de resposta do bot
        bot_message = {
            "from_type": "bot",
            "text": bot_text,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Atualizar sessão
        await db.vendas_sessions.update_one(
            {"session_id": request.session_id},
            {"$set": {"last_message_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Retornar mensagens
        messages_to_return = [
            {
                "from_type": "user",
                "text": request.text,
                "timestamp": client_message["timestamp"]
            },
            bot_message
        ]
        
        return VendasMessageResponse(messages=messages_to_return, bot_state="active")
        
        # Código removido - retorno antecipado implementado acima
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao processar mensagem de vendas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/button-click")
async def handle_button_click(
    request: dict,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    🆕 Processar clique em botão do sistema de botões interativos
    """
    try:
        session_id = request.get("session_id")
        button_id = request.get("button_id")
        
        if not session_id or not button_id:
            raise HTTPException(status_code=400, detail="session_id e button_id são obrigatórios")
        
        logger.info(f"🔘 Botão clicado: {button_id} na sessão: {session_id}")
        
        # Processar clique no botão
        buttons_service = ButtonsService(db)
        result = await buttons_service.handle_button_click(session_id, button_id)
        
        # Salvar mensagem do bot com resposta do botão (incluindo mídia)
        bot_message_id = str(uuid.uuid4())
        bot_message = {
            "message_id": bot_message_id,
            "session_id": session_id,
            "from_type": "bot",
            "text": result["response_text"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "has_button": False,
            "media_url": result.get("media_url"),
            "media_type": result.get("media_type")
        }
        await db.vendas_messages.insert_one(bot_message)
        
        # Preparar resposta
        response = {
            "message": {
                "message_id": bot_message_id,
                "from_type": "bot",
                "text": result["response_text"],
                "timestamp": bot_message["timestamp"],
                "has_button": False,
                "media_url": result.get("media_url"),
                "media_type": result.get("media_type")
            },
            "has_sub_buttons": result["has_sub_buttons"],
            "buttons": [b.dict() for b in result["sub_buttons"]] if result["sub_buttons"] else []
        }
        
        logger.info(f"✅ Botão processado - Sub-botões: {result['has_sub_buttons']}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao processar clique em botão: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/button-action")
async def handle_button_action(
    request: dict,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Processar ação de botão (ex: gerar teste) - LEGADO
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
        
        # Obter WhatsApp da sessão
        whatsapp = session.get("whatsapp")
        
        if action == "GERAR_TESTE":
            # Verificar se já gerou teste para este WhatsApp
            existing_test = await db.vendas_sessions.find_one({
                "whatsapp": whatsapp,
                "test_generated": True
            })
            
            if existing_test:
                logger.info(f"⚠️ Cliente {whatsapp} já possui um teste ativo")
                
                # Mensagem informando que já possui teste
                bot_message_id = str(uuid.uuid4())
                bot_message = {
                    "message_id": bot_message_id,
                    "session_id": session_id,
                    "from_type": "bot",
                    "text": (
                        "⚠️ **Você já possui um teste ativo!**\n\n"
                        f"👤 **Usuário:** {existing_test.get('iptv_user', 'N/A')}\n"
                        f"🔐 **Senha:** {existing_test.get('iptv_pass', 'N/A')}\n\n"
                        "📱 Entre em contato com nosso suporte se precisar de ajuda!"
                    ),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "has_button": False
                }
                
                await db.vendas_messages.insert_one(bot_message)
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "message": bot_message["text"],
                    "has_button": False
                }
            
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

@router.post("/request-test")
async def request_test(
    request: dict,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Cliente solicita teste - gera usuário/senha automaticamente
    """
    try:
        session_id = request.get("session_id")
        whatsapp = request.get("whatsapp")
        pin = request.get("pin")
        name = request.get("name")  # Pegar nome do cliente
        
        if not session_id or not whatsapp or not pin:
            raise HTTPException(status_code=400, detail="Dados incompletos")
        
        # Verificar se já gerou teste
        session = await db.vendas_sessions.find_one({"session_id": session_id})
        if session and session.get("test_generated"):
            return {
                "success": False,
                "message": "Você já gerou um teste! ⚠️"
            }
        
        # Buscar API de teste
        config = await db.vendas_simple_config.find_one({"is_active": True})
        api_teste_url = config.get("api_teste_url", "https://gesth.io/api/get-teste?hash=TG1OTW5QWHlaTW5Q") if config else "https://gesth.io/api/get-teste?hash=TG1OTW5QWHlaTW5Q"
        
        # Gerar teste via API
        result = await vendas_ai_service.generate_iptv_test(api_teste_url)
        
        if result["success"]:
            # Preparar dados de atualização
            update_data = {
                "whatsapp": whatsapp,
                "pin": pin,
                "contact_saved": True,
                "test_generated": True,
                "iptv_user": result.get("usuario"),
                "iptv_pass": result.get("senha"),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Adicionar nome se fornecido
            if name:
                update_data["client_name"] = name
            
            # Salvar tudo na sessão
            await db.vendas_sessions.update_one(
                {"session_id": session_id},
                {"$set": update_data}
            )
            
            logger.info(f"✅ Teste gerado para {name or 'cliente'} ({whatsapp}): {result.get('usuario')}")
            
            return {
                "success": True,
                "usuario": result.get("usuario"),
                "senha": result.get("senha"),
                "message": f"🎉 Teste criado com sucesso!\n\n📱 Usuário: {result.get('usuario')}\n🔐 Senha: {result.get('senha')}"
            }
        else:
            return {
                "success": False,
                "message": result.get("message", "Erro ao gerar teste")
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao solicitar teste: {e}")
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

@router.post("/migrate-session")
async def migrate_vendas_session(
    request: dict,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Migrar sessão do /vendas para o chat principal
    Salva dados do cliente para uso no suporte.help
    """
    try:
        vendas_session_id = request.get("vendas_session_id")
        whatsapp = request.get("whatsapp")
        pin = request.get("pin")
        credentials = request.get("credentials", {})
        
        if not vendas_session_id or not whatsapp or not pin:
            raise HTTPException(status_code=400, detail="Dados incompletos")
        
        # Buscar todas as mensagens da sessão de vendas
        messages = await db.vendas_messages.find(
            {"session_id": vendas_session_id}
        ).sort("timestamp", 1).to_list(length=None)
        
        # Criar ou buscar ticket no sistema principal
        existing_ticket = await db.tickets.find_one({
            "whatsapp": whatsapp,
            "status": {"$in": ["open", "ATENDENDO"]}
        })
        
        ticket_id = None
        if existing_ticket:
            ticket_id = existing_ticket["id"]
            logger.info(f"📋 Ticket existente encontrado: {ticket_id}")
        else:
            # Criar novo ticket
            ticket_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            new_ticket = {
                "id": ticket_id,
                "whatsapp": whatsapp,
                "status": "open",
                "agent_id": None,
                "department": None,
                "ticket_origin": "vendas",
                "vendas_session_id": vendas_session_id,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat()
            }
            await db.tickets.insert_one(new_ticket)
            logger.info(f"✅ Novo ticket criado: {ticket_id}")
        
        # Copiar TODAS as mensagens do /vendas para o ticket principal
        messages_copied = 0
        for msg in messages:
            # Converter mensagem de vendas para formato do chat principal
            main_chat_message = {
                "id": str(uuid.uuid4()),
                "ticket_id": ticket_id,
                "text": msg.get("text", ""),
                "from_type": msg.get("from_type", "client"),  # client ou bot
                "timestamp": msg.get("timestamp"),
                "media_url": msg.get("media_url"),
                "media_type": msg.get("media_type"),
                "buttons": msg.get("buttons", []),
                "metadata": {
                    "from_vendas": True,
                    "vendas_session_id": vendas_session_id,
                    "original_message_id": msg.get("id")
                }
            }
            
            # Inserir na collection de mensagens principais
            await db.messages.insert_one(main_chat_message)
            messages_copied += 1
        
        logger.info(f"📨 {messages_copied} mensagens copiadas de /vendas para ticket {ticket_id}")
        
        # Criar registro de migração
        migration_data = {
            "vendas_session_id": vendas_session_id,
            "ticket_id": ticket_id,
            "whatsapp": whatsapp,
            "pin": pin,
            "iptv_user": credentials.get("usuario"),
            "iptv_pass": credentials.get("senha"),
            "migrated_at": datetime.now(timezone.utc).isoformat(),
            "message_count": len(messages),
            "messages_copied": messages_copied,
            "status": "migrated"
        }
        
        # Salvar na collection de migrações
        await db.vendas_migrations.insert_one(migration_data)
        
        # Atualizar sessão original
        await db.vendas_sessions.update_one(
            {"session_id": vendas_session_id},
            {
                "$set": {
                    "migrated": True,
                    "migrated_to_ticket_id": ticket_id,
                    "migrated_at": datetime.now(timezone.utc).isoformat(),
                    "migrated_to": "main_chat"
                }
            }
        )
        
        # Atualizar pinned_user e pinned_pass do usuário
        if credentials.get("usuario") and credentials.get("senha"):
            await db.users.update_one(
                {"whatsapp": whatsapp},
                {
                    "$set": {
                        "pinned_user": credentials.get("usuario"),
                        "pinned_pass": credentials.get("senha")
                    }
                },
                upsert=False
            )
            logger.info(f"✅ Credenciais IPTV salvas para {whatsapp}")
        
        logger.info(f"✅ Sessão {vendas_session_id} migrada para ticket {ticket_id}")
        
        return {
            "success": True,
            "message": "Sessão migrada com sucesso",
            "ticket_id": ticket_id,
            "migrated_messages": messages_copied
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao migrar sessão: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/assume-ai-session")
async def assume_ai_session(
    request: dict,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Atendente assume conversa da IA
    - Cria/atualiza ticket
    - Desativa IA
    - Migra mensagens de vendas para ticket principal
    - Abre conversa para o atendente
    """
    try:
        session_id = request.get("session_id")
        whatsapp = request.get("whatsapp")
        agent_id = request.get("agent_id")
        
        if not session_id or not agent_id:
            raise HTTPException(status_code=400, detail="Dados incompletos")
        
        # 1. Buscar sessão de vendas
        session = await db.vendas_sessions.find_one({"session_id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        
        # 2. Desativar IA
        await db.vendas_sessions.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "ai_active": False,
                    "agent_assumed": True,
                    "agent_id": agent_id,
                    "assumed_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        # 3. Buscar ou criar ticket
        existing_ticket = await db.tickets.find_one({
            "whatsapp": whatsapp,
            "status": {"$in": ["open", "ATENDENDO"]}
        })
        
        if existing_ticket:
            # Atualizar ticket existente
            ticket_id = existing_ticket["id"]
            await db.tickets.update_one(
                {"id": ticket_id},
                {
                    "$set": {
                        "status": "ATENDENDO",
                        "agent_id": agent_id,
                        "vendas_session_id": session_id,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            logger.info(f"✅ Ticket existente atualizado: {ticket_id}")
        else:
            # Criar novo ticket
            ticket_id = str(uuid.uuid4())
            new_ticket = {
                "id": ticket_id,
                "whatsapp": whatsapp,
                "status": "ATENDENDO",
                "agent_id": agent_id,
                "department": None,
                "ticket_origin": "ia",
                "vendas_session_id": session_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            await db.tickets.insert_one(new_ticket)
            logger.info(f"✅ Novo ticket criado: {ticket_id}")
        
        # 4. Copiar mensagens de vendas para ticket principal
        messages = await db.vendas_messages.find(
            {"session_id": session_id}
        ).sort("timestamp", 1).to_list(length=None)
        
        messages_copied = 0
        for msg in messages:
            # Verificar se mensagem já foi copiada
            existing_msg = await db.messages.find_one({
                "metadata.vendas_session_id": session_id,
                "metadata.original_message_id": msg.get("message_id")
            })
            
            if not existing_msg:
                main_chat_message = {
                    "id": str(uuid.uuid4()),
                    "ticket_id": ticket_id,
                    "text": msg.get("text", ""),
                    "from_type": msg.get("from_type", "client"),
                    "timestamp": msg.get("timestamp"),
                    "media_url": msg.get("media_url"),
                    "media_type": msg.get("media_type"),
                    "buttons": msg.get("buttons", []),
                    "metadata": {
                        "from_vendas": True,
                        "vendas_session_id": session_id,
                        "original_message_id": msg.get("message_id")
                    }
                }
                await db.messages.insert_one(main_chat_message)
                messages_copied += 1
        
        logger.info(f"📨 {messages_copied} mensagens copiadas para ticket {ticket_id}")
        
        return {
            "success": True,
            "ticket_id": ticket_id,
            "messages_copied": messages_copied,
            "message": "Conversa assumida com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao assumir sessão IA: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/button-reset")
async def reset_button_session(
    request: dict,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    🆕 Resetar sessão de botões para voltar ao menu principal
    """
    try:
        session_id = request.get("session_id")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id necessário")
        
        logger.info(f"🔄 Resetando sessão de botões: {session_id}")
        
        buttons_service = ButtonsService(db)
        await buttons_service.reset_session(session_id)
        
        # Buscar botões principais
        button_config = await buttons_service.get_config()
        
        return {
            "success": True,
            "message": "Sessão resetada para o menu principal",
            "buttons": [b.dict() for b in button_config.root_buttons]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao resetar sessão de botões: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reactivate-ai")
async def reactivate_ai_for_session(
    request: dict,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Reativar IA manualmente para uma sessão (botão do agente)
    """
    try:
        session_id = request.get("session_id")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id necessário")
        
        # Reativar IA
        await db.vendas_sessions.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "ai_active": True,
                    "ai_deactivated_until": None,
                    "ai_reactivated_manually": True,
                    "ai_reactivated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        logger.info(f"✅ IA reativada manualmente para sessão: {session_id}")
        
        return {
            "success": True,
            "message": "IA reativada com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao reativar IA: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai-sessions")
async def get_ai_sessions(
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Listar todas as sessões onde a IA está ativa (para aba roxa I.A)
    NÃO mostra sessões redirecionadas para SUPORTE
    """
    try:
        # Buscar todas as sessões ativas com IA (não redirecionadas)
        sessions = await db.vendas_sessions.find({
            "ai_active": True,
            "redirected_to_support": {"$ne": True},  # NÃO redirecionadas
            "status": {"$in": ["active", "waiting"]}
        }).sort("last_message_at", -1).to_list(length=100)
        
        # Buscar última mensagem de cada sessão
        sessions_with_info = []
        for session in sessions:
            last_msg = await db.vendas_messages.find_one(
                {"session_id": session["session_id"]},
                sort=[("timestamp", -1)]
            )
            
            sessions_with_info.append({
                "session_id": session["session_id"],
                "whatsapp": session.get("whatsapp", "Desconhecido"),
                "last_message": last_msg.get("text", "") if last_msg else "",
                "last_message_at": session.get("last_message_at"),
                "agent_name": session.get("ai_agent_name", "IA"),
                "created_at": session.get("created_at")
            })
        
        return {
            "success": True,
            "sessions": sessions_with_info,
            "total": len(sessions_with_info)
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar sessões IA: {e}")
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


# ==========================================
# ROTAS PARA PAINEL DO ATENDENTE
# ==========================================

@router.get("/ai-sessions")
async def list_ai_sessions(
    department_id: str = None,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Listar todas as sessões onde a IA está ativa
    Para mostrar na aba "I.A" do painel do atendente
    """
    try:
        query = {"ai_active": True}
        
        # Filtrar por departamento se especificado
        if department_id:
            query["department_id"] = department_id
        
        sessions = await db.vendas_sessions.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).to_list(length=None)
        
        # Para cada sessão, pegar última mensagem
        for session in sessions:
            last_message = await db.vendas_messages.find_one(
                {"session_id": session["session_id"]},
                {"_id": 0}
            ).sort("timestamp", -1)
            
            session["last_message"] = last_message if last_message else None
        
        logger.info(f"✅ {len(sessions)} sessões ativas com IA encontradas")
        
        return {"sessions": sessions, "total": len(sessions)}
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar sessões da IA: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agent-takeover/{session_id}")
async def agent_takeover_session(
    session_id: str,
    agent_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Atendente assume conversa que estava com IA
    """
    try:
        # Verificar se sessão existe
        session = await db.vendas_sessions.find_one({"session_id": session_id})
        
        if not session:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        
        # Desativar IA e atribuir ao atendente
        await db.vendas_sessions.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "ai_active": False,
                    "agent_id": agent_id,
                    "taken_over_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        # Salvar mensagem automática
        bot_message_id = str(uuid.uuid4())
        bot_message = {
            "message_id": bot_message_id,
            "session_id": session_id,
            "from_type": "system",
            "text": "Um atendente humano assumiu a conversa 👤",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "has_button": False
        }
        
        await db.vendas_messages.insert_one(bot_message)
        
        logger.info(f"✅ Atendente {agent_id} assumiu sessão: {session_id}")
        
        return {"success": True, "message": "Conversa assumida com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao assumir conversa: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/media")
async def upload_vendas_media(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    media_type: str = Form(...),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Upload de mídia (foto, vídeo, áudio) no chat de vendas
    """
    try:
        logger.info(f"📤 Upload de mídia recebido: {media_type} para sessão {session_id}")
        
        # Validar sessão
        session = await db.vendas_sessions.find_one({"session_id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        
        # Ler arquivo
        file_content = await file.read()
        file_size = len(file_content)
        
        logger.info(f"📦 Arquivo: {file.filename} ({file_size} bytes)")
        
        # Salvar arquivo usando media_service
        from media_service import save_media_file
        
        media_url = await save_media_file(
            file_content=file_content,
            filename=file.filename,
            content_type=file.content_type
        )
        
        logger.info(f"✅ Mídia salva: {media_url}")
        
        # Criar mensagem do cliente com mídia
        user_message_id = str(uuid.uuid4())
        user_message = {
            "message_id": user_message_id,
            "session_id": session_id,
            "sender": "client",
            "content": f"[{media_type.upper()}]",
            "media_url": media_url,
            "media_type": media_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "read": False
        }
        
        await db.vendas_messages.insert_one(user_message)
        
        # Remover _id para retornar
        user_message.pop('_id', None)
        
        # Se IA estiver ativa, gerar resposta automática
        bot_message = None
        if session.get('ai_active', False):
            bot_response = "👍 Recebi sua mídia! Como posso ajudar?"
            
            bot_message_id = str(uuid.uuid4())
            bot_message = {
                "message_id": bot_message_id,
                "session_id": session_id,
                "sender": "bot",
                "content": bot_response,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "read": False
            }
            
            await db.vendas_messages.insert_one(bot_message)
            bot_message.pop('_id', None)
        
        # Retornar mensagens
        messages = [user_message]
        if bot_message:
            messages.append(bot_message)
        
        return {"success": True, "messages": messages}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao processar mídia: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao processar mídia: {str(e)}")

