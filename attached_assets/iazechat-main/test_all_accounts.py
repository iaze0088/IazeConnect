"""
Busca avançada no Office - Testa todas as contas e usa paginação
"""
import asyncio
from playwright.async_api import async_playwright

async def search_in_all_accounts(search_term):
    """Busca em todas as contas office"""
    
    accounts = [
        "fabiotec34",
        "fabiotec35", 
        "fabiotec36",
        "fabiotec37",
        "fabiotec38"
    ]
    password = "cybertv26"
    
    print(f"🔍 Buscando '{search_term}' em {len(accounts)} contas...")
    print("")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        for account in accounts:
            print(f"{'='*60}")
            print(f"🔐 Testando conta: {account}")
            print(f"{'='*60}")
            
            page = await browser.new_page()
            
            try:
                # Login
                await page.goto("https://gestor.my/login", timeout=30000)
                await page.wait_for_load_state('networkidle')
                
                await page.fill('#login', account)
                await page.fill('#password', password)
                await page.click('button[type="submit"]')
                await page.wait_for_timeout(5000)
                
                if 'login' in page.url.lower():
                    print(f"   ❌ Login falhou para {account}")
                    await page.close()
                    continue
                
                print(f"   ✅ Login OK")
                
                # Navegar para gerenciar-linhas
                await page.goto("https://gestor.my/admin/gerenciar-linhas", timeout=30000)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_timeout(3000)
                
                # Tentar usar campo de busca primeiro
                print(f"   🔍 Tentando usar campo de busca...")
                
                search_field = None
                selectors = [
                    'input[type="search"]',
                    '.dataTables_filter input',
                    'input[placeholder*="Pesquisar"]',
                    'input[placeholder*="pesquisar"]'
                ]
                
                for selector in selectors:
                    try:
                        field = await page.query_selector(selector)
                        if field:
                            search_field = field
                            print(f"   ✅ Campo de busca encontrado: {selector}")
                            break
                    except:
                        pass
                
                if search_field:
                    # Usar campo de busca
                    await search_field.fill(search_term)
                    await page.wait_for_timeout(2000)
                    
                    # Verificar se encontrou
                    content = await page.content()
                    
                    variations = [
                        search_term,
                        f"({search_term[:2]}) {search_term[2:7]}-{search_term[7:]}",
                        f"{search_term[:2]} {search_term[2:7]}-{search_term[7:]}"
                    ]
                    
                    found = False
                    for var in variations:
                        if var in content:
                            found = True
                            print(f"   ✅ ENCONTRADO: '{var}'")
                            
                            # Extrair dados
                            tables = await page.query_selector_all('table')
                            if tables:
                                rows = await tables[0].query_selector_all('tbody tr')
                                for row in rows:
                                    row_text = await row.inner_text()
                                    if var.lower() in row_text.lower() or search_term.lower() in row_text.lower():
                                        cells = await row.query_selector_all('td')
                                        cell_data = []
                                        for cell in cells:
                                            cell_data.append((await cell.inner_text()).strip())
                                        
                                        print("")
                                        print(f"   🎉 CLIENTE ENCONTRADO EM: {account}")
                                        print("")
                                        print(f"   📊 Dados:")
                                        if len(cell_data) >= 7:
                                            print(f"      👤 Nome: {cell_data[0]}")
                                            print(f"      🆔 Usuário: {cell_data[2]}")
                                            print(f"      🔑 Senha: {cell_data[3]}")
                                            print(f"      📱 Telefone: {cell_data[4]}")
                                            print(f"      📡 Conexões: {cell_data[5]}")
                                            print(f"      📅 Vencimento: {cell_data[6]}")
                                            print(f"      🟢 Status: {cell_data[7] if len(cell_data) > 7 else 'N/A'}")
                                        
                                        await page.close()
                                        await browser.close()
                                        return True
                            break
                    
                    if found:
                        continue
                    else:
                        print(f"   ❌ Não encontrado com campo de busca")
                else:
                    print(f"   ⚠️ Campo de busca não encontrado, usando busca manual...")
                
                # Busca manual na tabela
                tables = await page.query_selector_all('table')
                if tables:
                    rows = await tables[0].query_selector_all('tbody tr')
                    total_rows = len(rows)
                    print(f"   📋 {total_rows} linhas visíveis")
                    
                    # Verificar primeiras linhas
                    for i, row in enumerate(rows):
                        row_text = await row.inner_text()
                        if search_term.lower() in row_text.lower():
                            cells = await row.query_selector_all('td')
                            cell_data = []
                            for cell in cells:
                                cell_data.append((await cell.inner_text()).strip())
                            
                            print("")
                            print(f"   🎉 CLIENTE ENCONTRADO EM: {account} (linha {i})")
                            print("")
                            print(f"   📊 Dados:")
                            if len(cell_data) >= 7:
                                print(f"      👤 Nome: {cell_data[0]}")
                                print(f"      🆔 Usuário: {cell_data[2]}")
                                print(f"      🔑 Senha: {cell_data[3]}")
                                print(f"      📱 Telefone: {cell_data[4]}")
                                print(f"      📡 Conexões: {cell_data[5]}")
                                print(f"      📅 Vencimento: {cell_data[6]}")
                                print(f"      🟢 Status: {cell_data[7] if len(cell_data) > 7 else 'N/A'}")
                            
                            await page.close()
                            await browser.close()
                            return True
                    
                    print(f"   ❌ Não encontrado nas linhas visíveis")
                
                await page.close()
                
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                await page.close()
                continue
            
            print("")
        
        await browser.close()
        
        print("")
        print(f"❌ Cliente '{search_term}' não encontrado em nenhuma das {len(accounts)} contas")
        return False

# Testar com telefone
print("="*70)
print("TESTE 1: Buscar por TELEFONE")
print("="*70)
asyncio.run(search_in_all_accounts("19989612020"))

print("")
print("")

# Testar com usuário
print("="*70)
print("TESTE 2: Buscar por USUÁRIO")
print("="*70)
asyncio.run(search_in_all_accounts("3334567oro"))
