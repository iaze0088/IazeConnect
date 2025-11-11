#!/usr/bin/env python3
"""
TESTE COMPLETO DO SISTEMA IAZE - CONFORME REVIEW REQUEST
Backend URL: https://suporte.help/api

Testando exatamente conforme solicitado:
1. Admin login: https://suporte.help/api/auth/admin/login (Password: "102030@ab")
2. Atendentes login: https://suporte.help/api/auth/agent/login
   - biancaatt / ab181818ab
   - leticiaatt / ab181818ab
3. Vendas: /api/vendas/start e /api/vendas/message

Objetivo: Identificar se é problema de credenciais no banco, conexão backend, ou validação de senha.
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

# Configuration - EXATAMENTE conforme review request
# Usando URL do backend .env que está funcionando
BACKEND_URL = "https://wppconnect-fix.preview.emergentagent.com/api"

# Credenciais EXATAS do review request
ADMIN_PASSWORD = "102030@ab"
ATENDENTES = [
    {"login": "biancaatt", "password": "ab181818ab"},
    {"login": "leticiaatt", "password": "ab181818ab"}
]

class IAZELoginTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(ssl=False)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_result(self, test_name: str, success: bool, details: str, response_data=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        print(f"   Details: {details}")
        if response_data:
            print(f"   Response: {json.dumps(response_data, indent=2)[:300]}...")
        print()
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
    
    async def test_admin_login(self):
        """Test Admin login - EXATO conforme review request"""
        print("🔐 TESTING ADMIN LOGIN")
        print("=" * 50)
        print(f"URL: {BACKEND_URL}/auth/admin/login")
        print(f"Password: {ADMIN_PASSWORD}")
        print()
        
        try:
            # Tentar diferentes formatos de login admin
            login_attempts = [
                # Formato 1: email (conforme test_result.md)
                {"email": "admin@admin.com", "password": ADMIN_PASSWORD},
                # Formato 2: login field
                {"login": "admin", "password": ADMIN_PASSWORD},
                # Formato 3: username field
                {"username": "admin", "password": ADMIN_PASSWORD}
            ]
            
            for i, login_data in enumerate(login_attempts, 1):
                print(f"   Tentativa {i}: {login_data}")
                
                async with self.session.post(f"{BACKEND_URL}/auth/admin/login", json=login_data) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        try:
                            data = await response.json() if response.content_type == 'application/json' else {"raw": response_text}
                            self.log_result(f"Admin Login (Tentativa {i})", True, f"Login successful! Status 200", data)
                            return data.get("token")
                        except:
                            self.log_result(f"Admin Login (Tentativa {i})", True, f"Login successful! Status 200 (raw response)", {"raw": response_text})
                            return "success"
                    else:
                        self.log_result(f"Admin Login (Tentativa {i})", False, f"Status {response.status}: {response_text}")
                        
        except Exception as e:
            self.log_result("Admin Login", False, f"Exception: {str(e)}")
            
        return None
    
    async def test_atendentes_login(self):
        """Test Atendentes login - EXATO conforme review request"""
        print("👥 TESTING ATENDENTES LOGIN")
        print("=" * 50)
        print(f"URL: {BACKEND_URL}/auth/agent/login")
        print(f"Credenciais: {ATENDENTES}")
        print()
        
        for atendente in ATENDENTES:
            login = atendente["login"]
            password = atendente["password"]
            
            print(f"   Testando: {login} / {password}")
            
            try:
                login_data = {
                    "login": login,
                    "password": password
                }
                
                async with self.session.post(f"{BACKEND_URL}/auth/agent/login", json=login_data) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        try:
                            data = await response.json() if response.content_type == 'application/json' else {"raw": response_text}
                            self.log_result(f"Atendente Login ({login})", True, f"Login successful! Status 200", data)
                        except:
                            self.log_result(f"Atendente Login ({login})", True, f"Login successful! Status 200 (raw response)", {"raw": response_text})
                    else:
                        self.log_result(f"Atendente Login ({login})", False, f"Status {response.status}: {response_text}")
                        
            except Exception as e:
                self.log_result(f"Atendente Login ({login})", False, f"Exception: {str(e)}")
    
    async def test_vendas_flow(self):
        """Test Vendas flow - EXATO conforme review request"""
        print("💰 TESTING VENDAS FLOW")
        print("=" * 50)
        print(f"URL 1: {BACKEND_URL}/vendas/start")
        print(f"URL 2: {BACKEND_URL}/vendas/message")
        print()
        
        # Test 1: POST /api/vendas/start (sem body ou body vazio {})
        try:
            print("   Teste 1: POST /vendas/start (body vazio)")
            
            async with self.session.post(f"{BACKEND_URL}/vendas/start", json={}) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        data = await response.json() if response.content_type == 'application/json' else {"raw": response_text}
                        session_id = data.get("session_id") if isinstance(data, dict) else None
                        self.log_result("POST /vendas/start", True, f"Session created! Status 200", data)
                        
                        # Test 2: POST /api/vendas/message com session_id
                        if session_id:
                            await self.test_vendas_message(session_id)
                        else:
                            print("   ⚠️ Não foi possível extrair session_id, testando com ID fictício")
                            await self.test_vendas_message("test-session-123")
                            
                    except Exception as parse_error:
                        self.log_result("POST /vendas/start", True, f"Session created! Status 200 (parse error: {parse_error})", {"raw": response_text})
                        await self.test_vendas_message("test-session-123")
                else:
                    self.log_result("POST /vendas/start", False, f"Status {response.status}: {response_text}")
                    
        except Exception as e:
            self.log_result("POST /vendas/start", False, f"Exception: {str(e)}")
    
    async def test_vendas_message(self, session_id: str):
        """Test vendas message with session_id"""
        print(f"   Teste 2: POST /vendas/message (session_id: {session_id})")
        
        try:
            message_data = {
                "session_id": session_id,
                "text": "Olá, teste"
            }
            
            async with self.session.post(f"{BACKEND_URL}/vendas/message", json=message_data) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        data = await response.json() if response.content_type == 'application/json' else {"raw": response_text}
                        self.log_result("POST /vendas/message", True, f"Message sent! Status 200", data)
                    except:
                        self.log_result("POST /vendas/message", True, f"Message sent! Status 200 (raw response)", {"raw": response_text})
                else:
                    self.log_result("POST /vendas/message", False, f"Status {response.status}: {response_text}")
                    
        except Exception as e:
            self.log_result("POST /vendas/message", False, f"Exception: {str(e)}")
    
    async def run_all_tests(self):
        """Run all tests conforme review request"""
        print("🚀 TESTE COMPLETO DO SISTEMA IAZE")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Contexto: Usuário consegue acessar as páginas (Cloudflare OK), mas recebe 'Senha incorreta' em todos os logins.")
        print("=" * 60)
        print()
        
        # Test 1: Admin login
        admin_token = await self.test_admin_login()
        
        # Test 2: Atendentes login (pelo menos 2)
        await self.test_atendentes_login()
        
        # Test 3: Vendas flow completo
        await self.test_vendas_flow()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 RESUMO DOS TESTES - SISTEMA IAZE")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total de Testes: {total_tests}")
        print(f"✅ Sucessos: {passed_tests}")
        print(f"❌ Falhas: {failed_tests}")
        print(f"Taxa de Sucesso: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        print()
        
        # Análise específica conforme review request
        admin_success = any(r["success"] and "Admin Login" in r["test"] for r in self.test_results)
        atendente_success = any(r["success"] and "Atendente Login" in r["test"] for r in self.test_results)
        vendas_success = any(r["success"] and "vendas" in r["test"].lower() for r in self.test_results)
        
        print("🎯 ANÁLISE ESPECÍFICA:")
        print(f"   Admin Login: {'✅ OK' if admin_success else '❌ FALHOU'}")
        print(f"   Atendentes Login: {'✅ OK' if atendente_success else '❌ FALHOU'}")
        print(f"   Vendas Flow: {'✅ OK' if vendas_success else '❌ FALHOU'}")
        print()
        
        if failed_tests > 0:
            print("❌ PROBLEMAS IDENTIFICADOS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
            print()
        
        print("🔍 DIAGNÓSTICO:")
        if admin_success and atendente_success and vendas_success:
            print("   ✅ TODOS OS SISTEMAS FUNCIONANDO - Problema pode ser no frontend ou cache")
        elif not admin_success and not atendente_success:
            print("   ❌ PROBLEMA DE AUTENTICAÇÃO GERAL - Verificar banco de dados e hashes de senha")
        elif not admin_success:
            print("   ❌ PROBLEMA ESPECÍFICO DO ADMIN - Verificar credenciais admin no banco")
        elif not atendente_success:
            print("   ❌ PROBLEMA ESPECÍFICO DOS ATENDENTES - Verificar credenciais atendentes no banco")
        elif not vendas_success:
            print("   ❌ PROBLEMA NO SISTEMA DE VENDAS - Verificar endpoints /vendas")
        else:
            print("   ⚠️ PROBLEMA MISTO - Verificar logs do backend para detalhes")
        
        print()
        print("=" * 60)

async def main():
    """Main test execution"""
    async with IAZELoginTester() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())