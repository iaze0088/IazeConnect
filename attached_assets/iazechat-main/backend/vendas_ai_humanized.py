"""
IA HUMANIZADA - WA SITE
Usa GPT-4o-mini com técnica de prompt stuffing (instruções em CADA mensagem)
SUPORTA: emergentintegrations OU OpenAI nativa (cada revenda pode ter sua chave)
"""
import logging
import os
from datetime import datetime, timezone
from typing import Tuple, List, Dict

logger = logging.getLogger(__name__)

class HumanizedVendasAI:
    """IA Humanizada que REALMENTE segue instruções"""
    
    def __init__(self):
        logger.info("✅ IA Humanizada inicializada (multi-key support)")
    
    async def get_response(
        self,
        user_message: str,
        session_id: str,
        instructions: str,
        db,
        custom_api_key: str = None  # 🆕 Chave personalizada por revenda
    ) -> str:
        """
        Obtém resposta da IA REAL seguindo instruções
        Suporta emergentintegrations OU OpenAI nativa
        🚀 OTIMIZADO: Limita tamanho de instruções para melhor performance
        🎯 NOVO: Verifica Base de Conhecimento CERTO|ERRADO primeiro
        """
        try:
            # 🎯 PASSO 1: Verificar Base de Conhecimento CERTO|ERRADO
            from correct_wrong_knowledge import correct_wrong_service
            
            knowledge_match = await correct_wrong_service.search_knowledge(user_message, db)
            
            if knowledge_match:
                logger.info(f"🎯 Match na Base CERTO|ERRADO: {knowledge_match.get('question')}")
                
                # Formatar resposta usando apenas opções CERTAS
                response_text = correct_wrong_service.format_response(knowledge_match, include_wrong=False)
                
                if response_text:
                    # Salvar no histórico
                    await self.save_message(session_id, "user", user_message, db)
                    await self.save_message(session_id, "assistant", response_text, db)
                    
                    logger.info(f"✅ Resposta CERTA enviada (Base de Conhecimento)")
                    return response_text
            
            # Se não achou na base CERTO|ERRADO, continuar com IA normal
            
            # Buscar histórico
            history = await self.get_history(session_id, db, limit=10)
            
            # Construir contexto do histórico
            history_text = ""
            if history:
                history_text = "\n\n[HISTÓRICO DA CONVERSA]:\n"
                for msg in history[-6:]:  # Últimas 6 mensagens
                    role = "Cliente" if msg.get('role') == 'user' else "Você (Juliana)"
                    history_text += f"{role}: {msg.get('content', '')}\n"
            
            # 🚀 OTIMIZAÇÃO CRÍTICA: Se instruções são muito grandes (>30k chars), limitar
            optimized_instructions = instructions
            
            if len(instructions) > 30000:
                logger.warning(f"⚠️ Instruções muito grandes ({len(instructions)} chars) - Limitando a 25k para melhor performance")
                
                # Limitar a 25k chars (melhor performance mantendo qualidade)
                optimized_instructions = instructions[:25000]
                optimized_instructions += "\n\n[... restante das instruções omitido para otimização de performance ...]"
                
                logger.info(f"✅ Instruções otimizadas: {len(instructions)} → {len(optimized_instructions)} chars")
            
            # 🔥 TÉCNICA: Colocar instruções DENTRO da mensagem do usuário
            stuffed_message = f"""[INSTRUÇÕES QUE VOCÊ DEVE SEGUIR]:
{optimized_instructions}

{history_text}

[NOVA MENSAGEM DO CLIENTE]:
{user_message}

[IMPORTANTE]: 
- Você É Juliana (não diga que é uma IA)
- Responda de forma NATURAL e HUMANIZADA
- Siga EXATAMENTE as regras das suas instruções
- Seja DIRETA, não genérica
- Uma pergunta por vez"""
            
            system_prompt = "Você é Juliana. Siga as instruções fornecidas. Seja natural e humana."
            
            logger.info(f"🤖 Enviando para GPT-4o-mini | Session: {session_id} | Prompt size: {len(stuffed_message)} chars")
            
            # 🔑 DECIDIR QUAL BIBLIOTECA USAR
            api_key = custom_api_key or os.environ.get('OPENAI_API_KEY') or os.environ.get('EMERGENT_LLM_KEY')
            
            if not api_key:
                logger.error("❌ Nenhuma API key configurada!")
                return "Erro: API key não configurada. Entre em contato com o suporte."
            
            # Detectar tipo de chave
            use_emergent = api_key.startswith('sk-emergent-')
            
            if use_emergent:
                # Usar emergentintegrations
                logger.info("🔧 Usando emergentintegrations")
                response_text = await self._call_emergent(api_key, system_prompt, stuffed_message, session_id)
            else:
                # Usar OpenAI nativa
                logger.info("🔧 Usando OpenAI SDK nativa")
                response_text = await self._call_openai(api_key, system_prompt, stuffed_message)
            
            logger.info(f"✅ GPT respondeu ({len(response_text)} chars): {response_text[:100]}...")
            
            # Salvar no histórico
            await self.save_message(session_id, "user", user_message, db)
            await self.save_message(session_id, "assistant", response_text, db)
            
            return response_text
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter resposta da IA: {e}")
            import traceback
            logger.error(f"❌ Traceback completo: {traceback.format_exc()}")
            return "Desculpe, tive um problema técnico. Pode repetir?"
    
    async def _call_emergent(self, api_key: str, system_prompt: str, user_message: str, session_id: str) -> str:
        """Chamar usando emergentintegrations com timeout"""
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            import asyncio
            
            chat = LlmChat(
                api_key=api_key,
                session_id=session_id,
                system_message=system_prompt,
                initial_messages=None
            ).with_model("openai", "gpt-4o-mini")
            
            message = UserMessage(text=user_message)
            
            # 🚀 OTIMIZAÇÃO: Adicionar timeout de 15 segundos
            try:
                response = await asyncio.wait_for(
                    chat.send_message(message),
                    timeout=15.0
                )
            except asyncio.TimeoutError:
                logger.error("⏱️ Timeout ao chamar IA (15s)")
                return "Desculpe, estou demorando muito para responder. Pode tentar novamente?"
            
            if hasattr(response, 'to_text'):
                return response.to_text()
            elif hasattr(response, 'text'):
                return response.text
            else:
                return str(response)
        except Exception as e:
            logger.error(f"❌ Erro emergent: {e}")
            raise
    
    async def _call_openai(self, api_key: str, system_prompt: str, user_message: str) -> str:
        """Chamar usando OpenAI SDK nativa"""
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=api_key)
            
            # 🚀 OTIMIZAÇÃO: Reduzir max_tokens para respostas mais rápidas
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.9,
                max_tokens=300,  # 🚀 Reduzido de 500 para 300 (respostas mais rápidas)
                timeout=15.0  # 🚀 Timeout de 15 segundos
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"❌ Erro OpenAI: {e}")
            raise
    
    async def save_message(self, session_id: str, role: str, content: str, db):
        """Salva mensagem no histórico"""
        try:
            doc = {
                "session_id": session_id,
                "role": role,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await db.ai_conversation_memory.insert_one(doc)
            logger.info(f"💾 Salvo: {role}")
        except Exception as e:
            logger.error(f"❌ Erro ao salvar: {e}")
    
    async def get_history(self, session_id: str, db, limit: int = 20) -> List[Dict]:
        """Recupera histórico"""
        try:
            msgs = await db.ai_conversation_memory.find(
                {"session_id": session_id}
            ).sort("timestamp", -1).limit(limit).to_list(length=None)
            
            msgs.reverse()
            return msgs
        except Exception as e:
            logger.error(f"❌ Erro ao buscar histórico: {e}")
            return []


# Instância global
humanized_vendas_ai = HumanizedVendasAI()
