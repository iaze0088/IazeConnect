"""
Serviço de Auto-Busca de Credenciais por Telefone
"""
import logging
import re
from typing import Optional, Dict, List
from datetime import datetime, timezone, date

logger = logging.getLogger(__name__)

class CredentialAutoSearch:
    """Busca automática de credenciais por telefone"""
    
    def __init__(self):
        pass
    
    def normalize_phone_formats(self, phone: str) -> List[str]:
        """
        Gera todas as variações possíveis de um número de telefone
        
        Exemplo: +5519982769291
        Retorna: [
            "5519982769291",
            "19982769291", 
            "982769291",
            "5519982769291",
            "+5519982769291"
        ]
        """
        # Remover caracteres especiais
        clean = re.sub(r'[^\d]', '', phone)
        
        formats = set()
        
        # Adicionar o número limpo
        formats.add(clean)
        
        # Se tem DDI (55)
        if clean.startswith('55'):
            # Sem DDI
            without_ddi = clean[2:]
            formats.add(without_ddi)
            
            # Só DDD + número (sem 9 extra se tiver)
            if len(without_ddi) >= 11:
                ddd = without_ddi[:2]
                numero = without_ddi[2:]
                
                # Com 9
                formats.add(f"{ddd}{numero}")
                
                # Sem 9 (se começar com 9)
                if numero.startswith('9') and len(numero) == 9:
                    formats.add(f"{ddd}{numero[1:]}")
                
                # Sem DDD
                formats.add(numero)
                if numero.startswith('9') and len(numero) == 9:
                    formats.add(numero[1:])
        
        # Com +
        formats.add(f"+{clean}")
        
        # Só os últimos 8 ou 9 dígitos
        if len(clean) >= 8:
            formats.add(clean[-8:])
        if len(clean) >= 9:
            formats.add(clean[-9:])
        
        logger.info(f"📱 Gerados {len(formats)} formatos para {phone}: {list(formats)[:5]}...")
        
        return list(formats)
    
    async def search_credentials_by_phone(
        self, 
        phone: str, 
        office_credentials_list: List[Dict],
        office_service
    ) -> Optional[Dict]:
        """
        Busca credenciais usando todas as variações de telefone
        
        Args:
            phone: Número de telefone
            office_credentials_list: Lista de credenciais do Office
            office_service: Instância do serviço Office
            
        Returns:
            Dict com credenciais encontradas ou None
        """
        try:
            # Gerar todos os formatos
            phone_formats = self.normalize_phone_formats(phone)
            
            logger.info(f"🔍 Buscando credenciais para telefone: {phone}")
            logger.info(f"📋 Testando {len(phone_formats)} formatos")
            
            # Tentar cada formato em cada Office
            for phone_format in phone_formats:
                for office_cred in office_credentials_list:
                    try:
                        result = await office_service.buscar_cliente(
                            {
                                "username": office_cred["username"],
                                "password": office_cred["password"]
                            },
                            phone_format
                        )
                        
                        if result and result.get("success"):
                            logger.info(f"✅ Credenciais encontradas! Formato: {phone_format}, Office: {office_cred['username']}")
                            
                            # Adicionar informações extras
                            result["phone_used"] = phone_format
                            result["office_used"] = office_cred["username"]
                            
                            return result
                            
                    except Exception as e:
                        logger.debug(f"Erro ao buscar {phone_format} em {office_cred['username']}: {e}")
                        continue
            
            logger.warning(f"❌ Credenciais não encontradas para telefone: {phone}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar credenciais por telefone: {e}")
            return None
    
    def should_search_today(self, last_search_date: Optional[str]) -> bool:
        """
        Verifica se deve buscar novamente hoje
        
        Args:
            last_search_date: Data da última busca (ISO format)
            
        Returns:
            bool: True se deve buscar novamente
        """
        if not last_search_date:
            return True
        
        try:
            last_date = datetime.fromisoformat(last_search_date).date()
            today = datetime.now(timezone.utc).date()
            
            return today > last_date
            
        except:
            return True

# Instância global
credential_auto_search = CredentialAutoSearch()
