"""
Serviço de Integração XUI (IPTV Panel)
Permite consultar usuários, senhas e datas de vencimento
"""
import httpx
import os
from datetime import datetime
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

class XUIService:
    """Serviço para integração com XUI Panel"""
    
    def __init__(self):
        # Configurações do XUI (devem estar no .env)
        self.xui_url = os.environ.get('XUI_API_URL', '')
        self.xui_username = os.environ.get('XUI_USERNAME', '')
        self.xui_password = os.environ.get('XUI_PASSWORD', '')
        self.xui_api_key = os.environ.get('XUI_API_KEY', '')
        
        logger.info(f"🎬 XUI Service inicializado: {self.xui_url}")
    
    async def authenticate(self) -> Optional[str]:
        """
        Autenticar no XUI e obter token
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.xui_url}/api/auth",
                    json={
                        "username": self.xui_username,
                        "password": self.xui_password
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    token = data.get('token') or data.get('api_token')
                    logger.info("✅ XUI autenticado com sucesso")
                    return token
                else:
                    logger.error(f"❌ Erro na autenticação XUI: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Erro ao autenticar no XUI: {e}")
            return None
    
    async def search_user_by_username(self, username: str) -> Optional[Dict]:
        """
        Buscar usuário no XUI pelo nome de usuário
        """
        try:
            # Tentar autenticação
            token = await self.authenticate()
            if not token and not self.xui_api_key:
                logger.error("❌ Sem token de autenticação XUI")
                return None
            
            # Usar API key ou token
            headers = {}
            if self.xui_api_key:
                headers['Authorization'] = f'Bearer {self.xui_api_key}'
            elif token:
                headers['Authorization'] = f'Bearer {token}'
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Endpoint para buscar usuário
                response = await client.get(
                    f"{self.xui_url}/api/user/{username}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    logger.info(f"✅ Usuário encontrado no XUI: {username}")
                    
                    # Formatar dados
                    return self._format_user_data(user_data)
                else:
                    logger.warning(f"⚠️ Usuário não encontrado no XUI: {username}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Erro ao buscar usuário no XUI: {e}")
            return None
    
    async def search_users_by_keyword(self, keyword: str) -> List[Dict]:
        """
        Buscar múltiplos usuários no XUI por palavra-chave
        """
        try:
            token = await self.authenticate()
            if not token and not self.xui_api_key:
                return []
            
            headers = {}
            if self.xui_api_key:
                headers['Authorization'] = f'Bearer {self.xui_api_key}'
            elif token:
                headers['Authorization'] = f'Bearer {token}'
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Buscar todos os usuários e filtrar
                response = await client.get(
                    f"{self.xui_url}/api/users",
                    headers=headers,
                    params={"search": keyword}
                )
                
                if response.status_code == 200:
                    users = response.json()
                    logger.info(f"✅ Encontrados {len(users)} usuários no XUI")
                    
                    # Formatar cada usuário
                    return [self._format_user_data(user) for user in users]
                else:
                    logger.warning(f"⚠️ Erro ao buscar usuários: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Erro ao buscar usuários no XUI: {e}")
            return []
    
    def _format_user_data(self, raw_data: Dict) -> Dict:
        """
        Formatar dados do usuário XUI para padrão IAZE
        """
        try:
            # Extrair campos comuns do XUI
            username = raw_data.get('username') or raw_data.get('user')
            password = raw_data.get('password') or raw_data.get('pass')
            
            # Data de expiração (pode vir em formatos diferentes)
            exp_date = raw_data.get('exp_date') or raw_data.get('expiration_date')
            if exp_date:
                # Converter timestamp Unix para data legível
                if isinstance(exp_date, int):
                    exp_date_formatted = datetime.fromtimestamp(exp_date).strftime('%d/%m/%Y')
                else:
                    exp_date_formatted = exp_date
            else:
                exp_date_formatted = "N/A"
            
            # Status
            is_active = raw_data.get('is_active') or raw_data.get('active') or False
            status = "Ativo" if is_active else "Inativo"
            
            # Conexões
            max_connections = raw_data.get('max_connections') or raw_data.get('max_conns') or 1
            active_connections = raw_data.get('active_connections') or raw_data.get('active_conns') or 0
            
            return {
                "username": username,
                "password": password,
                "expiration_date": exp_date_formatted,
                "status": status,
                "is_active": is_active,
                "max_connections": max_connections,
                "active_connections": active_connections,
                "package": raw_data.get('package') or raw_data.get('bouquet'),
                "created_at": raw_data.get('created_at'),
                "notes": raw_data.get('notes') or raw_data.get('admin_notes')
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao formatar dados do usuário: {e}")
            return raw_data
    
    async def check_connection(self) -> bool:
        """
        Verificar se a conexão com XUI está funcionando
        """
        try:
            token = await self.authenticate()
            return token is not None or bool(self.xui_api_key)
        except Exception as e:
            logger.error(f"❌ Erro ao verificar conexão XUI: {e}")
            return False
