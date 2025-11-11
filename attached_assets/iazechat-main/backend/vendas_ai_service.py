"""
Serviço de IA para Sistema de Vendas CyberTV
Bot inteligente que responde com IA e envia botões interativos
"""
import re
import httpx
import logging
import os
import uuid
from typing import Optional, Dict, Tuple, List
from datetime import datetime, timezone, timedelta
from emergentintegrations.llm.chat import LlmChat, UserMessage
from dotenv import load_dotenv
from vendas_flow_12 import Flow12Manager

load_dotenv()

logger = logging.getLogger(__name__)

class VendasAIService:
    """Bot inteligente com IA para vendas"""
    
    def __init__(self):
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not self.api_key:
            logger.error("❌ EMERGENT_LLM_KEY não encontrada!")
        
        # Inicializar gerenciador de fluxo 12
        self.flow_12_manager = Flow12Manager()
        
        # Palavras-chave para detectar pedido de humano
        self.human_keywords = [
            "humano", "atendente", "pessoa", "alguém", "real",
            "operador", "funcionário", "vendedor", "suporte",
            "falar com alguém", "falar com pessoa", "quero um humano",
            "me transfira", "transferir", "escalar"
        ]
        
        # Cache de instruções carregadas de URLs/arquivos
        self.instructions_cache = {}
    
    async def load_instructions_from_external(self, instructions_url: str = None, instructions_file: str = None) -> Optional[str]:
        """
        Carrega instruções de arquivo ou URL externa
        Prioridade: ARQUIVO > URL > None
        """
        try:
            # Tentar carregar de ARQUIVO primeiro (prioridade máxima)
            if instructions_file and instructions_file.strip():
                # Verificar cache
                cache_key = f"file_{instructions_file}"
                if cache_key in self.instructions_cache:
                    logger.info(f"📦 Usando instruções em cache de arquivo: {instructions_file}")
                    return self.instructions_cache[cache_key]
                
                logger.info(f"📄 Carregando instruções de arquivo: {instructions_file}")
                
                # Caminho do arquivo (assumindo que está em /app/instructions/)
                file_path = f"/app/instructions/{instructions_file}"
                
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if content and len(content.strip()) > 10:
                        # Salvar em cache
                        self.instructions_cache[cache_key] = content
                        logger.info(f"✅ Instruções carregadas de ARQUIVO ({len(content)} chars)")
                        return content
                    else:
                        logger.warning("⚠️ Arquivo vazio ou muito pequeno")
                else:
                    logger.error(f"❌ Arquivo não encontrado: {file_path}")
            
            # Se não conseguiu carregar de arquivo, tentar URL
            if instructions_url and instructions_url.strip():
                # Verificar cache
                cache_key = f"url_{instructions_url}"
                if cache_key in self.instructions_cache:
                    logger.info(f"📦 Usando instruções em cache de URL: {instructions_url[:50]}...")
                    return self.instructions_cache[cache_key]
                
                logger.info(f"🌐 Carregando instruções de URL: {instructions_url}")
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(instructions_url)
                    
                    if response.status_code == 200:
                        content = response.text
                        
                        # Validar se não está vazio
                        if content and len(content.strip()) > 10:
                            # Salvar em cache
                            self.instructions_cache[cache_key] = content
                            logger.info(f"✅ Instruções carregadas de URL ({len(content)} chars)")
                            return content
                        else:
                            logger.warning("⚠️ URL retornou conteúdo vazio ou muito pequeno")
                    else:
                        logger.error(f"❌ Erro ao carregar URL: Status {response.status_code}")
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar instruções externas: {e}")
            return None
    
    # Tools/Functions disponíveis para a IA
    @property
    def tools(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "buscar_credenciais",
                    "description": "Busca o usuário e senha do cliente no sistema. Use quando o cliente perguntar sobre suas credenciais, usuário, senha ou login.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "search_term": {
                                "type": "string",
                                "description": "Número de telefone do cliente ou usuário informado pelo cliente para buscar"
                            },
                            "search_type": {
                                "type": "string",
                                "enum": ["whatsapp", "usuario"],
                                "description": "Tipo de busca: 'whatsapp' se for número de telefone, 'usuario' se cliente informou o usuário"
                            }
                        },
                        "required": ["search_term", "search_type"]
                    }
                }
            }
        ]
    
    def detect_off_topic_response(self, response: str, agent_config: Optional[Dict]) -> bool:
        """
        Detectar se a resposta da IA fugiu do escopo configurado
        """
        if not agent_config:
            return False
        
        # Palavras-chave que indicam resposta fora do escopo
        off_topic_keywords = [
            # Tópicos gerais não relacionados
            "receita", "cozinha", "ingredientes",
            "política", "eleição", "governo",
            "religião", "igreja", "deus",
            "medicina", "doença", "sintomas", "remédio",
            "lei", "advogado", "processo",
            "programação", "código", "python", "javascript",
            "matemática", "equação", "cálculo",
            # Outros serviços não relacionados
            "netflix", "spotify", "amazon prime"  # apenas se não for o foco
        ]
        
        # Verificar palavras proibidas configuradas
        avoid_words = agent_config.get('avoid_words', '').lower()
        avoid_topics = agent_config.get('avoid_topics', '').lower()
        
        response_lower = response.lower()
        
        # Verificar se mencionou tópicos proibidos
        if avoid_topics:
            for topic in avoid_topics.split(','):
                topic = topic.strip()
                if topic and topic in response_lower:
                    logger.warning(f"⚠️ IA mencionou tópico proibido: {topic}")
                    return True
        
        # Verificar palavras proibidas
        if avoid_words:
            for word in avoid_words.split(','):
                word = word.strip()
                if word and word in response_lower:
                    logger.warning(f"⚠️ IA usou palavra proibida: {word}")
                    return True
        
        return False
    
    def detect_human_request(self, user_message: str) -> bool:
        """
        Detecta se cliente está pedindo para falar com humano
        """
        message_lower = user_message.lower()
        
        for keyword in self.human_keywords:
            if keyword in message_lower:
                logger.info(f"🚨 Pedido de humano detectado: '{keyword}' em '{user_message}'")
                return True
        
        return False
    
    def format_questions_with_line_breaks(self, text: str) -> str:
        """
        Adiciona quebra de linha dupla após cada pergunta (frase terminando com "?")
        para melhorar legibilidade da conversa.
        
        Exemplo:
        Input: "pra gerar um teste gratis, primeiro me informa qual aparelho deseja usar? se for smartv ou tv box me avisa."
        Output: "pra gerar um teste gratis, primeiro me informa qual aparelho deseja usar?\n\nse for smartv ou tv box me avisa."
        """
        # Regex para detectar "?" seguido de espaço e texto (não quebra de linha)
        # Adiciona \n\n após cada "?" que não tem \n logo após
        formatted = re.sub(
            r'\?(\s+)([^\n])',  # ? seguido de espaço(s) e caractere que não é \n
            r'?\n\n\2',  # Substitui por ? + dupla quebra + o caractere
            text
        )
        
        return formatted
    
    async def buscar_credenciais_completo(
        self, 
        whatsapp: str, 
        db = None
    ) -> Tuple[Optional[Dict], str]:
        """
        Busca credenciais com 3 etapas:
        1. Banco local (office_clients)
        2. Painel gestor.my (via office_service)
        3. Se não encontrar, retorna None
        
        Returns:
            (credenciais, fonte) onde fonte pode ser "banco_local", "gestor_my" ou None
        """
        
        # ETAPA 1: Buscar no banco local
        logger.info(f"🔍 ETAPA 1: Buscando credenciais no banco local para {whatsapp}")
        
        if db is not None:
            try:
                # Normalizar whatsapp
                whatsapp_clean = re.sub(r'\D', '', whatsapp)
                
                # Buscar no banco local
                client = await db.office_clients.find_one({
                    "$or": [
                        {"telefone": whatsapp_clean},
                        {"telefone": {"$regex": whatsapp_clean[-8:]}},  # últimos 8 dígitos
                        {"usuario": whatsapp_clean}
                    ]
                })
                
                if client:
                    logger.info("✅ ETAPA 1: Credenciais encontradas no banco local!")
                    return ({
                        "usuario": client.get("usuario", ""),
                        "senha": client.get("senha", ""),
                        "nome": client.get("nome", ""),
                        "vencimento": client.get("vencimento", ""),
                        "status": client.get("status", "")
                    }, "banco_local")
                else:
                    logger.info("⚠️ ETAPA 1: Não encontrado no banco local")
                    
            except Exception as e:
                logger.error(f"❌ Erro ao buscar no banco local: {e}")
        
        # ETAPA 2: Buscar no painel gestor.my
        logger.info("🔍 ETAPA 2: Buscando credenciais no painel gestor.my")
        
        try:
            from office_service import OfficeService
            office_service = OfficeService()
            
            # Buscar credenciais do Office no banco
            if db is not None:
                config = await db.config.find_one({})
                office_creds = config.get('office_credentials', []) if config else []
                
                # Tentar em cada conta do Office
                for cred in office_creds:
                    logger.info(f"🔑 Tentando conta Office: {cred.get('username')}")
                    
                    result = await office_service.search_client_credentials(
                        cred.get('username'),
                        cred.get('password'),
                        whatsapp
                    )
                    
                    if result and result.get('found'):
                        logger.info("✅ ETAPA 2: Credenciais encontradas no gestor.my!")
                        return (result.get('credentials'), "gestor_my")
                
                logger.info("⚠️ ETAPA 2: Não encontrado no gestor.my")
                
        except Exception as e:
            logger.error(f"❌ Erro ao buscar no gestor.my: {e}")
        
        # Não encontrado em nenhuma etapa
        logger.warning(f"❌ Credenciais NÃO encontradas para {whatsapp}")
        return (None, None)
    
    async def buscar_credenciais(
        self, 
        whatsapp: str, 
        db = None
    ) -> Tuple[Optional[Dict], str]:
        """
        Função de compatibilidade - chama buscar_credenciais_completo
        """
        return await self.buscar_credenciais_completo(whatsapp, db)
    
    async def buscar_credenciais_cliente(self, search_term: str, search_type: str = "whatsapp") -> Dict:
        """
        Busca credenciais do cliente no Office
        
        Args:
            search_term: Telefone ou usuário
            search_type: "whatsapp" ou "usuario"
            
        Returns:
            Dict com resultado da busca
        """
        try:
            logger.info(f"🔍 IA solicitou busca de credenciais: {search_term} (tipo: {search_type})")
            
            # Importar serviço aqui para evitar circular import
            from credential_auto_search import credential_auto_search
            from office_service_playwright import office_service_playwright
            from motor.motor_asyncio import AsyncIOMotorClient
            
            # Conectar ao MongoDB
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://mongodb:27017')
            db_name = os.environ.get('DB_NAME', 'support_chat')
            client = AsyncIOMotorClient(mongo_url)
            db = client[db_name]
            
            # Buscar credenciais do Office
            office_credentials = await db.office_credentials.find(
                {"active": True}
            ).to_list(length=None)
            
            if not office_credentials:
                return {
                    "success": False,
                    "message": "❌ Nenhum sistema configurado para busca. Entre em contato com o suporte."
                }
            
            # Se for WhatsApp, usar busca inteligente com múltiplos formatos
            if search_type == "whatsapp":
                result = await credential_auto_search.search_credentials_by_phone(
                    search_term,
                    office_credentials,
                    office_service_playwright
                )
            else:
                # Busca direta por usuário
                for cred in office_credentials:
                    result = await office_service_playwright.buscar_cliente(
                        {
                            "username": cred["username"],
                            "password": cred["password"]
                        },
                        search_term
                    )
                    
                    if result and result.get("success"):
                        break
            
            if result and result.get("success"):
                logger.info(f"✅ Credenciais encontradas pela IA para: {search_term}")
                return {
                    "success": True,
                    "usuario": result.get("usuario"),
                    "senha": result.get("senha"),
                    "vencimento": result.get("vencimento"),
                    "status": result.get("status")
                }
            else:
                logger.warning(f"❌ Credenciais não encontradas pela IA para: {search_term}")
                return {
                    "success": False,
                    "message": f"❌ Não encontrei cadastro com esse {search_type}: {search_term}"
                }
                
        except Exception as e:
            logger.error(f"❌ Erro ao buscar credenciais pela IA: {e}")
            return {
                "success": False,
                "message": "❌ Erro ao buscar credenciais. Tente novamente."
            }
    
    def detect_support_redirect(self, user_message: str) -> tuple[bool, str]:
        """
        Detecta se cliente precisa ser redirecionado para SUPORTE
        Returns: (should_redirect, reason)
        """
        message_lower = user_message.lower()
        
        # Palavras-chave de reembolso
        refund_keywords = [
            "reembolso", "devolver", "devolução", "cancelar", "cancela",
            "estorno", "quero meu dinheiro", "reembolsar"
        ]
        
        # Palavras-chave de atendimento humanizado
        human_support_keywords = [
            "atendente humanizado", "falar com atendente", "falar com humano",
            "quero falar com alguém", "atendimento humano", "pessoa real",
            "suporte humanizado"
        ]
        
        # Palavras de frustração/raiva
        frustration_keywords = [
            "não entendo", "não funciona", "péssimo", "horrível", "ridículo",
            "chato", "complicado", "difícil", "confuso", "não consigo",
            "irritado", "furioso", "bravo", "absurdo", "inútil"
        ]
        
        # Verificar reembolso
        for keyword in refund_keywords:
            if keyword in message_lower:
                logger.info(f"💰 Solicitação de reembolso detectada: '{keyword}'")
                return (True, "reembolso")
        
        # Verificar atendimento humanizado
        for keyword in human_support_keywords:
            if keyword in message_lower:
                logger.info(f"👤 Solicitação de atendente humanizado: '{keyword}'")
                return (True, "atendimento_humanizado")
        
        # Verificar frustração (contador - precisa 2+ palavras)
        frustration_count = sum(1 for keyword in frustration_keywords if keyword in message_lower)
        if frustration_count >= 2:
            logger.info(f"😤 Cliente frustrado detectado ({frustration_count} palavras)")
            return (True, "frustrado")
        
        return (False, "")
    
    async def redirect_to_support(
        self,
        session_id: str,
        whatsapp: str,
        reason: str,
        db
    ) -> dict:
        """
        Redireciona cliente para SUPORTE e desativa IA por 1 hora
        """
        try:
            logger.info(f"🔄 Redirecionando {whatsapp} para SUPORTE. Motivo: {reason}")
            
            # 1. Desativar IA por 1 hora
            now = datetime.now(timezone.utc)
            deactivate_until = now + timedelta(hours=1)
            
            await db.vendas_sessions.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "ai_active": False,
                        "ai_deactivated_until": deactivate_until.isoformat(),
                        "ai_deactivation_reason": reason,
                        "redirected_to_support": True,
                        "redirected_at": now.isoformat()
                    }
                }
            )
            
            # 2. Buscar reseller_id da sessão ou da config
            session = await db.vendas_sessions.find_one({"session_id": session_id})
            reseller_id = None
            
            if session and session.get("reseller_id"):
                reseller_id = session.get("reseller_id")
            else:
                # Buscar reseller_id da config ativa
                config = await db.vendas_simple_config.find_one({"is_active": True})
                if config and config.get("reseller_id"):
                    reseller_id = config.get("reseller_id")
                else:
                    # Fallback: buscar primeiro reseller do sistema
                    first_reseller = await db.resellers.find_one({})
                    if first_reseller:
                        reseller_id = first_reseller.get("id")
            
            logger.info(f"🔑 Reseller ID encontrado: {reseller_id}")
            
            # 3. Buscar department_id do departamento "SUPORTE" ou "WA Suporte"
            department_id = None
            department = await db.departments.find_one({
                "name": {"$in": ["SUPORTE", "WA Suporte", "Suporte", "suporte"]}
            })
            
            if department:
                department_id = department.get("id")
                logger.info(f"📁 Department ID encontrado: {department_id} ({department.get('name')})")
            else:
                logger.warning("⚠️ Nenhum departamento SUPORTE encontrado, ticket será criado sem department_id")
            
            # 4. Buscar se já existe usuário com este WhatsApp
            client_name = "Cliente"
            
            # Se WhatsApp vazio, usar identificador da sessão
            if not whatsapp or whatsapp == "":
                whatsapp = f"vendas_{session_id[:8]}"  # Usar primeiros 8 chars do session_id
                client_name = f"Cliente Vendas (Sessão {session_id[:8]})"
                logger.info(f"📝 WhatsApp não informado, usando identificador: {whatsapp}")
            else:
                user = await db.users.find_one({"whatsapp": whatsapp})
                if user:
                    client_name = user.get("name", "Cliente")
            
            # 5. Criar ticket no sistema de suporte (se não existir)
            # Buscar por whatsapp OU por vendas_session_id
            existing_ticket = await db.tickets.find_one({
                "$or": [
                    {"whatsapp": whatsapp},
                    {"vendas_session_id": session_id}
                ],
                "status": {"$in": ["open", "ATENDENDO"]}
            })
            
            if not existing_ticket:
                ticket_id = str(uuid.uuid4())
                
                # Gerar ticket_number
                ticket_count = await db.tickets.count_documents({}) + 1
                ticket_number = f"#{ticket_count:05d}"
                
                new_ticket = {
                    "id": ticket_id,
                    "ticket_number": ticket_number,
                    "whatsapp": whatsapp,
                    "client_name": client_name,
                    "status": "open",  # Status "open" para aparecer na fila ESPERA
                    "agent_id": None,
                    "department_id": department_id,  # ID do departamento
                    "reseller_id": reseller_id,  # ID do reseller (multi-tenant)
                    "ticket_origin": "vendas_ia",  # Origem: IA do /vendas
                    "ai_redirected": True,
                    "ai_redirect_reason": reason,
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                    "vendas_session_id": session_id  # Referência à sessão de vendas
                }
                await db.tickets.insert_one(new_ticket)
                logger.info(f"✅ Ticket criado: {ticket_id} ({ticket_number}) para {whatsapp} - Reseller: {reseller_id}")
            else:
                logger.info(f"ℹ️ Ticket já existe para {whatsapp}: {existing_ticket.get('id')}")
            
            # 6. Retornar mensagem de transferência
            reason_text = {
                "reembolso": "sua solicitação de reembolso",
                "atendimento_humanizado": "sua necessidade de atendimento personalizado",
                "frustrado": "melhor atendê-lo com um especialista"
            }.get(reason, "seu atendimento")
            
            message = f"Estou te transferindo para o departamento de SUPORTE Humanizado para tratar {reason_text}. Por favor aguarde que em breve eles te responderão! 🙋‍♂️"
            
            return {
                "success": True,
                "message": message,
                "deactivate_until": deactivate_until.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao redirecionar para suporte: {e}")
            return {
                "success": False,
                "message": "Desculpe, tive um problema. Por favor aguarde um momento.",
                "error": str(e)
            }
    
    async def get_conversation_history(self, session_id: str, db, max_messages: int = 200) -> List[Dict]:
        """
        Recuperar histórico de conversa (últimas N mensagens)
        Para manter contexto da IA
        """
        try:
            memory = await db.ai_conversation_memory.find_one({"session_id": session_id})
            
            if not memory or "messages" not in memory:
                logger.debug(f"📭 Nenhum histórico encontrado para: {session_id}")
                return []
            
            messages = memory.get("messages", [])
            
            # Pegar apenas as últimas N mensagens (padrão: 200)
            if len(messages) > max_messages:
                messages = messages[-max_messages:]
                logger.info(f"📚 Histórico limitado a {max_messages} mensagens para: {session_id}")
            
            logger.info(f"📚 Histórico recuperado: {len(messages)} mensagens para: {session_id}")
            return messages
            
        except Exception as e:
            logger.error(f"❌ Erro ao recuperar histórico: {e}")
            return []
    
    async def save_to_memory(self, session_id: str, role: str, content: str, db):
        """
        Salvar mensagem na memória de conversa
        """
        try:
            message_data = {
                "role": role,  # "user" ou "assistant"
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Usar a rota de API internamente
            from datetime import timedelta
            
            memory = await db.ai_conversation_memory.find_one({"session_id": session_id})
            
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(days=60)
            
            if memory:
                await db.ai_conversation_memory.update_one(
                    {"session_id": session_id},
                    {
                        "$push": {"messages": message_data},
                        "$set": {"expires_at": expires_at.isoformat()}
                    }
                )
            else:
                new_memory = {
                    "session_id": session_id,
                    "messages": [message_data],
                    "metadata": {},
                    "created_at": now.isoformat(),
                    "expires_at": expires_at.isoformat()
                }
                await db.ai_conversation_memory.insert_one(new_memory)
            
            logger.debug(f"💾 Mensagem salva na memória: {session_id}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar na memória: {e}")
    
    async def create_auto_feedback(self, session_id: str, tipo: str, contexto: dict, agent_id: str, db):
        """
        Criar feedback automático baseado no resultado da conversa
        """
        try:
            import uuid
            feedback_id = str(uuid.uuid4())
            
            feedback_data = {
                "id": feedback_id,
                "session_id": session_id,
                "tipo": tipo,  # "acerto" | "erro"
                "categoria": "auto_detectado",
                "contexto": contexto,
                "resultado": "Detectado automaticamente pelo sistema",
                "marcado_por": "sistema",
                "aprovado_admin": False,
                "agent_id": agent_id,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db.ai_learning_feedback.insert_one(feedback_data)
            
            logger.info(f"✅ Feedback automático criado: {tipo} - {session_id}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar feedback automático: {e}")
        
    async def get_ai_response(
        self, 
        user_message: str, 
        session_id: str,
        empresa_nome: str = "CyberTV",
        conversation_history: List[Dict] = None,
        agent_config: Optional[Dict] = None,
        db = None
    ) -> Tuple[str, bool, Optional[str], bool, Optional[Dict], Optional[str]]:
        """
        Obtém resposta da IA
        Returns: (bot_message, should_show_button, button_action, human_requested, redirect_data, button_text)
        """
        try:
            # 0. DETECTAR PALAVRAS-CHAVE PARA BUSCA AUTOMÁTICA DE CREDENCIAIS
            from keyword_credential_search import keyword_detector, format_credential_response
            
            if keyword_detector.detect(user_message):
                logger.info(f"🔑 Palavra-chave detectada! Buscando credenciais para sessão: {session_id}")
                
                try:
                    # Buscar sessão para pegar WhatsApp
                    session = await db.vendas_sessions.find_one({"session_id": session_id}) if db is not None else None
                    whatsapp = session.get("whatsapp", "") if session else ""
                    
                    if whatsapp and db is not None:
                        # Buscar credenciais automaticamente
                        from credential_auto_search import credential_auto_search
                        from office_service_playwright import office_service_playwright
                        
                        # Buscar credenciais do Office
                        office_credentials = await db.office_credentials.find(
                            {"active": True}
                        ).to_list(length=None)
                        
                        if office_credentials:
                            logger.info(f"🔍 Buscando credenciais no Office para: {whatsapp}")
                            
                            # Buscar credenciais
                            result = await credential_auto_search.search_credentials_by_phone(
                                whatsapp,
                                office_credentials,
                                office_service_playwright
                            )
                            
                            if result.get("success") and result.get("credential"):
                                # Extrair intenção (o que cliente quer saber)
                                intent = keyword_detector.extract_intent(user_message)
                                
                                # Formatar resposta
                                credential_msg = format_credential_response(result["credential"], intent)
                                
                                # Aplicar formatação de quebras de linha
                                credential_msg = self.format_questions_with_line_breaks(credential_msg)
                                
                                # Salvar na memória
                                await self.save_to_memory(session_id, "user", user_message, db)
                                await self.save_to_memory(session_id, "assistant", credential_msg, db)
                                
                                logger.info(f"✅ Credenciais encontradas e retornadas para: {whatsapp}")
                                
                                # Retornar credenciais diretamente
                                return (
                                    credential_msg,
                                    False,  # Sem botão
                                    None,
                                    False,  # Não é pedido de humano
                                    None,
                                    None
                                )
                            else:
                                # Não encontrou credenciais
                                error_msg = "❌ Não encontrei suas credenciais no sistema. Por favor, entre em contato com o suporte."
                                error_msg = self.format_questions_with_line_breaks(error_msg)
                                await self.save_to_memory(session_id, "user", user_message, db)
                                await self.save_to_memory(session_id, "assistant", error_msg, db)
                                
                                logger.warning(f"⚠️ Credenciais não encontradas para: {whatsapp}")
                                
                                return (error_msg, False, None, False, None, None)
                        else:
                            # Sem credenciais cadastradas
                            no_cred_msg = "❌ Sistema de credenciais não configurado. Entre em contato com o suporte."
                            no_cred_msg = self.format_questions_with_line_breaks(no_cred_msg)
                            await self.save_to_memory(session_id, "user", user_message, db)
                            await self.save_to_memory(session_id, "assistant", no_cred_msg, db)
                            
                            return (no_cred_msg, False, None, False, None, None)
                    else:
                        # Sem WhatsApp na sessão
                        no_phone_msg = "❌ Não consegui identificar seu WhatsApp. Por favor, inicie uma nova conversa."
                        no_phone_msg = self.format_questions_with_line_breaks(no_phone_msg)
                        await self.save_to_memory(session_id, "user", user_message, db)
                        await self.save_to_memory(session_id, "assistant", no_phone_msg, db)
                        
                        return (no_phone_msg, False, None, False, None, None)
                        
                except Exception as cred_error:
                    logger.error(f"❌ Erro ao buscar credenciais: {cred_error}")
                    error_msg = "❌ Ocorreu um erro ao buscar suas credenciais. Por favor, tente novamente."
                    error_msg = self.format_questions_with_line_breaks(error_msg)
                    
                    # Salvar na memória
                    if db is not None:
                        await self.save_to_memory(session_id, "user", user_message, db)
                        await self.save_to_memory(session_id, "assistant", error_msg, db)
                    
                    return (error_msg, False, None, False, None, None)
            
            # 1. VERIFICAR SE ESTÁ NO FLUXO 12 (criação de teste)
            session = await db.vendas_sessions.find_one({"session_id": session_id}) if db is not None else None
            flow_12_active = session and session.get("flow_12_state") not in [None, "initial", ""]
            
            # Se está no fluxo 12 OU cliente digitou "12", processar fluxo
            if flow_12_active or user_message.strip() == "12":
                logger.info(f"🎯 Processando fluxo 12 - Estado: {session.get('flow_12_state') if session else 'initial'}")
                flow_result = await self.flow_12_manager.process_flow_12(session_id, user_message, db)
                
                # Aplicar formatação de quebras de linha
                formatted_message = self.format_questions_with_line_breaks(flow_result["message"])
                
                return (
                    formatted_message,
                    flow_result["has_button"],
                    flow_result["button_action"],
                    False,
                    flow_result.get("redirect_data"),  # Dados de redirecionamento
                    flow_result.get("button_text")  # Texto do botão
                )
            
            # 1. DETECTAR SE CLIENTE DIGITOU "12" (SOLICITAR TESTE) - REMOVIDO, agora usa Flow12Manager
            # (código antigo removido)
            
            # 2. DETECTAR REDIRECIONAMENTO PARA SUPORTE (REEMBOLSO, ATENDENTE, FRUSTRAÇÃO)
            should_redirect, redirect_reason = self.detect_support_redirect(user_message)
            
            if should_redirect:
                logger.info(f"🔄 Redirecionando para SUPORTE. Motivo: {redirect_reason}")
                
                # Buscar whatsapp da sessão
                session = await db.vendas_sessions.find_one({"session_id": session_id}) if db is not None else None
                whatsapp = session.get("whatsapp", "") if session else ""
                
                # Redirecionar para suporte e desativar IA
                redirect_result = await self.redirect_to_support(
                    session_id,
                    whatsapp,
                    redirect_reason,
                    db
                ) if db is not None else {"message": "Erro ao redirecionar"}
                
                # Aplicar formatação de quebras de linha
                redirect_message = self.format_questions_with_line_breaks(redirect_result["message"])
                
                # Salvar na memória
                if db is not None:
                    await self.save_to_memory(session_id, "user", user_message, db)
                    await self.save_to_memory(session_id, "assistant", redirect_message, db)
                
                return (
                    redirect_message,
                    False,
                    None,
                    False,  # Não é pedido de humano tradicional, é redirecionamento
                    None,  # Sem redirect_data (já foi redirecionado)
                    None  # Sem button_text
                )
            
            # 3. DETECTAR PEDIDO DE HUMANO
            human_requested = self.detect_human_request(user_message)
            
            if human_requested:
                logger.info(f"🚨 Cliente pediu humano na sessão: {session_id}")
                
                human_msg = "Entendi! Já estou encaminhando você para um atendente humano. Aguarde que em breve alguém irá te responder 😊"
                human_msg = self.format_questions_with_line_breaks(human_msg)
                
                # Salvar na memória que cliente pediu humano
                if db is not None:
                    await self.save_to_memory(session_id, "user", user_message, db)
                    await self.save_to_memory(
                        session_id, 
                        "assistant", 
                        human_msg,
                        db
                    )
                    
                    # Criar feedback automático de erro (cliente pediu humano = não foi resolvido pela IA)
                    agent_id = agent_config.get('id') if agent_config else None
                    if agent_id:
                        await self.create_auto_feedback(
                            session_id,
                            "erro",
                            {
                                "motivo": "Cliente solicitou atendente humano",
                                "mensagem_cliente": user_message
                            },
                            agent_id,
                            db
                        )
                
                return (
                    human_msg,
                    False,
                    None,
                    True  # human_requested = True
                )
            
            # 2. SALVAR MENSAGEM DO USUÁRIO NA MEMÓRIA
            if db is not None:
                await self.save_to_memory(session_id, "user", user_message, db)
            
            # Usar API key do agente se disponível, senão usar do .env
            api_key_to_use = self.api_key
            if agent_config and agent_config.get('api_key'):
                api_key_to_use = agent_config['api_key']
                logger.info(f"🔑 Usando API key do agente: {api_key_to_use[:20]}...")
            else:
                logger.info(f"🔑 Usando API key do .env: {api_key_to_use[:20] if api_key_to_use else 'NENHUMA'}...")
            
            if not api_key_to_use:
                logger.error("❌ Nenhuma API key disponível!")
                return ("Erro: API key não configurada.", False, None, False, None, None)
            
            # Usar configuração do agente se disponível
            if agent_config:
                logger.info(f"🤖 Usando configuração do agente: {agent_config.get('name', 'Unknown')}")
                
                system_parts = []
                
                # 🎯 SYSTEM PROMPT PROFISSIONAL - Baseado em Best Practices 2025
                system_parts.append("""
Você é um assistente de IA especializado e focado.

🔴 REGRAS CRÍTICAS - NUNCA VIOLE:

1. Você DEVE seguir EXATAMENTE as instruções específicas fornecidas abaixo
2. As instruções abaixo definem QUEM você é, O QUE você faz, e COMO você responde
3. Você NÃO é uma IA genérica - você tem um propósito específico
4. Se uma pergunta não está relacionada ao seu propósito, educadamente redirecione

═══════════════════════════════════════════════════════
📋 SUAS INSTRUÇÕES ESPECÍFICAS (LEIA COM ATENÇÃO):
═══════════════════════════════════════════════════════
""")
                # Adicionar configurações específicas do agente
                if agent_config.get('who_is'):
                    system_parts.append(f"👤 QUEM VOCÊ É: {agent_config['who_is']}")
                else:
                    system_parts.append("👤 QUEM VOCÊ É: [NÃO CONFIGURADO - Use apenas instruções abaixo]")
                
                if agent_config.get('what_does'):
                    system_parts.append(f"📋 O QUE VOCÊ FAZ: {agent_config['what_does']}")
                else:
                    system_parts.append("📋 O QUE VOCÊ FAZ: [NÃO CONFIGURADO - Use apenas instruções abaixo]")
                
                if agent_config.get('objective'):
                    system_parts.append(f"🎯 SEU OBJETIVO: {agent_config['objective']}")
                else:
                    system_parts.append("🎯 SEU OBJETIVO: [NÃO CONFIGURADO - Use apenas instruções abaixo]")
                
                if agent_config.get('how_respond'):
                    system_parts.append(f"💬 COMO RESPONDER: {agent_config['how_respond']}")
                else:
                    system_parts.append("💬 COMO RESPONDER: [NÃO CONFIGURADO - Use apenas instruções abaixo]")
                
                # 🔥 CARREGAR INSTRUÇÕES DE URL OU ARQUIVO (PRIORIDADE MÁXIMA)
                instructions_from_external = None
                instructions_file = agent_config.get('instructions_file')
                instructions_url = agent_config.get('instructions_url')
                
                logger.info(f"🔍 Verificando fontes externas - File: {instructions_file}, URL: {instructions_url}")
                
                # 🚀 NOVO: Usar RAG se for arquivo (buscar apenas partes relevantes)
                # FORÇAR USO DO RAG - ignorar campo instructions se houver arquivo
                if instructions_file and instructions_file.strip():
                    from instructions_rag import instructions_rag
                    
                    filepath = f"/app/instructions/{instructions_file}"
                    logger.info(f"🤖 FORÇANDO RAG para arquivo: {instructions_file}")
                    
                    # Buscar apenas partes relevantes para esta mensagem
                    relevant_instructions = instructions_rag.get_relevant_instructions(filepath, user_message)
                    
                    if relevant_instructions:
                        # 🔥 LIMITAR TAMANHO (mesmo RAG pode retornar muito)
                        MAX_RAG_SIZE = 15000  # 15KB - suficiente para contexto relevante
                        if len(relevant_instructions) > MAX_RAG_SIZE:
                            logger.warning(f"⚠️ RAG retornou muito ({len(relevant_instructions)} chars), limitando a {MAX_RAG_SIZE}")
                            relevant_instructions = relevant_instructions[:MAX_RAG_SIZE]
                        
                        instructions_from_external = relevant_instructions
                        logger.info(f"✅ RAG retornou {len(relevant_instructions)} chars de instruções relevantes")
                        
                        # NÃO carregar de URL se arquivo funcionou
                        instructions_url = None
                    else:
                        logger.warning("⚠️ RAG não retornou instruções, tentando carregar arquivo completo")
                
                # Se RAG não funcionou, tentar URL ou carregar arquivo completo
                if not instructions_from_external and (instructions_url or instructions_file):
                    logger.info("🌐 Tentando carregar instruções de fonte externa (fallback)...")
                    instructions_from_external = await self.load_instructions_from_external(
                        instructions_url=instructions_url,
                        instructions_file=instructions_file if not instructions_from_external else None
                    )
                    
                    if instructions_from_external:
                        logger.info(f"✅ Instruções EXTERNAS carregadas: {len(instructions_from_external)} chars")
                    else:
                        logger.warning(f"⚠️ Não conseguiu carregar de fonte externa (File: {instructions_file}, URL: {instructions_url})")
                
                # Usar instruções externas se disponíveis, senão usar campo instructions
                final_instructions = instructions_from_external or agent_config.get('instructions', '')
                
                # 🔥 FALLBACK: Se não houver instruções, usar instruções padrão de IPTV
                if not final_instructions or len(final_instructions.strip()) < 50:
                    logger.warning("⚠️ NENHUMA INSTRUÇÃO CONFIGURADA! Usando instruções padrão de IPTV...")
                    final_instructions = """
Você é Juliana Silva, consultora de vendas da CyberTV IPTV.

O QUE VOCÊ OFERECE:
- Teste grátis de 3 horas para todos os dispositivos
- Suporte completo para instalação
- Planos de 1, 3, 6 e 12 meses
- Aplicativos: ASSIST PLUS, LAZER PLAY, HADES PLAY 2

DISPOSITIVOS SUPORTADOS:
- Smart TV (Samsung, LG, etc)
- TV Box (Xiaomi, Intelbras, etc)
- Fire Stick
- Celular (Android/iPhone)
- PC/Notebook

COMO ATENDER O CLIENTE (IMPORTANTE - LEIA COM ATENÇÃO):

1. 🚨 SEMPRE LEIA A MENSAGEM COMPLETA DO CLIENTE ANTES DE RESPONDER:
   - Se cliente disse "quero teste no meu tv box" → ele JÁ INFORMOU o aparelho (tv box)
   - Se cliente disse "quero fazer teste no firestick" → ele JÁ INFORMOU o aparelho (fire stick)
   - NÃO pergunte novamente o que o cliente já informou!

2. Fluxo para TESTE GRÁTIS:
   a) Se cliente JÁ disse o aparelho na mensagem:
      → Pule para próxima pergunta: "Qual aplicativo prefere? ASSIST PLUS, LAZER PLAY ou HADES PLAY 2?"
   
   b) Se cliente NÃO disse o aparelho:
      → Pergunte: "Em qual dispositivo você vai usar? Smart TV, TV Box, Fire Stick, Celular ou PC?"
   
   c) Depois de saber aparelho + app:
      → Pergunte: "Qual seu número de WhatsApp para eu enviar as credenciais?"

3. Seja inteligente e contextual:
   - ENTENDA o que o cliente está dizendo
   - NÃO seja repetitiva
   - Avance a conversa naturalmente

4. Seja simpática, use emojis moderadamente

PREÇOS DOS PLANOS:
- 1 mês - 2 telas: R$ 21,00
- 1 mês - 4 telas: R$ 28,00
- 3 meses - 2 telas: R$ 58,00
- 3 meses - 4 telas: R$ 78,00
- 6 meses - 2 telas: R$ 108,00
- 6 meses - 4 telas: R$ 148,00
- 12 meses - 2 telas: R$ 198,00
- 12 meses - 4 telas: R$ 278,00

LEMBRE-SE: Você é INTELIGENTE. Leia a mensagem COMPLETA antes de responder!
"""
                
                # 🔥 LIMITAR TAMANHO APENAS SE NECESSÁRIO
                if len(final_instructions) > 100000:
                    logger.warning(f"⚠️ Instruções muito grandes ({len(final_instructions)} chars). Truncando para 100000 chars")
                    final_instructions = final_instructions[:100000]
                    final_instructions += "\n\n[... restante omitido por tamanho ...]"
                
                system_parts.append(final_instructions)
                logger.info(f"✅ Instruções carregadas: {len(final_instructions)} chars")
                
                system_parts.append("""
═══════════════════════════════════════════════════════

🎯 COMPORTAMENTO OBRIGATÓRIO:

1. Você DEVE se comportar EXATAMENTE conforme descrito nas instruções acima
2. Se as instruções dizem que você é "Juliana Silva da CyberTV" - você É Juliana Silva
3. Se as instruções dizem que você oferece "teste grátis de 3 horas" - você oferece isso
4. Se as instruções especificam um fluxo de conversa - você SEGUE esse fluxo

🚫 O QUE NUNCA FAZER:

1. NUNCA diga "Sou uma IA" ou "Sou ChatGPT" - você tem a identidade definida nas instruções
2. NUNCA ofereça ajuda genérica - você tem um propósito específico
3. NUNCA ignore o contexto das instruções acima
4. NUNCA responda sobre tópicos não relacionados às suas instruções

✅ TESTE: Se o usuário pedir "teste grátis" e suas instruções mencionam isso, responda conforme suas instruções, NÃO de forma genérica!

═══════════════════════════════════════════════════════
""")
                
                
                system_message = "\n\n".join(system_parts)
                
                # 🔍 LOG COMPLETO DO SYSTEM MESSAGE PARA DEBUG
                logger.info(f"📝 System message construído ({len(system_message)} caracteres)")
                logger.info(f"🔍 PRIMEIROS 500 CHARS DO SYSTEM MESSAGE:\n{system_message[:500]}")
                logger.info(f"🔍 ÚLTIMOS 500 CHARS DO SYSTEM MESSAGE:\n{system_message[-500:]}")
            else:
                logger.warning("⚠️ NENHUMA CONFIGURAÇÃO - IA sem instruções específicas")
                # Deixar IA responder naturalmente sem instruções fixas
                system_message = f"Você é um assistente virtual da {empresa_nome}. Responda de forma educada e profissional."

            # 🔥 RECUPERAR HISTÓRICO DE CONVERSA (últimas 200 mensagens)
            history = await self.get_conversation_history(session_id, db, max_messages=200)
            
            # 🚫 INTERCEPTOR DESABILITADO - DEIXAR IA TRABALHAR NATURALMENTE
            # O interceptor estava causando mais problemas do que soluções:
            # - Ignorava quando usuário já dizia o dispositivo na mensagem
            # - Criava loops infinitos
            # - Impedia a IA de usar suas capacidades naturais
            # 
            # SOLUÇÃO: Confiar na IA com instruções bem escritas
            user_message_lower = user_message.lower()
            
            logger.info("🤖 Interceptor desabilitado - IA processará naturalmente com base nas instruções")
            
            # Converter histórico para formato do LlmChat
            initial_messages = []
            
            # 🔥 FORÇAR IDENTIDADE COM FEW-SHOT LEARNING
            # Adicionar exemplo de conversa que FORÇA a IA a seguir as instruções
            if agent_config:
                initial_messages.append({
                    "role": "user",
                    "content": "Quem é você?"
                })
                initial_messages.append({
                    "role": "assistant",
                    "content": f"Sou {agent_config.get('name', 'assistente virtual')} e trabalho seguindo minhas instruções específicas de atendimento."
                })
                logger.info(f"🎯 Few-shot learning adicionado para forçar identidade")
            
            # Carregar histórico existente
            if history:
                for msg in history:
                    initial_messages.append({
                        "role": msg.get("role"),  # "user" ou "assistant"
                        "content": msg.get("content", "")
                    })
                logger.info(f"📚 Contexto carregado: {len(history)} mensagens anteriores")
            
            logger.info(f"📚 Total de mensagens iniciais: {len(initial_messages)}")
            
            # Criar chat instance
            # 🔥 USAR GPT-4o-MINI para melhor aderência às instruções
            # Research 2025: gpt-4o-mini é mais obediente a system prompts específicos
            model_to_use = "gpt-4o-mini"
            
            logger.info("🎯 Usando GPT-4o-mini para máxima aderência às instruções específicas")
            
            # 🔥 NÃO PASSAR temperature no __init__ - emergentintegrations não suporta
            chat = LlmChat(
                api_key=api_key_to_use,
                session_id=session_id,
                system_message=system_message,
                initial_messages=initial_messages if initial_messages else None
            ).with_model("openai", model_to_use)
            
            # Aplicar temperatura APÓS criar o chat
            # chat.temperature = 0.1  # Comentado - biblioteca não suporta modificação
            
            logger.info(f"🤖 Usando modelo: {model_to_use} | System message: {len(system_message)} chars | Histórico: {len(initial_messages)} msgs")
            
            # 🔥 NORMALIZAR MENSAGEM DO USUÁRIO (facilitar compreensão da IA)
            # Detectar respostas curtas que são dispositivos e expandir
            normalized_message = user_message
            user_msg_lower = user_message.lower().replace(' ', '')
            
            device_mappings = {
                'smarttv': 'Smart TV',
                'smart-tv': 'Smart TV',
                'smart_tv': 'Smart TV',
                'tvbox': 'TV Box',
                'tv-box': 'TV Box',
                'tv_box': 'TV Box',
                'firestick': 'Fire Stick',
                'fire-stick': 'Fire Stick',
                'fire_stick': 'Fire Stick',
                'celular': 'Celular',
                'smartphone': 'Celular',
                'pc': 'PC',
                'computador': 'PC',
                'notebook': 'PC'
            }
            
            # Se mensagem curta (1-2 palavras) E corresponde a um dispositivo
            if len(user_message.split()) <= 2:
                for key, value in device_mappings.items():
                    if key in user_msg_lower:
                        normalized_message = f"Vou usar {value}"
                        logger.info(f"🔄 Mensagem normalizada: '{user_message}' → '{normalized_message}'")
                        break
            
            # 🔥 PREFIXAR MENSAGEM DO USUÁRIO COM CONTEXTO
            # Técnica avançada: adicionar contexto à mensagem do usuário
            contextual_user_message = f"""[CONTEXTO: Você é {agent_config.get('name', 'assistente')} e deve responder conforme suas instruções específicas]

Mensagem do cliente: {normalized_message}"""
            
            # Criar mensagem do usuário com contexto prefixado
            message = UserMessage(text=contextual_user_message)
            
            logger.info(f"📝 Mensagem contextualizada para forçar aderência às instruções")
            
            # 🔥 CHAMAR A IA - SEM PREFIXO NEGATIVO
            # Enviar e obter resposta
            response = await chat.send_message(message)
            
            # Extrair texto da resposta
            if hasattr(response, 'to_text'):
                response_text = response.to_text()
            elif hasattr(response, 'text'):
                response_text = response.text
            else:
                response_text = str(response)
            
            logger.info(f"✅ IA respondeu: {response_text[:200]}...")
            
            # Converter response para string se necessário
            if not isinstance(response_text, str):
                response = str(response_text)
            else:
                response = response_text
            
            # APLICAR APENAS FORMATAÇÃO BÁSICA: Quebra de linha após perguntas
            response = self.format_questions_with_line_breaks(response)
            logger.info(f"✅ Formatação básica aplicada")
            
            # 3. SALVAR RESPOSTA DA IA NA MEMÓRIA
            if db is not None:
                await self.save_to_memory(session_id, "assistant", response, db)
            
            # Detectar se deve mostrar botão
            should_show_button = False
            button_action = None
            clean_response = response
            
            if "[BUTTON:GERAR_TESTE]" in response:
                should_show_button = True
                button_action = "GERAR_TESTE"
                clean_response = response.replace("[BUTTON:GERAR_TESTE]", "").strip()
            
            logger.info(f"✅ IA respondeu: {clean_response[:100]}... | Botão: {should_show_button}")
            
            return (clean_response, should_show_button, button_action, False, None, None)
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Erro ao obter resposta da IA: {error_msg}")
            
            # Detectar erro de limite de tokens
            if "token" in error_msg.lower() or "limit" in error_msg.lower():
                logger.error("⚠️ ERRO: Prompt muito grande - limite de tokens excedido")
                token_error = "Desculpe, as instruções do agente estão muito grandes. Por favor, contate o administrador para otimizar a configuração."
                token_error = self.format_questions_with_line_breaks(token_error)
                return (
                    token_error,
                    False,
                    None,
                    False,
                    None,
                    None
                )
            
            # Fallback genérico
            generic_error = "Desculpe, houve um erro. Tente novamente."
            generic_error = self.format_questions_with_line_breaks(generic_error)
            return (
                generic_error,
                False,
                None,
                False,
                None,
                None
            )
    
    async def generate_iptv_test(self, api_url: str) -> Dict:
        """
        Gera teste IPTV via API
        Returns: {"success": bool, "usuario": str, "senha": str, "message": str}
        """
        try:
            logger.info(f"🔄 Chamando API de teste IPTV: {api_url}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(api_url)
                
                if response.status_code == 200:
                    try:
                        # Tentar parsear como JSON
                        data = response.json()
                        logger.info(f"✅ API Response JSON: {data}")
                        
                        # Extrair usuário e senha
                        usuario = data.get('username') or data.get('usuario')
                        senha = data.get('password') or data.get('senha')
                        
                        if usuario and senha:
                            usuario = str(usuario)
                            senha = str(senha)
                            
                            message = (
                                "🎉 **Teste gerado com sucesso!**\n\n"
                                "📺 **Dados de acesso ao IPTV:**\n"
                                f"👤 **Usuário:** {usuario}\n"
                                f"🔐 **Senha:** {senha}\n\n"
                                "⏰ **Validade:** 3 horas\n\n"
                                "Aproveite seu teste! 😊"
                            )
                            
                            return {
                                "success": True,
                                "usuario": usuario,
                                "senha": senha,
                                "message": message
                            }
                    except:
                        # Fallback para texto
                        response_text = response.text
                        logger.info(f"✅ API Response Text: {response_text}")
                        
                        usuario_match = re.search(r'(Usuário|username):\s*(\d+)', response_text, re.IGNORECASE)
                        senha_match = re.search(r'(Senha|password):\s*(\w+)', response_text, re.IGNORECASE)
                        
                        if usuario_match and senha_match:
                            usuario = usuario_match.group(2)
                            senha = senha_match.group(2)
                            
                            message = (
                                "🎉 **Teste gerado com sucesso!**\n\n"
                                "📺 **Dados de acesso ao IPTV:**\n"
                                f"👤 **Usuário:** {usuario}\n"
                                f"🔐 **Senha:** {senha}\n\n"
                                "⏰ **Validade:** 3 horas\n\n"
                                "Aproveite seu teste! 😊"
                            )
                            
                            return {
                                "success": True,
                                "usuario": usuario,
                                "senha": senha,
                                "message": message
                            }
                
                logger.error(f"❌ API retornou erro: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Erro ao gerar teste IPTV: {e}")
        
        return {
            "success": False,
            "message": "❌ Desculpe, houve um erro ao gerar seu teste. Por favor, tente novamente em alguns instantes."
        }
    
    async def process_media_message(
        self,
        media_data: bytes,
        media_type: str,  # 'audio', 'image', 'video'
        filename: str,
        session_id: str,
        agent_config: Optional[Dict] = None,
        db = None
    ) -> Tuple[str, str]:
        """
        Processa mídia enviada pelo cliente e retorna transcrição/análise + resposta da IA
        
        Returns: (media_text, ai_response)
        """
        try:
            from media_service import media_service
            
            media_text = ""
            
            # Processar dependendo do tipo
            if media_type == 'audio':
                logger.info(f"🎤 Processando áudio: {filename}")
                result = await media_service.transcribe_audio(
                    audio_data=media_data,
                    filename=filename,
                    language="pt"
                )
                media_text = f"[Áudio transcrito]: {result['text']}"
                
            elif media_type == 'image':
                logger.info(f"🖼️ Processando imagem: {filename}")
                result = await media_service.analyze_image(
                    image_data=media_data,
                    prompt="O cliente enviou esta imagem. Descreva o que você vê e extraia qualquer texto presente."
                )
                media_text = f"[Imagem analisada]: {result['text']}"
                
            elif media_type == 'video':
                logger.info(f"🎥 Processando vídeo: {filename}")
                result = await media_service.process_video(
                    video_data=media_data,
                    filename=filename,
                    extract_audio=True,
                    analyze_frames=True
                )
                media_text = f"[Vídeo processado]: {result.get('combined_summary', '')}"
            
            # Salvar na memória
            if db is not None:
                await self.save_to_memory(session_id, "user", media_text, db)
            
            # Obter resposta da IA com o conteúdo da mídia
            ai_response, _, _, _ = await self.get_ai_response(
                user_message=media_text,
                session_id=session_id,
                agent_config=agent_config,
                db=db
            )
            
            return media_text, ai_response
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar mídia: {e}")
            return "", "Desculpe, não consegui processar essa mídia. Pode tentar enviar novamente ou descrever o que precisa?"

# Instância global
vendas_ai_service = VendasAIService()
