"""
Serviço de integração com Office (gestor.my)
Faz scraping automático para buscar dados de clientes
"""
import httpx
import logging
import re
from typing import Optional, Dict, List
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger(__name__)

class OfficeService:
    """Serviço para integração com gestor.my via scraping"""
    
    def __init__(self):
        self.base_url = "https://gestor.my"
        self.cookies = None
        self.client = None
    
    async def login(self, username: str, password: str) -> bool:
        """
        Faz login no gestor.my
        
        Returns:
            bool: True se login bem-sucedido, False caso contrário
        """
        try:
            logger.info(f"🔐 Tentando login no Office com usuário: {username}")
            
            # Criar cliente HTTP persistente
            self.client = httpx.AsyncClient(
                timeout=30.0, 
                follow_redirects=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            
            # Fazer POST de login
            login_data = {
                "usuario": username,
                "senha": password
            }
            
            response = await self.client.post(
                f"{self.base_url}/painel/login",
                data=login_data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": f"{self.base_url}/"
                }
            )
            
            # Verificar se login foi bem-sucedido
            logger.info(f"📊 Login response status: {response.status_code}")
            
            if response.status_code == 200:
                # Salvar cookies
                self.cookies = dict(response.cookies)
                logger.info(f"✅ Login bem-sucedido no Office. Cookies salvos: {len(self.cookies)}")
                return True
            else:
                logger.error(f"❌ Falha no login: Status {response.status_code}")
                return False
                    
        except Exception as e:
            logger.error(f"❌ Erro ao fazer login no Office: {e}")
            return False
    
    async def buscar_cliente(self, credentials: Dict, search_term: str) -> Optional[Dict]:
        """
        Busca dados de um cliente no Office
        
        Args:
            credentials: {"username": "...", "password": "..."}
            search_term: Usuário ou WhatsApp para buscar
            
        Returns:
            Dict com dados do cliente ou None se não encontrado
        """
        try:
            logger.info(f"🔍 Buscando cliente: {search_term}")
            
            # Fazer login
            if not await self.login(credentials["username"], credentials["password"]):
                return {
                    "error": "Falha ao fazer login no Office",
                    "success": False
                }
            
            # URLs de busca (clientes oficiais e testes)
            search_urls = [
                f"{self.base_url}/admin/gerenciar-linhas",
                f"{self.base_url}/admin/gerenciar-testes"
            ]
            
            for url in search_urls:
                try:
                    logger.info(f"🔍 Buscando em: {url}")
                    
                    # Fazer GET na página de gerenciamento
                    response = await self.client.get(
                        url,
                        cookies=self.cookies
                    )
                    
                    if response.status_code == 200:
                        # Parsear HTML
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Buscar na página inteira pelo termo
                        page_text = soup.get_text()
                        
                        # Se o termo foi encontrado, extrair dados
                        if search_term in page_text:
                            cliente_data = self._parse_client_data(soup, search_term)
                            
                            if cliente_data and cliente_data.get('success'):
                                logger.info(f"✅ Cliente encontrado em: {url}")
                                cliente_data['source_url'] = url
                                cliente_data['tipo'] = 'Teste Grátis' if 'teste' in url else 'Cliente Oficial'
                                return cliente_data
                        else:
                            logger.info(f"⚠️ Termo '{search_term}' não encontrado em {url}")
                            
                except Exception as e:
                    logger.debug(f"Erro ao buscar em {url}: {e}")
                    continue
            
            # Se não encontrou em nenhuma URL
            logger.warning(f"❌ Cliente '{search_term}' não encontrado em nenhuma URL")
            return {
                "error": "Cliente não encontrado",
                "success": False,
                "search_term": search_term
            }
                
        except Exception as e:
            logger.error(f"❌ Erro ao buscar cliente: {e}")
            return {
                "error": str(e),
                "success": False
            }
        finally:
            # Fechar cliente HTTP
            if self.client:
                await self.client.aclose()
    
    def _parse_client_data(self, soup: BeautifulSoup, search_term: str) -> Optional[Dict]:
        """
        Parseia o HTML para extrair dados do cliente
        
        Args:
            soup: BeautifulSoup object
            search_term: Termo buscado
            
        Returns:
            Dict com dados do cliente ou None
        """
        try:
            # Procurar por tabelas com dados
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    
                    # Verificar se alguma célula contém o termo buscado
                    row_text = ' '.join([cell.get_text(strip=True) for cell in cells])
                    
                    if search_term.lower() in row_text.lower():
                        # Extrair dados da linha
                        data = {}
                        
                        # Estratégia: buscar padrões comuns
                        # Usuário (pode ser número ou texto)
                        for cell in cells:
                            text = cell.get_text(strip=True)
                            
                            # Detectar usuário (geralmente é o termo buscado)
                            if search_term in text:
                                data['usuario'] = text
                            
                            # Detectar senha (palavras como "senha" ou padrões)
                            if 'senha' in cell.get_text().lower() or len(text) == 8:
                                # Pode ser senha (8 caracteres é comum)
                                if 'senha' not in data:
                                    data['senha'] = text
                            
                            # Detectar status
                            if any(keyword in text.lower() for keyword in ['ativo', 'ativa', 'online']):
                                data['status'] = 'Ativo'
                            elif any(keyword in text.lower() for keyword in ['inativo', 'vencido', 'offline']):
                                data['status'] = 'Inativo'
                            
                            # Detectar data de vencimento
                            if re.match(r'\d{2}/\d{2}/\d{4}', text):
                                data['vencimento'] = text
                        
                        # Se conseguiu extrair pelo menos o usuário, retornar
                        if 'usuario' in data or search_term in row_text:
                            data['success'] = True
                            data['search_term'] = search_term
                            data['texto_completo'] = row_text
                            
                            # Se não achou usuário explícito, usar o termo de busca
                            if 'usuario' not in data:
                                data['usuario'] = search_term
                            
                            logger.info(f"✅ Dados extraídos: {data}")
                            return data
            
            # Se não encontrou em tabelas, tentar buscar no HTML geral
            page_text = soup.get_text()
            
            if search_term.lower() in page_text.lower():
                # Cliente existe na página, retornar dados básicos
                data = {
                    'success': True,
                    'usuario': search_term,
                    'search_term': search_term,
                    'texto_completo': f'Cliente {search_term} encontrado no sistema',
                    'info': 'Dados encontrados mas não foi possível extrair detalhes completos'
                }
                
                # Tentar encontrar senha com regex
                senha_match = re.search(rf'{search_term}[^\w]*([A-Za-z0-9]{{6,12}})', page_text)
                if senha_match:
                    data['senha'] = senha_match.group(1)
                
                return data
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao parsear dados: {e}")
            return None
    
    async def renovar_cliente(self, credentials: Dict, usuario: str, dias: int = 30) -> Dict:
        """
        Renova a conta de um cliente
        
        Args:
            credentials: Credenciais do Office
            usuario: Usuário a ser renovado
            dias: Dias de renovação (padrão 30)
            
        Returns:
            Dict com resultado da operação
        """
        try:
            logger.info(f"🔄 Renovando cliente: {usuario} por {dias} dias")
            
            # Fazer login
            if not await self.login(credentials["username"], credentials["password"]):
                return {
                    "error": "Falha ao fazer login no Office",
                    "success": False
                }
            
            # Tentar encontrar endpoint de renovação
            # Como não temos a estrutura exata, retornar que precisa ser feito manualmente
            return {
                "success": False,
                "error": "Renovação deve ser feita manualmente no painel do Office",
                "message": f"Para renovar {usuario} por {dias} dias, acesse: https://gestor.my/admin/gerenciar-linhas",
                "usuario": usuario,
                "dias": dias
            }
                    
        except Exception as e:
            logger.error(f"❌ Erro ao renovar cliente: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            if self.client:
                await self.client.aclose()

# Instância global
office_service = OfficeService()
