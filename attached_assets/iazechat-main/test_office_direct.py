"""
Teste focado de busca no Office com logging detalhado
"""
import asyncio
from playwright.async_api import async_playwright
import sys

async def test_office_search():
    """Teste direto de busca no Office"""
    
    search_term = "19989612020"  # Telefone
    # search_term = "3334567oro"  # Username
    
    print(f"🔍 Buscando: {search_term}")
    print("")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # 1. Login
            print("1️⃣ Acessando login...")
            await page.goto("https://gestor.my/login", timeout=30000)
            await page.wait_for_load_state('networkidle')
            
            print("2️⃣ Preenchendo credenciais...")
            await page.fill('#login', 'fabiotec35')
            await page.fill('#password', '102030@ab')
            
            print("3️⃣ Clicando em entrar...")
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)
            
            current_url = page.url
            print(f"4️⃣ URL após login: {current_url}")
            
            if 'login' in current_url.lower():
                print("❌ Login falhou! Ainda na página de login")
                await browser.close()
                return
            
            print("✅ Login OK!")
            
            # 2. Navegar para gerenciar linhas
            print("")
            print("5️⃣ Navegando para gerenciar-linhas...")
            await page.goto("https://gestor.my/admin/gerenciar-linhas", timeout=30000)
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(3000)
            
            # 3. Buscar campo de pesquisa
            print("6️⃣ Procurando campo de pesquisa...")
            
            # Listar todos os inputs da página
            inputs = await page.query_selector_all('input')
            print(f"   Encontrados {len(inputs)} campos input")
            
            for i, inp in enumerate(inputs):
                inp_type = await inp.get_attribute('type')
                inp_placeholder = await inp.get_attribute('placeholder')
                inp_class = await inp.get_attribute('class')
                print(f"   Input {i}: type={inp_type}, placeholder={inp_placeholder}, class={inp_class}")
            
            # 4. Tentar buscar na tabela diretamente
            print("")
            print("7️⃣ Buscando na tabela...")
            
            # Pegar conteúdo da página
            content = await page.content()
            
            # Verificar se termo está na página
            if search_term in content:
                print(f"✅ Termo '{search_term}' ENCONTRADO no HTML!")
            else:
                print(f"❌ Termo '{search_term}' NÃO encontrado no HTML")
                
                # Buscar variações
                variations = [
                    search_term,
                    f"({search_term[:2]}) {search_term[2:7]}-{search_term[7:]}",  # (19) 98961-2020
                    f"{search_term[:2]} {search_term[2:7]}-{search_term[7:]}",   # 19 98961-2020
                ]
                
                for var in variations:
                    if var in content:
                        print(f"✅ Variação encontrada: '{var}'")
                        search_term = var
                        break
            
            # 5. Extrair dados da tabela
            print("")
            print("8️⃣ Extraindo dados da tabela...")
            
            tables = await page.query_selector_all('table')
            print(f"   Encontradas {len(tables)} tabelas")
            
            if len(tables) > 0:
                rows = await tables[0].query_selector_all('tbody tr')
                print(f"   Encontradas {len(rows)} linhas na tabela")
                
                for i, row in enumerate(rows[:5]):  # Primeiras 5 linhas
                    row_text = await row.inner_text()
                    print(f"   Linha {i}: {row_text[:100]}")
                    
                    if search_term.lower() in row_text.lower():
                        print(f"")
                        print(f"✅✅✅ ENCONTRADO NA LINHA {i}!")
                        print(f"")
                        print(f"Dados completos:")
                        print(row_text)
                        
                        # Extrair células
                        cells = await row.query_selector_all('td')
                        print(f"")
                        print(f"Células ({len(cells)}):")
                        for j, cell in enumerate(cells):
                            cell_text = await cell.inner_text()
                            print(f"  [{j}] {cell_text}")
                        
                        break
                else:
                    print(f"❌ Termo não encontrado nas primeiras {len(rows[:5])} linhas")
                    print(f"   Total de linhas: {len(rows)}")
                    
                    if len(rows) > 5:
                        print(f"   ⚠️ Há mais linhas! Pode estar em outra página")
            
            await browser.close()
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_office_search())
