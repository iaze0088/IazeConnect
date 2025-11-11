"""
Sistema de Busca Automática de Credenciais por Palavras-Chave
Detecta quando cliente pergunta sobre login/senha e busca automaticamente
"""

import re
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

class KeywordCredentialDetector:
    """
    Detecta palavras-chave relacionadas a login/senha/vencimento
    """
    
    # Palavras-chave que acionam busca automática
    KEYWORDS = [
        # Login/Usuário
        r"qual\s+(?:é|eh|e)\s+meu\s+usuario",
        r"qual\s+meu\s+usuario",
        r"esqueci\s+meu\s+usuario",
        r"qual\s+meu\s+login",
        r"esqueci\s+meu\s+login",
        r"qual\s+(?:é|eh|e)\s+meu\s+login",
        
        # Senha
        r"qual\s+minha\s+senha",
        r"esqueci\s+minha\s+senha",
        r"qual\s+(?:é|eh|e)\s+minha\s+senha",
        r"qual\s+a\s+senha",
        
        # Usuário e Senha juntos
        r"qual\s+meu\s+usuario\s+e\s+senha",
        r"usuario\s+e\s+senha",
        r"login\s+e\s+senha",
        
        # Vencimento
        r"quando\s+vence\s+meu\s+usuario",
        r"quando\s+vence\s+meu\s+login",
        r"quando\s+vence\s+meu\s+acesso",
        r"qual\s+a\s+data\s+de\s+vencimento",
        r"data\s+de\s+vencimento",
        r"validade\s+do\s+acesso",
        
        # Variações
        r"preciso\s+do\s+meu\s+login",
        r"preciso\s+da\s+minha\s+senha",
        r"me\s+passa\s+o\s+usuario",
        r"me\s+passa\s+a\s+senha",
        r"meu\s+acesso",
        r"minhas\s+credenciais"
    ]
    
    def __init__(self):
        self.patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.KEYWORDS]
    
    def detect(self, message: str) -> bool:
        """
        Detecta se mensagem contém palavra-chave
        
        Args:
            message: Texto da mensagem
            
        Returns:
            True se detectou palavra-chave, False caso contrário
        """
        if not message or not isinstance(message, str):
            return False
        
        # Normalizar mensagem (remover acentos, converter minúsculas)
        normalized = self._normalize(message)
        
        # Verificar cada pattern
        for pattern in self.patterns:
            if pattern.search(normalized):
                logger.info(f"🔑 Palavra-chave detectada: {pattern.pattern}")
                return True
        
        return False
    
    def _normalize(self, text: str) -> str:
        """Normaliza texto para comparação"""
        # Remover acentos
        replacements = {
            'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a',
            'é': 'e', 'ê': 'e',
            'í': 'i',
            'ó': 'o', 'ô': 'o', 'õ': 'o',
            'ú': 'u', 'ü': 'u',
            'ç': 'c'
        }
        
        text = text.lower()
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def extract_intent(self, message: str) -> Dict[str, bool]:
        """
        Extrai intenção da mensagem
        
        Returns:
            {
                "wants_username": bool,
                "wants_password": bool,
                "wants_expiry": bool
            }
        """
        normalized = self._normalize(message)
        
        return {
            "wants_username": any([
                re.search(r"usuario|login", normalized),
            ]),
            "wants_password": any([
                re.search(r"senha", normalized),
            ]),
            "wants_expiry": any([
                re.search(r"vence|vencimento|validade|data", normalized),
            ])
        }


# Instância global
keyword_detector = KeywordCredentialDetector()


def format_credential_response(credential: Dict, intent: Dict) -> str:
    """
    Formata resposta com credenciais baseado na intenção
    
    Args:
        credential: Dados da credencial encontrada
        intent: Intenção extraída da mensagem
        
    Returns:
        Mensagem formatada para enviar ao cliente
    """
    parts = []
    
    # Sempre incluir usuário
    if credential.get("username"):
        parts.append(f"👤 *Usuário:* {credential['username']}")
    
    # Incluir senha se solicitada ou se perguntou "usuário e senha"
    if intent.get("wants_password") or (intent.get("wants_username") and not intent.get("wants_expiry")):
        if credential.get("password"):
            parts.append(f"🔑 *Senha:* {credential['password']}")
    
    # Incluir data de vencimento se solicitada
    if intent.get("wants_expiry"):
        if credential.get("expiry_date"):
            parts.append(f"📅 *Vencimento:* {credential['expiry_date']}")
        elif credential.get("validade"):
            parts.append(f"📅 *Vencimento:* {credential['validade']}")
        else:
            parts.append(f"📅 *Vencimento:* Consulte o suporte")
    
    # Incluir URL de acesso
    if credential.get("url"):
        parts.append(f"🌐 *Acesso:* {credential['url']}")
    
    if not parts:
        return "Credenciais encontradas mas sem detalhes disponíveis."
    
    # Mensagem de cabeçalho
    header = "🔐 *Suas Credenciais de Acesso:*\n"
    
    return header + "\n".join(parts)
