"""
Serviço de integração com Office (gestor.my) usando Playwright
Faz scraping automático com navegador real
"""
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import logging
import re
from typing import Optional, Dict
import asyncio

logger = logging.getLogger(__name__)

class OfficeServicePlaywright:
    """Serviço para integração com gestor.my via Playwright (navegador real)"""
    
    def __init__(self):
        self.base_url = "https://gestor.my"
        
    async def buscar_cliente(self, credentials: Dict, search_term: str) -> Dict:
        """
        Busca dados de um cliente no Office usando navegador real
        
        Args:
            credentials: {"username": "...", "password": "..."}
            search_term: Usuário ou WhatsApp para buscar
            
        Returns:
            Dict com dados do cliente
        """
        # Normalizar search_term
        import re
        original_search = search_term
        search_term = search_term.strip()
        
        # Detectar se é SOMENTE número (telefone) ou tem letras (username)
        has_letters = bool(re.search(r'[a-zA-Z]', search_term))
        has_numbers = bool(re.search(r'\d', search_term))
        
        if has_numbers and not has_letters:
            # É SOMENTE número = TELEFONE → remover caracteres especiais
            search_term = re.sub(r'[^\d]', '', search_term)
            logger.info(f"📞 Telefone normalizado: '{original_search}' → '{search_term}'")
        elif has_letters:
            # Tem LETRAS = USERNAME → manter letras e números, remover apenas espaços e caracteres especiais
            search_term = re.sub(r'[^a-zA-Z0-9]', '', search_term)
            logger.info(f"👤 Username normalizado: '{original_search}' → '{search_term}'")
        else:
            # Apenas caracteres especiais ou vazio
            logger.warning(f"⚠️ Search term inválido: '{original_search}'")
        
        logger.info(f"🔍 Iniciando busca com Playwright: {search_term}")
        
        async with async_playwright() as p:
            try:
                # Lançar navegador
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                context = await browser.new_context()
                page = await context.new_page()
                
                # 1. Fazer login
                logger.info(f"🔐 Fazendo login com usuário: {credentials['username']}")
                await page.goto(f"{self.base_url}/login", timeout=30000)
                
                # Aguardar página carregar
                await page.wait_for_load_state('networkidle', timeout=10000)
                
                # Tirar screenshot antes do login
                await page.screenshot(path='/tmp/office_before_login.png')
                logger.info("📸 Screenshot 1: Página de login")
                
                # Debug: Verificar se campos existem
                username_field = await page.query_selector('input[type="text"]')
                password_field = await page.query_selector('input[type="password"]')
                
                if not username_field or not password_field:
                    logger.error("❌ Campos de login não encontrados!")
                    # Tentar seletores alternativos
                    username_field = await page.query_selector('input[name="username"], input[id="username"], input[placeholder*="usuário"]')
                    password_field = await page.query_selector('input[name="password"], input[id="password"], input[placeholder*="senha"]')
                
                if username_field and password_field:
                    # Preencher formulário de login
                    logger.info(f"✅ Campos encontrados, preenchendo...")
                    await username_field.fill(credentials['username'])
                    await password_field.fill(credentials['password'])
                    
                    # Tirar screenshot após preencher
                    await page.screenshot(path='/tmp/office_filled.png')
                    logger.info("📸 Screenshot 2: Formulário preenchido")
                    
                    # Clicar no botão de login
                    login_button = await page.query_selector('button[type="submit"], input[type="submit"], button:has-text("Entrar"), button:has-text("Login")')
                    if login_button:
                        await login_button.click()
                        logger.info("🖱️ Clicou no botão de login")
                    else:
                        logger.warning("⚠️ Botão de login não encontrado, tentando Enter")
                        await password_field.press('Enter')
                else:
                    logger.error("❌ Não foi possível encontrar campos de login!")
                    await browser.close()
                    return {
                        "success": False,
                        "error": "Campos de login não encontrados na página"
                    }
                
                # Aguardar navegação ou mudança de URL
                try:
                    await page.wait_for_url('**/admin/**', timeout=10000)
                    logger.info("✅ Redirecionado para admin")
                except:
                    # Se não redirecionou, aguardar load state
                    await page.wait_for_load_state('networkidle', timeout=15000)
                
                # Screenshot após login
                await page.screenshot(path='/tmp/office_after_login.png')
                logger.info(f"✅ Login realizado. URL atual: {page.url}")
                logger.info("📸 Screenshot 3: Após login")
                
                # Se ainda não está em /admin, verificar se login foi bem-sucedido
                if '/admin' not in page.url:
                    logger.warning(f"⚠️ Login pode ter falhado. URL atual: {page.url}")
                    # Tentar navegar diretamente para admin/home
                    await page.goto(f"{self.base_url}/admin/home", timeout=15000)
                    logger.info(f"✅ Navegado manualmente para admin/home")
                
                # 2. Buscar em clientes oficiais
                result = await self._search_in_page(
                    page, 
                    f"{self.base_url}/admin/gerenciar-linhas",
                    search_term,
                    "Cliente Oficial"
                )
                
                if result and result.get('success'):
                    await browser.close()
                    return result
                
                # 3. Buscar em testes grátis
                result = await self._search_in_page(
                    page,
                    f"{self.base_url}/admin/gerenciar-testes",
                    search_term,
                    "Teste Grátis"
                )
                
                if result and result.get('success'):
                    await browser.close()
                    return result
                
                # 4. BUSCA DIRETA usando campo de pesquisa
                logger.info(f"🔍 Tentando busca direta no painel usando campo Pesquisar...")
                
                # Navegar para gerenciar linhas
                await page.goto(f"{self.base_url}/admin/gerenciar-linhas", timeout=30000)
                await page.wait_for_load_state('networkidle', timeout=10000)
                
                # Aguardar um pouco para página carregar completamente
                await page.wait_for_timeout(2000)
                
                # Tentar encontrar campo de busca com múltiplos seletores
                search_field = None
                selectors_to_try = [
                    'input[type="search"]',
                    'input[placeholder*="Pesquisar"]',
                    'input[placeholder*="pesquisar"]', 
                    'input[placeholder*="Buscar"]',
                    'input[aria-label*="search"]',
                    '.dataTables_filter input',
                    '#search',
                    'input.form-control[type="search"]'
                ]
                
                for selector in selectors_to_try:
                    try:
                        search_field = await page.query_selector(selector)
                        if search_field:
                            logger.info(f"✅ Campo de busca encontrado com seletor: {selector}")
                            break
                    except:
                        continue
                
                if search_field:
                    # Limpar campo primeiro
                    await search_field.fill('')
                    await page.wait_for_timeout(500)
                    
                    # Digitar termo de busca
                    logger.info(f"⌨️ Digitando no campo de pesquisa: {search_term}")
                    await search_field.fill(search_term)
                    await page.wait_for_timeout(3000)  # Aguardar filtro aplicar
                    
                    # Screenshot após pesquisa
                    await page.screenshot(path='/tmp/office_after_search.png')
                    logger.info(f"📸 Screenshot após pesquisa salvo")
                    
                    # Tentar extrair dados filtrados da tabela
                    result = await self._extract_from_current_page(page, search_term, "Cliente Oficial")
                    if result and result.get('success'):
                        await browser.close()
                        return result
                else:
                    logger.warning("⚠️ Campo de pesquisa não encontrado")
                
                # Não encontrado
                await browser.close()
                return {
                    "success": False,
                    "error": "Cliente não encontrado após busca",
                    "search_term": search_term
                }
                
            except PlaywrightTimeout as e:
                logger.error(f"❌ Timeout: {e}")
                return {
                    "success": False,
                    "error": f"Timeout ao acessar o Office: {str(e)}"
                }
            except Exception as e:
                logger.error(f"❌ Erro ao buscar cliente: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }
    
    async def _search_in_page(self, page, url: str, search_term: str, tipo: str) -> Optional[Dict]:
        """
        Busca em uma página específica
        """
        try:
            logger.info(f"🔍 Buscando em: {url}")
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Aguardar mais tempo para AJAX carregar
            await page.wait_for_timeout(2000)
            
            # Rolar a página para baixo para forçar carregamento de lazy load
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            
            # Rolar de volta para cima
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(1000)
            
            # Screenshot da página de busca
            page_name = url.split('/')[-1]
            await page.screenshot(path=f'/tmp/office_search_{page_name}.png')
            logger.info(f"📸 Screenshot: Página {page_name}")
            
            # Pegar todo o conteúdo da página
            content = await page.content()
            
            # Salvar HTML para debug
            with open(f'/tmp/office_{page_name}.html', 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"💾 HTML salvo: /tmp/office_{page_name}.html")
            
            # Verificar se o termo está na página (case-insensitive)
            if search_term.lower() not in content.lower():
                logger.info(f"⚠️ Termo '{search_term}' não encontrado em {url}")
                return None
            
            logger.info(f"✅ Termo '{search_term}' encontrado em {url}")
            
            # Tentar extrair dados da tabela
            # Procurar por linhas da tabela que contenham o termo
            try:
                # Aguardar tabela carregar (mas não falhar se não houver)
                tables = await page.query_selector_all('table')
                logger.info(f"📊 Encontradas {len(tables)} tabelas na página")
                
                if len(tables) == 0:
                    raise Exception("Nenhuma tabela encontrada")
                
                # Pegar todas as linhas da primeira tabela
                rows = await tables[0].query_selector_all('tr')
                logger.info(f"📋 Encontradas {len(rows)} linhas na tabela")
                
                for row in rows:
                    row_text = await row.inner_text()
                    
                    logger.info(f"🔎 Verificando linha (primeiros 50 chars): {row_text[:50]}")
                    
                    if search_term.lower() in row_text.lower():
                        logger.info(f"📋 Linha encontrada com termo: {row_text[:100]}")
                        
                        # Extrair células
                        cells = await row.query_selector_all('td')
                        
                        if len(cells) >= 2:
                            # Extrair dados das células
                            cell_texts = []
                            for cell in cells:  # Pegar todas as células
                                text = await cell.inner_text()
                                cell_texts.append(text.strip())
                            
                            logger.info(f"📋 Células extraídas: {cell_texts[:8]}")  # Log primeiras 8
                            
                            # Montar resposta baseada na estrutura da tabela gestor.my
                            # Estrutura: [Nome, Info, Usuário, Senha, Telefone, Conexões, Vencimento, Status, Ações]
                            data = {
                                "success": True,
                                "search_term": search_term,
                                "tipo": tipo,
                                "source_url": url
                            }
                            
                            # Mapear campos pela posição
                            if len(cell_texts) >= 8:
                                data['usuario'] = cell_texts[2]  # Coluna 3: Usuário
                                data['senha'] = cell_texts[3]    # Coluna 4: Senha
                                data['telefone'] = cell_texts[4] if cell_texts[4] else None  # Coluna 5: Telefone
                                data['conexoes'] = cell_texts[5] # Coluna 6: Conexões
                                data['vencimento'] = cell_texts[6]  # Coluna 7: Vencimento
                                data['status'] = cell_texts[7]      # Coluna 8: Status
                            else:
                                # Fallback: tentar identificar campos
                                for i, text in enumerate(cell_texts):
                                    if text and len(text) > 0:
                                        # Se parece com senha (alfanumérico, 6-12 chars)
                                        if re.match(r'^[A-Za-z0-9]{6,12}$', text) and text != search_term:
                                            data['senha'] = text
                                        
                                        # Se parece com data (yyyy-mm-dd ou dd/mm/yyyy)
                                        if re.match(r'(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})', text):
                                            data['vencimento'] = text
                                        
                                        # Se contém "ativo" ou "expirado"
                                        if any(kw in text.upper() for kw in ['ATIVO', 'EXPIRADO', 'INATIVO']):
                                            data['status'] = text
                                
                                # Garantir que pelo menos usuário está setado
                                if 'usuario' not in data:
                                    data['usuario'] = search_term
                            
                            # Adicionar texto completo para referência
                            data['texto_completo'] = ' | '.join(cell_texts[:8])
                            
                            logger.info(f"✅ Dados extraídos: {data}")
                            return data
                
            except Exception as e:
                logger.warning(f"⚠️ Erro ao parsear tabela: {e}")
            
            # Se não conseguiu extrair da tabela, retornar dados básicos
            return {
                "success": True,
                "usuario": search_term,
                "search_term": search_term,
                "tipo": tipo,
                "source_url": url,
                "info": "Cliente encontrado, mas não foi possível extrair todos os detalhes"
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar em {url}: {e}")
            return None
    
    async def _extract_from_current_page(self, page, search_term: str, tipo: str) -> Optional[Dict]:
        """
        Extrai dados da página atual (usado após filtro de busca)
        """
        try:
            content = await page.content()
            
            if search_term.lower() not in content.lower():
                return None
            
            # Pegar tabelas
            tables = await page.query_selector_all('table')
            
            if len(tables) == 0:
                return None
            
            # Buscar nas linhas
            rows = await tables[0].query_selector_all('tr')
            
            for row in rows:
                row_text = await row.inner_text()
                
                if search_term.lower() in row_text.lower():
                    cells = await row.query_selector_all('td')
                    
                    if len(cells) >= 2:
                        cell_texts = []
                        for cell in cells:
                            text = await cell.inner_text()
                            cell_texts.append(text.strip())
                        
                        data = {
                            "success": True,
                            "search_term": search_term,
                            "tipo": tipo,
                            "source_url": page.url
                        }
                        
                        # Mapear campos pela posição
                        if len(cell_texts) >= 8:
                            data['usuario'] = cell_texts[2]
                            data['senha'] = cell_texts[3]
                            data['telefone'] = cell_texts[4] if cell_texts[4] else None
                            data['conexoes'] = cell_texts[5]
                            data['vencimento'] = cell_texts[6] if cell_texts[6] else "ILIMITADO"
                            data['status'] = cell_texts[7]
                        else:
                            if 'usuario' not in data:
                                data['usuario'] = search_term
                        
                        data['texto_completo'] = ' | '.join(cell_texts[:8])
                        
                        logger.info(f"✅ Dados extraídos via filtro: {data}")
                        return data
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair da página atual: {e}")
            return None

# Instância global
office_service_playwright = OfficeServicePlaywright()
