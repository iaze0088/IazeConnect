"""
Fluxo "12" - Criação de Teste Grátis
Gerencia o processo completo de criação de teste com WhatsApp, senha, PWA e auto-login
"""
import httpx
import logging
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# API para gerar credenciais de teste
CREDENTIALS_API_URL = "https://gesth.io/api/get-teste?hash=TG1OTW5QWHlaTW5Q"

class Flow12Manager:
    """Gerencia o fluxo '12' de criação de teste grátis"""
    
    async def process_flow_12(self, session_id: str, user_message: str, db) -> dict:
        """
        Processa uma mensagem dentro do fluxo 12
        
        Returns:
            {
                "message": str,  # Mensagem para o cliente
                "has_button": bool,  # Se deve mostrar botão
                "button_text": str,  # Texto do botão
                "button_action": str,  # Ação do botão
                "flow_complete": bool,  # Se o fluxo terminou
                "redirect_data": dict  # Dados para redirecionamento (se aplicável)
            }
        """
        # Buscar sessão atual
        session = await db.vendas_sessions.find_one({"session_id": session_id})
        if not session:
            logger.error(f"❌ Sessão {session_id} não encontrada")
            return self._error_response()
        
        # Estado do fluxo (armazenado na sessão)
        flow_state = session.get("flow_12_state", "initial")
        flow_data = session.get("flow_12_data", {})
        
        logger.info(f"📍 Fluxo 12 - Estado atual: {flow_state} | Mensagem: {user_message}")
        
        # Máquina de estados do fluxo
        if flow_state == "initial":
            # Cliente acabou de digitar "12" ou clicou no botão
            return await self._state_ask_whatsapp(session_id, db)
        
        elif flow_state == "waiting_whatsapp":
            # Cliente informou o WhatsApp
            return await self._state_process_whatsapp(session_id, user_message, db)
        
        elif flow_state == "waiting_password":
            # Cliente informou a senha de 2 dígitos
            return await self._state_process_password(session_id, user_message, flow_data, db)
        
        elif flow_state == "generating_credentials":
            # Credenciais foram geradas, aguardando confirmação PWA
            return await self._state_show_pwa_and_credentials(session_id, flow_data, db)
        
        elif flow_state == "complete":
            # Fluxo completo, redirecionar para suporte.help
            return await self._state_redirect_to_support(session_id, flow_data, db)
        
        else:
            logger.error(f"❌ Estado desconhecido: {flow_state}")
            return self._error_response()
    
    async def _state_ask_whatsapp(self, session_id: str, db) -> dict:
        """Estado: Pedir WhatsApp ao cliente"""
        # Atualizar estado da sessão
        await db.vendas_sessions.update_one(
            {"session_id": session_id},
            {"$set": {
                "flow_12_state": "waiting_whatsapp",
                "flow_12_started_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {
            "message": "📱 Perfeito! Para criar seu teste grátis, preciso do seu número de WhatsApp.\n\nPor favor, digite seu WhatsApp com DDD (exemplo: 11999999999):",
            "has_button": False,
            "button_text": None,
            "button_action": None,
            "flow_complete": False,
            "redirect_data": None
        }
    
    async def _state_process_whatsapp(self, session_id: str, whatsapp: str, db) -> dict:
        """Estado: Processar WhatsApp informado"""
        # Validar WhatsApp (apenas números)
        whatsapp_clean = ''.join(filter(str.isdigit, whatsapp))
        
        if len(whatsapp_clean) < 10 or len(whatsapp_clean) > 11:
            return {
                "message": "❌ WhatsApp inválido! Por favor, digite um número válido com DDD (exemplo: 11999999999):",
                "has_button": False,
                "button_text": None,
                "button_action": None,
                "flow_complete": False,
                "redirect_data": None
            }
        
        # VERIFICAR SE JÁ EXISTE TESTE PARA ESTE WHATSAPP
        existing_test = await db.vendas_sessions.find_one({
            "whatsapp": whatsapp_clean,
            "flow_12_state": {"$in": ["generating_credentials", "complete"]},
            "flow_12_data.username": {"$exists": True}
        })
        
        if existing_test:
            # Já existe teste gerado para este WhatsApp
            test_data = existing_test.get("flow_12_data", {})
            created_at = existing_test.get("flow_12_started_at", "")
            
            # Verificar se foi há menos de 24 horas (opcional - pode remover se quiser bloquear para sempre)
            from datetime import datetime, timezone, timedelta
            if created_at:
                try:
                    test_date = datetime.fromisoformat(created_at)
                    hours_ago = (datetime.now(timezone.utc) - test_date).total_seconds() / 3600
                    
                    if hours_ago < 24:
                        # Menos de 24 horas - bloquear
                        message = f"""⚠️ **Teste já gerado para este WhatsApp!**

📱 WhatsApp: `{whatsapp_clean}`
👤 Usuário: `{test_data.get('username', 'N/A')}`
🔑 Senha: `{test_data.get('api_password', 'N/A')}`
🌐 URL: {test_data.get('url', 'N/A')}

⏰ Você já gerou um teste há **{int(hours_ago)} horas**.
🚫 **Só é permitido 1 teste a cada 24 horas.**

💬 Se precisar de ajuda, entre em contato com o suporte."""
                        
                        return {
                            "message": message,
                            "has_button": False,
                            "button_text": None,
                            "button_action": None,
                            "flow_complete": True,  # Encerrar fluxo
                            "redirect_data": None
                        }
                except:
                    pass  # Se erro ao parsear data, continuar normalmente
            
            # Se passou 24 horas ou não tem data, mostrar credenciais antigas mas permitir novo teste
            logger.info(f"⚠️ WhatsApp {whatsapp_clean} já tem teste, mas passou 24h - permitindo novo")
        
        # Salvar WhatsApp e avançar estado
        await db.vendas_sessions.update_one(
            {"session_id": session_id},
            {"$set": {
                "flow_12_state": "waiting_password",
                "flow_12_data.whatsapp": whatsapp_clean,
                "whatsapp": whatsapp_clean  # Salvar também no campo principal
            }}
        )
        
        return {
            "message": f"✅ WhatsApp confirmado: `{whatsapp_clean}`\n\n🔐 Agora, crie uma senha de 2 dígitos que você vai lembrar (exemplo: 12, 99, 00):",
            "has_button": False,
            "button_text": None,
            "button_action": None,
            "flow_complete": False,
            "redirect_data": None
        }
    
    async def _state_process_password(self, session_id: str, password: str, flow_data: dict, db) -> dict:
        """Estado: Processar senha de 2 dígitos"""
        # Validar senha (2 dígitos)
        password_clean = ''.join(filter(str.isdigit, password))
        
        if len(password_clean) != 2:
            return {
                "message": "❌ Senha inválida! Por favor, digite uma senha de exatamente 2 dígitos (exemplo: 12):",
                "has_button": False,
                "button_text": None,
                "button_action": None,
                "flow_complete": False,
                "redirect_data": None
            }
        
        # Gerar credenciais via API
        logger.info(f"🔑 Gerando credenciais de teste para sessão {session_id}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(CREDENTIALS_API_URL)
                response.raise_for_status()
                credentials = response.json()
            
            if not credentials.get("result"):
                raise Exception("API retornou result=false")
            
            username = str(credentials.get("username", ""))
            api_password = str(credentials.get("password", ""))
            url = credentials.get("url", "")
            
            logger.info(f"✅ Credenciais geradas: user={username}, url={url}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar credenciais: {e}")
            return {
                "message": "❌ Erro ao gerar teste. Tente novamente em alguns instantes.",
                "has_button": False,
                "button_text": None,
                "button_action": None,
                "flow_complete": False,
                "redirect_data": None
            }
        
        # Salvar credenciais e senha do cliente
        await db.vendas_sessions.update_one(
            {"session_id": session_id},
            {"$set": {
                "flow_12_state": "generating_credentials",
                "flow_12_data.password": password_clean,
                "flow_12_data.username": username,
                "flow_12_data.api_password": api_password,
                "flow_12_data.url": url
            }}
        )
        
        # Retornar mensagem com botão para instalar PWA
        message = f"""🎉 Teste criado com sucesso!

📋 **Suas Credenciais:**
👤 Usuário: `{username}`
🔑 Senha: `{api_password}`
🌐 URL: {url}

📱 **Próximo passo:**
Clique no botão abaixo para instalar o aplicativo WA Suporte no seu celular. Com ele, você pode falar com nosso suporte sempre que precisar!"""
        
        return {
            "message": message,
            "has_button": True,
            "button_text": "📱 INSTALAR APP WA SUPORTE",
            "button_action": "INSTALL_PWA",
            "flow_complete": False,
            "redirect_data": None
        }
    
    async def _state_show_pwa_and_credentials(self, session_id: str, flow_data: dict, db) -> dict:
        """Estado: Mostrar PWA e preparar redirecionamento"""
        # Cliente clicou para instalar PWA
        # Atualizar estado para completo
        await db.vendas_sessions.update_one(
            {"session_id": session_id},
            {"$set": {
                "flow_12_state": "complete"
            }}
        )
        
        whatsapp = flow_data.get("whatsapp", "")
        password = flow_data.get("password", "")
        username = flow_data.get("username", "")
        api_password = flow_data.get("api_password", "")
        
        # Criar ticket de suporte com histórico
        redirect_data = await self._create_support_ticket(session_id, whatsapp, password, db)
        
        message = f"""✅ Aplicativo instalado com sucesso!

🎯 **Você será redirecionado automaticamente** para o chat de suporte com suas credenciais já configuradas.

📋 **Lembre-se:**
• WhatsApp: {whatsapp}
• Senha de acesso: {password}

Aguarde alguns segundos..."""
        
        return {
            "message": message,
            "has_button": False,
            "button_text": None,
            "button_action": None,
            "flow_complete": True,
            "redirect_data": redirect_data
        }
    
    async def _state_redirect_to_support(self, session_id: str, flow_data: dict, db) -> dict:
        """Estado: Redirecionar para suporte.help"""
        whatsapp = flow_data.get("whatsapp", "")
        password = flow_data.get("password", "")
        
        redirect_data = await self._create_support_ticket(session_id, whatsapp, password, db)
        
        return {
            "message": "Redirecionando...",
            "has_button": False,
            "button_text": None,
            "button_action": None,
            "flow_complete": True,
            "redirect_data": redirect_data
        }
    
    async def _create_support_ticket(self, session_id: str, whatsapp: str, password: str, db) -> dict:
        """Cria ticket de suporte com histórico de conversa do /vendas"""
        try:
            # Buscar histórico de mensagens do /vendas
            messages = await db.vendas_messages.find(
                {"session_id": session_id}
            ).sort("timestamp", 1).to_list(length=None)
            
            # Criar ou buscar usuário
            user = await db.users.find_one({"whatsapp": whatsapp})
            
            if not user:
                # Criar novo usuário
                user_id = str(uuid.uuid4())
                await db.users.insert_one({
                    "id": user_id,
                    "whatsapp": whatsapp,
                    "pin": password,
                    "display_name": f"Cliente {whatsapp}",
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
            else:
                user_id = user["id"]
                # Atualizar PIN
                await db.users.update_one(
                    {"id": user_id},
                    {"$set": {"pin": password}}
                )
            
            # Criar ticket de suporte
            ticket_id = str(uuid.uuid4())
            await db.tickets.insert_one({
                "id": ticket_id,
                "client_id": user_id,
                "status": "open",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source": "vendas_flow_12"
            })
            
            # Transferir mensagens do /vendas para o ticket de suporte
            for msg in messages:
                message_id = str(uuid.uuid4())
                await db.messages.insert_one({
                    "id": message_id,
                    "ticket_id": ticket_id,
                    "from_type": msg["from_type"],  # "client" ou "bot"
                    "sender_type": "client" if msg["from_type"] == "client" else "system",
                    "text": msg["text"],
                    "created_at": msg["timestamp"],
                    "kind": "text"
                })
            
            logger.info(f"✅ Ticket {ticket_id} criado com {len(messages)} mensagens transferidas")
            
            return {
                "user_id": user_id,
                "ticket_id": ticket_id,
                "whatsapp": whatsapp,
                "password": password,
                "message_count": len(messages)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar ticket de suporte: {e}")
            return {}
    
    def _error_response(self) -> dict:
        """Resposta padrão de erro"""
        return {
            "message": "❌ Ocorreu um erro. Por favor, tente novamente digitando '12'.",
            "has_button": False,
            "button_text": None,
            "button_action": None,
            "flow_complete": False,
            "redirect_data": None
        }
