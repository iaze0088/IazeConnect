"""
Serviço de Sincronização Office - Download de TODOS os clientes
Mantém banco de dados local atualizado automaticamente
"""
import asyncio
from playwright.async_api import async_playwright
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone
from typing import List, Dict, Optional
import logging
import os

logger = logging.getLogger(__name__)

class OfficeSyncService:
    """Sincronização completa de clientes do Office para banco local"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.accounts = [
            {"username": "fabiotec34", "password": "cybertv26"},
            {"username": "fabiotec35", "password": "cybertv26"},
            {"username": "fabiotec36", "password": "cybertv26"},
            {"username": "fabiotec37", "password": "cybertv26"},
            {"username": "fabiotec38", "password": "cybertv26"}
        ]
    
    async def sync_all_clients(self) -> Dict:
        """
        Sincronizar TODOS os clientes de TODOS os painéis
        """
        logger.info("🔄 Iniciando sincronização completa de clientes Office...")
        
        start_time = datetime.now(timezone.utc)
        total_clients = 0
        new_clients = 0
        updated_clients = 0
        errors = 0
        
        results_by_account = {}
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            for account in self.accounts:
                username = account["username"]
                logger.info(f"📥 Sincronizando {username}...")
                
                try:
                    result = await self._sync_account(browser, account)
                    results_by_account[username] = result
                    
                    total_clients += result["total"]
                    new_clients += result["new"]
                    updated_clients += result["updated"]
                    
                    logger.info(f"✅ {username}: {result['total']} clientes processados")
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao sincronizar {username}: {e}")
                    errors += 1
                    results_by_account[username] = {"error": str(e)}
            
            await browser.close()
        
        # Salvar registro de sincronização
        sync_record = {
            "sync_id": f"sync_{int(start_time.timestamp())}",
            "started_at": start_time.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": (datetime.now(timezone.utc) - start_time).total_seconds(),
            "summary": {
                "total_clients": total_clients,
                "new_clients": new_clients,
                "updated_clients": updated_clients,
                "errors": errors
            },
            "results_by_account": results_by_account
        }
        
        await self.db.office_sync_history.insert_one(sync_record)
        
        logger.info(f"✅ Sincronização completa: {total_clients} clientes, {new_clients} novos, {updated_clients} atualizados")
        
        return sync_record
    
    async def _sync_account(self, browser, account: Dict) -> Dict:
        """Sincronizar clientes de uma conta específica"""
        
        username = account["username"]
        password = account["password"]
        
        page = await browser.new_page()
        
        try:
            # 1. Login
            await page.goto("https://gestor.my/login", timeout=30000)
            await page.wait_for_load_state('networkidle')
            
            await page.fill('#login', username)
            await page.fill('#password', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)
            
            if 'login' in page.url.lower():
                raise Exception(f"Login falhou para {username}")
            
            # 2. Navegar para gerenciar-linhas
            await page.goto("https://gestor.my/admin/gerenciar-linhas", timeout=30000)
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(3000)
            
            # 3. Extrair TODOS os clientes
            clients = await self._extract_all_clients(page)
            
            # 4. Salvar no banco
            new_count = 0
            updated_count = 0
            
            for client in clients:
                # Adicionar metadados
                client["office_account"] = username
                client["last_synced_at"] = datetime.now(timezone.utc).isoformat()
                
                # Verificar se já existe
                existing = await self.db.office_clients.find_one({
                    "usuario": client["usuario"],
                    "office_account": username
                })
                
                if existing:
                    # Verificar se houve mudanças
                    if self._has_changes(existing, client):
                        # Salvar histórico de mudanças
                        change_record = {
                            "client_id": str(existing["_id"]),
                            "usuario": client["usuario"],
                            "office_account": username,
                            "changed_at": datetime.now(timezone.utc).isoformat(),
                            "old_data": {
                                "senha": existing.get("senha"),
                                "vencimento": existing.get("vencimento"),
                                "status": existing.get("status"),
                                "conexoes": existing.get("conexoes")
                            },
                            "new_data": {
                                "senha": client.get("senha"),
                                "vencimento": client.get("vencimento"),
                                "status": client.get("status"),
                                "conexoes": client.get("conexoes")
                            }
                        }
                        await self.db.office_changes_history.insert_one(change_record)
                        
                        # Atualizar
                        await self.db.office_clients.update_one(
                            {"_id": existing["_id"]},
                            {"$set": client}
                        )
                        updated_count += 1
                else:
                    # Novo cliente
                    await self.db.office_clients.insert_one(client)
                    new_count += 1
            
            await page.close()
            
            return {
                "total": len(clients),
                "new": new_count,
                "updated": updated_count
            }
            
        except Exception as e:
            await page.close()
            raise e
    
    async def _extract_all_clients(self, page) -> List[Dict]:
        """Extrair TODOS os clientes da tabela (todas as páginas)"""
        
        all_clients = []
        
        # Aumentar número de registros por página
        try:
            selectors = [
                '.dataTables_length select',
                'select[name="datatable_length"]',
                'select[name="example_length"]'
            ]
            
            for selector in selectors:
                try:
                    select_elem = await page.query_selector(selector)
                    if select_elem:
                        # Selecionar 100 registros (maior opção disponível)
                        await select_elem.select_option(value="100")
                        await page.wait_for_timeout(2000)
                        logger.info(f"   ✅ Configurado para mostrar 100 registros por página")
                        break
                except:
                    continue
        except Exception as e:
            logger.warning(f"   ⚠️ Não conseguiu mudar paginação: {e}")
        
        # Extrair da tabela (loop por todas as páginas)
        tables = await page.query_selector_all('table')
        
        if not tables:
            return []
        
        page_number = 1
        
        while True:
            logger.info(f"   📄 Extraindo página {page_number}...")
            
            rows = await tables[0].query_selector_all('tbody tr')
            
            if len(rows) == 0:
                break
            
            for row in rows:
                try:
                    cells = await row.query_selector_all('td')
                    
                    if len(cells) < 7:
                        continue
                    
                    cell_data = []
                    for cell in cells:
                        text = await cell.inner_text()
                        cell_data.append(text.strip())
                    
                    # Extrair dados
                    client = {
                        "nome": cell_data[0] if len(cell_data) > 0 else "",
                        "info": cell_data[1] if len(cell_data) > 1 else "",
                        "usuario": cell_data[2] if len(cell_data) > 2 else "",
                        "senha": cell_data[3] if len(cell_data) > 3 else "",
                        "telefone": cell_data[4] if len(cell_data) > 4 else "",
                        "conexoes": cell_data[5] if len(cell_data) > 5 else "",
                        "vencimento": cell_data[6] if len(cell_data) > 6 else "",
                        "status": cell_data[7] if len(cell_data) > 7 else "",
                        "extracted_at": datetime.now(timezone.utc).isoformat()
                    }
                    
                    # Normalizar telefone
                    if client["telefone"]:
                        client["telefone_normalized"] = ''.join(filter(str.isdigit, client["telefone"]))
                    
                    # Classificar status
                    status_lower = client["status"].lower()
                    if "ativo" in status_lower or "ilimitado" in status_lower:
                        client["status_type"] = "ativo"
                    elif "expirado" in status_lower:
                        client["status_type"] = "expirado"
                    elif "expirando" in status_lower:
                        client["status_type"] = "expirando"
                    else:
                        client["status_type"] = "outros"
                    
                    all_clients.append(client)
                    
                except Exception as e:
                    logger.warning(f"Erro ao extrair linha: {e}")
                    continue
            
            # Tentar ir para próxima página
            try:
                # Procurar botão "Próximo" ou "Next"
                next_button = None
                
                selectors = [
                    '.paginate_button.next:not(.disabled)',
                    'a.paginate_button.next:not(.disabled)',
                    '.pagination .next:not(.disabled) a',
                    '[aria-label="Next"]:not(.disabled)'
                ]
                
                for selector in selectors:
                    try:
                        btn = await page.query_selector(selector)
                        if btn:
                            # Verificar se não está desabilitado
                            classes = await btn.get_attribute('class')
                            if 'disabled' not in (classes or ''):
                                next_button = btn
                                break
                    except:
                        continue
                
                if next_button:
                    await next_button.click()
                    await page.wait_for_timeout(2000)
                    page_number += 1
                else:
                    logger.info(f"   ✅ Última página alcançada (total: {page_number} páginas)")
                    break
                    
            except Exception as e:
                logger.info(f"   ✅ Fim da paginação")
                break
        
        logger.info(f"   📊 Total extraído: {len(all_clients)} clientes")
        return all_clients
    
    def _has_changes(self, old: Dict, new: Dict) -> bool:
        """Verificar se houve mudanças significativas"""
        
        fields_to_compare = ["senha", "vencimento", "status", "conexoes", "telefone"]
        
        for field in fields_to_compare:
            if old.get(field) != new.get(field):
                return True
        
        return False
    
    async def get_clients_by_filters(self, filters: Dict) -> List[Dict]:
        """
        Buscar clientes com filtros
        
        Filtros disponíveis:
        - status_type: "ativo", "expirado", "outros"
        - office_account: "fabiotec34", etc
        - telefone: "19989612020"
        - usuario: "3334567oro"
        - search: busca geral
        """
        
        query = {}
        
        if filters.get("status_type"):
            query["status_type"] = filters["status_type"]
        
        if filters.get("office_account"):
            query["office_account"] = filters["office_account"]
        
        if filters.get("telefone"):
            telefone_normalized = ''.join(filter(str.isdigit, filters["telefone"]))
            query["telefone_normalized"] = telefone_normalized
        
        if filters.get("usuario"):
            query["usuario"] = {"$regex": filters["usuario"], "$options": "i"}
        
        if filters.get("search"):
            # Busca geral em múltiplos campos
            search_term = filters["search"]
            
            # Se o termo contém apenas dígitos (é um telefone), normalizar
            search_normalized = ''.join(filter(str.isdigit, search_term))
            
            if search_normalized and len(search_normalized) >= 8:
                # É um número - buscar por partes do número normalizado
                # Remover código do país (55) e DDD se presentes
                possible_numbers = [
                    search_normalized,  # Completo: 5519989612020
                    search_normalized[-10:],  # Últimos 10: 9989612020
                    search_normalized[-11:],  # Últimos 11: 19989612020
                ]
                if len(search_normalized) > 11:
                    possible_numbers.append(search_normalized[-13:])  # Com 55: 5519989612020
                
                # Buscar em nome, usuario E telefone (com regex flexível para números)
                # Usar apenas números normalizados (sem caracteres especiais)
                query["$or"] = [
                    {"nome": {"$regex": search_normalized, "$options": "i"}},
                    {"usuario": {"$regex": search_normalized, "$options": "i"}},
                    {"telefone": {"$regex": search_normalized, "$options": "i"}},
                    # Buscar também nos possíveis formatos do número
                    {"usuario": {"$regex": possible_numbers[1], "$options": "i"}},
                    {"telefone": {"$regex": possible_numbers[1], "$options": "i"}},
                ]
                
                # Se tiver mais de 11 dígitos, buscar também sem código de país
                if len(search_normalized) > 11:
                    query["$or"].extend([
                        {"usuario": {"$regex": possible_numbers[2], "$options": "i"}},
                        {"telefone": {"$regex": possible_numbers[2], "$options": "i"}},
                    ])
            else:
                # Busca por texto normal - escapar caracteres especiais de regex
                import re
                search_escaped = re.escape(search_term)
                query["$or"] = [
                    {"nome": {"$regex": search_escaped, "$options": "i"}},
                    {"usuario": {"$regex": search_escaped, "$options": "i"}},
                    {"telefone": {"$regex": search_escaped, "$options": "i"}},
                ]
        
        clients = await self.db.office_clients.find(query).to_list(length=None)
        
        # Remover _id para serialização
        for client in clients:
            client.pop("_id", None)
        
        return clients
    
    async def get_statistics(self) -> Dict:
        """Obter estatísticas dos clientes"""
        
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "account": "$office_account",
                        "status": "$status_type"
                    },
                    "count": {"$sum": 1}
                }
            }
        ]
        
        results = await self.db.office_clients.aggregate(pipeline).to_list(length=None)
        
        # Formatar resultado
        stats = {}
        total_ativos = 0
        total_expirados = 0
        total_expirando = 0
        total_outros = 0
        
        for result in results:
            account = result["_id"]["account"]
            status = result["_id"]["status"]
            count = result["count"]
            
            if account not in stats:
                stats[account] = {"ativo": 0, "expirado": 0, "expirando": 0, "outros": 0}
            
            stats[account][status] = count
            
            if status == "ativo":
                total_ativos += count
            elif status == "expirado":
                total_expirados += count
            elif status == "expirando":
                total_expirando += count
            else:
                total_outros += count
        
        return {
            "by_account": stats,
            "totals": {
                "ativo": total_ativos,
                "expirado": total_expirados,
                "expirando": total_expirando,
                "outros": total_outros,
                "total": total_ativos + total_expirados + total_expirando + total_outros
            }
        }
