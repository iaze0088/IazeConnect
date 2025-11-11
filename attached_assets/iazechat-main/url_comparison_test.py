#!/usr/bin/env python3
"""
TESTE DE COMPARAÇÃO DE URLs - DIAGNÓSTICO DO PROBLEMA
Testando ambas as URLs para identificar o problema exato:
1. https://suporte.help/api (HTTPS - não funciona)
2. http://suporte.help/api (HTTP - funciona)
3. https://wppconnect-fix.preview.emergentagent.com/api (HTTPS - funciona)
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

# URLs para testar
URLS_TO_TEST = [
    {"name": "suporte.help HTTPS", "url": "https://suporte.help/api", "expected": "FAIL - Connection refused"},
    {"name": "suporte.help HTTP", "url": "http://suporte.help/api", "expected": "SUCCESS - Should work"},
    {"name": "juliana-chat HTTPS", "url": "https://wppconnect-fix.preview.emergentagent.com/api", "expected": "SUCCESS - Should work"}
]

# Credenciais para teste
ADMIN_CREDS = {"email": "admin@admin.com", "password": "102030@ab"}
ATENDENTE_CREDS = {"login": "biancaatt", "password": "ab181818ab"}

class URLComparisonTester:
    def __init__(self):
        self.session = None
        self.results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            connector=aiohttp.TCPConnector(ssl=False)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_url(self, url_info):
        """Test a specific URL"""
        name = url_info["name"]
        base_url = url_info["url"]
        expected = url_info["expected"]
        
        print(f"\n🔍 TESTING: {name}")
        print(f"URL: {base_url}")
        print(f"Expected: {expected}")
        print("-" * 50)
        
        # Test 1: Admin Login
        await self.test_admin_login(name, base_url)
        
        # Test 2: Agent Login
        await self.test_agent_login(name, base_url)
        
        # Test 3: Vendas Start
        await self.test_vendas_start(name, base_url)
    
    async def test_admin_login(self, name, base_url):
        """Test admin login for a specific URL"""
        try:
            async with self.session.post(f"{base_url}/auth/admin/login", json=ADMIN_CREDS) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Admin Login: SUCCESS (200)")
                    self.results.append({"url": name, "test": "Admin Login", "status": "SUCCESS", "details": "Login successful"})
                else:
                    error_text = await response.text()
                    print(f"   ❌ Admin Login: FAIL ({response.status}) - {error_text[:100]}")
                    self.results.append({"url": name, "test": "Admin Login", "status": "FAIL", "details": f"Status {response.status}"})
        except Exception as e:
            print(f"   ❌ Admin Login: FAIL - {str(e)}")
            self.results.append({"url": name, "test": "Admin Login", "status": "FAIL", "details": str(e)})
    
    async def test_agent_login(self, name, base_url):
        """Test agent login for a specific URL"""
        try:
            async with self.session.post(f"{base_url}/auth/agent/login", json=ATENDENTE_CREDS) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Agent Login: SUCCESS (200)")
                    self.results.append({"url": name, "test": "Agent Login", "status": "SUCCESS", "details": "Login successful"})
                else:
                    error_text = await response.text()
                    print(f"   ❌ Agent Login: FAIL ({response.status}) - {error_text[:100]}")
                    self.results.append({"url": name, "test": "Agent Login", "status": "FAIL", "details": f"Status {response.status}"})
        except Exception as e:
            print(f"   ❌ Agent Login: FAIL - {str(e)}")
            self.results.append({"url": name, "test": "Agent Login", "status": "FAIL", "details": str(e)})
    
    async def test_vendas_start(self, name, base_url):
        """Test vendas start for a specific URL"""
        try:
            async with self.session.post(f"{base_url}/vendas/start", json={}) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Vendas Start: SUCCESS (200)")
                    self.results.append({"url": name, "test": "Vendas Start", "status": "SUCCESS", "details": "Session created"})
                else:
                    error_text = await response.text()
                    print(f"   ❌ Vendas Start: FAIL ({response.status}) - {error_text[:100]}")
                    self.results.append({"url": name, "test": "Vendas Start", "status": "FAIL", "details": f"Status {response.status}"})
        except Exception as e:
            print(f"   ❌ Vendas Start: FAIL - {str(e)}")
            self.results.append({"url": name, "test": "Vendas Start", "status": "FAIL", "details": str(e)})
    
    async def run_all_tests(self):
        """Run tests for all URLs"""
        print("🚀 TESTE DE COMPARAÇÃO DE URLs - DIAGNÓSTICO COMPLETO")
        print("=" * 70)
        print("Objetivo: Identificar por que usuário recebe 'Senha incorreta'")
        print("=" * 70)
        
        for url_info in URLS_TO_TEST:
            await self.test_url(url_info)
        
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive summary"""
        print("\n" + "=" * 70)
        print("📊 RESUMO COMPLETO - DIAGNÓSTICO DO PROBLEMA")
        print("=" * 70)
        
        # Group results by URL
        url_results = {}
        for result in self.results:
            url = result["url"]
            if url not in url_results:
                url_results[url] = []
            url_results[url].append(result)
        
        # Print results for each URL
        for url, results in url_results.items():
            success_count = sum(1 for r in results if r["status"] == "SUCCESS")
            total_count = len(results)
            
            print(f"\n🌐 {url}:")
            print(f"   Sucessos: {success_count}/{total_count}")
            
            for result in results:
                status_icon = "✅" if result["status"] == "SUCCESS" else "❌"
                print(f"   {status_icon} {result['test']}: {result['details']}")
        
        # Final diagnosis
        print(f"\n🔍 DIAGNÓSTICO FINAL:")
        
        suporte_https_working = any(r["status"] == "SUCCESS" and r["url"] == "suporte.help HTTPS" for r in self.results)
        suporte_http_working = any(r["status"] == "SUCCESS" and r["url"] == "suporte.help HTTP" for r in self.results)
        juliana_working = any(r["status"] == "SUCCESS" and r["url"] == "juliana-chat HTTPS" for r in self.results)
        
        if not suporte_https_working and suporte_http_working and juliana_working:
            print("   🎯 PROBLEMA IDENTIFICADO: HTTPS não configurado para suporte.help")
            print("   📋 CAUSA: Usuário tenta acessar https://suporte.help mas só http://suporte.help funciona")
            print("   🔧 SOLUÇÃO: Configurar SSL/HTTPS para suporte.help OU orientar usuário usar HTTP")
        elif suporte_https_working and suporte_http_working and juliana_working:
            print("   ✅ TODOS OS ENDPOINTS FUNCIONANDO - Problema pode ser cache do navegador")
        elif not suporte_https_working and not suporte_http_working:
            print("   ❌ PROBLEMA NO DOMÍNIO suporte.help - Verificar DNS e servidor")
        else:
            print("   ⚠️ PROBLEMA MISTO - Verificar configuração específica")
        
        print(f"\n💡 RECOMENDAÇÕES:")
        if not suporte_https_working and suporte_http_working:
            print("   1. Configurar certificado SSL para suporte.help")
            print("   2. OU atualizar frontend para usar http://suporte.help")
            print("   3. OU redirecionar suporte.help para juliana-chat.preview.emergentagent.com")
        
        print("   4. Verificar se usuário está acessando a URL correta")
        print("   5. Limpar cache do navegador se necessário")
        
        print("\n" + "=" * 70)

async def main():
    """Main test execution"""
    async with URLComparisonTester() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())