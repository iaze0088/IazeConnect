"""
Serviço XUI adaptado para diferentes versões
Suporta múltiplos métodos de autenticação e endpoints
"""
import httpx
import os
from datetime import datetime
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

class XUIService:
    """Serviço para integração com XUI Panel - Versão Adaptável"""
    
    def __init__(self):
        self.xui_url = os.environ.get('XUI_API_URL', '')
        self.xui_api_key = os.environ.get('XUI_API_KEY', '')
        self.xui_username = os.environ.get('XUI_USERNAME', '')
        self.xui_password = os.environ.get('XUI_PASSWORD', '')
        
        logger.info(f"🎬 XUI Service inicializado: {self.xui_url}")
    
    async def search_user_by_username(self, username: str) -> Optional[Dict]:
        """
        Buscar usuário no XUI - Método Adaptável
        Tenta múltiplos métodos de autenticação
        """
        try:
            # Método 1: Tentar com Access Code (Reseller API)
            if self.xui_api_key:
                logger.info(f"🔍 Tentando buscar {username} via Access Code...")
                result = await self._search_with_access_code(username)
                if result:
                    return result
            
            # Método 2: Tentar com username/password (API padrão)
            if self.xui_username and self.xui_password:
                logger.info(f"🔍 Tentando buscar {username} via username/password...")
                result = await self._search_with_credentials(username)
                if result:
                    return result
            
            logger.warning(f"⚠️ Usuário {username} não encontrado em nenhum método")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar usuário: {e}")
            return None
    
    async def _search_with_access_code(self, username: str) -> Optional[Dict]:
        """Buscar usando Access Code (Reseller API)"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Endpoint padrão XUI com Access Code
                response = await client.get(
                    f"{self.xui_url}/api/line/username/{username}",
                    headers={"apikey": self.xui_api_key}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return self._format_user_data(data)
                    
        except Exception as e:
            logger.debug(f"Método Access Code falhou: {e}")
            return None
    
    async def _search_with_credentials(self, username: str) -> Optional[Dict]:
        """Buscar usando username/password (player_api.php style)"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Estilo player_api.php
                response = await client.get(
                    f"{self.xui_url}/player_api.php",
                    params={
                        "username": self.xui_username,
                        "password": self.xui_password,
                        "action": "get_line_info",
                        "line_username": username
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return self._format_user_data(data)
                    
        except Exception as e:
            logger.debug(f"Método credentials falhou: {e}")
            return None
    
    async def search_users_by_keyword(self, keyword: str) -> List[Dict]:
        """
        Buscar múltiplos usuários por keyword
        Retorna mock data por enquanto até descobrir endpoint correto
        """
        logger.info(f"🔍 Busca por keyword: {keyword}")
        
        # Por enquanto, retorna exemplo
        # Quando descobrir o endpoint correto, implementar aqui
        return []
    
    def _format_user_data(self, raw_data: Dict) -> Dict:
        """Formatar dados do usuário para padrão IAZE"""
        try:
            # Tentar extrair campos comuns
            username = (raw_data.get('username') or 
                       raw_data.get('user') or 
                       raw_data.get('line_username'))
            
            password = (raw_data.get('password') or 
                       raw_data.get('pass') or 
                       raw_data.get('line_password'))
            
            # Data de expiração
            exp_date = (raw_data.get('exp_date') or 
                       raw_data.get('expiration_date') or
                       raw_data.get('exp'))
            
            if exp_date:
                if isinstance(exp_date, int):
                    exp_date_formatted = datetime.fromtimestamp(exp_date).strftime('%d/%m/%Y')
                else:
                    exp_date_formatted = str(exp_date)
            else:
                exp_date_formatted = "N/A"
            
            # Status
            is_active = raw_data.get('is_active', raw_data.get('active', False))
            status = "Ativo" if is_active else "Inativo"
            
            # Conexões
            max_connections = raw_data.get('max_connections', 1)
            active_connections = raw_data.get('active_connections', 0)
            
            return {
                "username": username or "N/A",
                "password": password or "N/A",
                "expiration_date": exp_date_formatted,
                "status": status,
                "is_active": is_active,
                "max_connections": max_connections,
                "active_connections": active_connections,
                "package": raw_data.get('package'),
                "notes": raw_data.get('notes')
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao formatar dados: {e}")
            return {
                "username": "Erro ao formatar",
                "password": "N/A",
                "expiration_date": "N/A",
                "status": "Desconhecido",
                "is_active": False,
                "max_connections": 1,
                "active_connections": 0
            }
    
    async def check_connection(self) -> bool:
        """Verificar se consegue conectar no XUI"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(self.xui_url)
                return response.status_code in [200, 301, 302]
        except Exception as e:
            logger.error(f"❌ Erro ao verificar conexão: {e}")
            return False
