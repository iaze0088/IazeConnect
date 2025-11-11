"""
Sistema de Auto-Resposta Inteligente - Baseado em Palavras-Chave
Detecta perguntas sobre usuário/senha e responde automaticamente
SEM precisar de IA!
"""
import re
from typing import Optional, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)

class AutoResponseService:
    """Serviço de resposta automática baseada em palavras-chave"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        
        # Palavras-chave que indicam pergunta sobre credenciais
        self.credential_keywords = [
            # Português
            r'\b(qual|quais|me\s+manda|envia|preciso)\s+(meu|minha|o|a)\s+(usuario|usuário|login|user|senha|pass|password|credenciais|dados|acesso)',
            r'\b(usuario|usuário|login|senha|pass|password)\s+(e|é|eh)\s+',
            r'\b(esqueci|perdi|nao\s+sei|não\s+sei|cadê|onde\s+esta|onde\s+está)\s+(meu|minha|o|a)?\s*(usuario|usuário|login|senha)',
            r'\b(como|qual)\s+(faz|faço|fazer)\s+login',
            r'\b(meu\s+login|minha\s+senha|minhas\s+credenciais)',
            r'\b(qual\s+meu\s+user|qual\s+minha\s+senha)',
        ]
        
        # Palavras-chave para informações sobre vencimento
        self.expiry_keywords = [
            r'\b(quando|qual)\s+(vence|expira|acaba)',
            r'\b(data|dia)\s+de\s+vencimento',
            r'\b(até\s+quando|validade)',
            r'\b(vai\s+expirar|está\s+vencido)',
        ]
    
    async def should_auto_respond(self, message: str, client_phone: str = None) -> Optional[Dict]:
        """
        Verificar se deve responder automaticamente
        
        Returns:
            Dict com tipo de resposta e dados OU None se não deve responder
        """
        message_lower = message.lower()
        
        # Verificar se é pergunta sobre credenciais
        for pattern in self.credential_keywords:
            if re.search(pattern, message_lower):
                logger.info(f"🤖 Detectada pergunta sobre credenciais: {message[:50]}")
                
                # Se tem telefone, buscar automaticamente
                if client_phone:
                    credentials = await self._get_credentials_by_phone(client_phone)
                    if credentials:
                        return {
                            "type": "credentials",
                            "data": credentials,
                            "auto_response": self._format_credentials_message(credentials)
                        }
                
                return {
                    "type": "credentials_prompt",
                    "message": "Para consultar seus dados, preciso do seu telefone. Você está ligando de qual número?"
                }
        
        # Verificar se é pergunta sobre vencimento
        for pattern in self.expiry_keywords:
            if re.search(pattern, message_lower):
                logger.info(f"🤖 Detectada pergunta sobre vencimento: {message[:50]}")
                
                if client_phone:
                    credentials = await self._get_credentials_by_phone(client_phone)
                    if credentials:
                        return {
                            "type": "expiry",
                            "data": credentials,
                            "auto_response": self._format_expiry_message(credentials)
                        }
        
        return None
    
    async def _get_credentials_by_phone(self, phone: str) -> Optional[Dict]:
        """Buscar credenciais pelo telefone"""
        try:
            # Normalizar telefone (remover caracteres especiais)
            phone_normalized = ''.join(filter(str.isdigit, phone))
            
            # Buscar no banco
            client = await self.db.office_clients.find_one({
                "telefone_normalized": phone_normalized
            })
            
            if client:
                logger.info(f"✅ Cliente encontrado: {client['usuario']}")
                return {
                    "usuario": client.get("usuario", "N/A"),
                    "senha": client.get("senha", "N/A"),
                    "telefone": client.get("telefone", "N/A"),
                    "vencimento": client.get("vencimento", "N/A"),
                    "status": client.get("status", "N/A"),
                    "conexoes": client.get("conexoes", "N/A"),
                    "office_account": client.get("office_account", "N/A")
                }
            else:
                logger.warning(f"⚠️ Cliente não encontrado: {phone_normalized}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao buscar credenciais: {e}")
            return None
    
    def _format_credentials_message(self, credentials: Dict) -> str:
        """Formatar mensagem com credenciais"""
        return f"""📺 *Seus Dados de Acesso*

👤 *Usuário:* {credentials['usuario']}
🔑 *Senha:* {credentials['senha']}
📱 *Telefone:* {credentials['telefone']}
📅 *Vencimento:* {credentials['vencimento']}
🟢 *Status:* {credentials['status']}
📡 *Conexões:* {credentials['conexoes']}

✅ _Dados enviados automaticamente!_"""
    
    def _format_expiry_message(self, credentials: Dict) -> str:
        """Formatar mensagem com vencimento"""
        return f"""📅 *Informações de Vencimento*

📺 *Usuário:* {credentials['usuario']}
📅 *Vencimento:* {credentials['vencimento']}
🟢 *Status:* {credentials['status']}

✅ _Informação enviada automaticamente!_"""
