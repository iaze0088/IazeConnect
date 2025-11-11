"""
Serviço de IA para Sistema de Vendas CyberTV
Bot inteligente que responde com IA e envia botões interativos
"""
import re
import httpx
import logging
import os
from typing import Optional, Dict, Tuple, List
from datetime import datetime, timezone
from emergentintegrations.llm.chat import LlmChat, UserMessage
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class VendasAIService:
    """Bot inteligente com IA para vendas"""
    
    def __init__(self):
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not self.api_key:
            logger.error("❌ EMERGENT_LLM_KEY não encontrada!")
        
    async def get_ai_response(
        self, 
        user_message: str, 
        session_id: str,
        empresa_nome: str = "CyberTV",
        conversation_history: List[Dict] = None,
        agent_config: Optional[Dict] = None
    ) -> Tuple[str, bool, Optional[str]]:
        """
        Obtém resposta da IA
        Returns: (bot_message, should_show_button, button_action)
        """
        try:
            # Usar API key do agente se disponível, senão usar do .env
            api_key_to_use = self.api_key
            if agent_config and agent_config.get('api_key'):
                api_key_to_use = agent_config['api_key']
                logger.info(f"🔑 Usando API key do agente: {api_key_to_use[:20]}...")
            else:
                logger.info(f"🔑 Usando API key do .env: {api_key_to_use[:20] if api_key_to_use else 'NENHUMA'}...")
            
            if not api_key_to_use:
                logger.error("❌ Nenhuma API key disponível!")
                return ("Erro: API key não configurada.", False, None)
            
            # Usar configuração do agente se disponível
            if agent_config:
                logger.info(f"🤖 Usando configuração do agente: {agent_config.get('name', 'Unknown')}")
                system_parts = []
                
                if agent_config.get('who_is'):
                    system_parts.append(f"QUEM VOCÊ É: {agent_config['who_is']}")
                if agent_config.get('what_does'):
                    system_parts.append(f"O QUE VOCÊ FAZ: {agent_config['what_does']}")
                if agent_config.get('objective'):
                    system_parts.append(f"SEU OBJETIVO: {agent_config['objective']}")
                if agent_config.get('how_respond'):
                    system_parts.append(f"COMO RESPONDER: {agent_config['how_respond']}")
                if agent_config.get('instructions'):
                    system_parts.append(f"INSTRUÇÕES:\n{agent_config['instructions']}")
                if agent_config.get('avoid_topics'):
                    system_parts.append(f"EVITE FALAR SOBRE: {agent_config['avoid_topics']}")
                if agent_config.get('avoid_words'):
                    system_parts.append(f"PALAVRAS PROIBIDAS: {agent_config['avoid_words']}")
                
                system_message = "\n\n".join(system_parts)
                
                logger.info(f"📝 System message construído ({len(system_message)} caracteres)")
            else:
                logger.warning("⚠️ NENHUMA CONFIGURAÇÃO - IA sem instruções específicas")
                # Deixar IA responder naturalmente sem instruções fixas
                system_message = f"Você é um assistente virtual da {empresa_nome}. Responda de forma educada e profissional."

            # Criar chat instance
            chat = LlmChat(
                api_key=api_key_to_use,
                session_id=session_id,
                system_message=system_message
            ).with_model("openai", "gpt-4o-mini")
            
            # Criar mensagem do usuário
            message = UserMessage(text=user_message)
            
            # Enviar e obter resposta
            response = await chat.send_message(message)
            
            # Detectar se deve mostrar botão
            should_show_button = False
            button_action = None
            clean_response = response
            
            if "[BUTTON:GERAR_TESTE]" in response:
                should_show_button = True
                button_action = "GERAR_TESTE"
                clean_response = response.replace("[BUTTON:GERAR_TESTE]", "").strip()
            
            logger.info(f"✅ IA respondeu: {clean_response[:100]}... | Botão: {should_show_button}")
            
            return (clean_response, should_show_button, button_action)
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter resposta da IA: {e}")
            # Fallback básico
            return (
                "Desculpe, houve um erro. Tente novamente.",
                False,
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

# Instância global
vendas_ai_service = VendasAIService()
