#!/usr/bin/env python3
"""
🧪 TESTE SISTEMÁTICO - ABA 2: DOMÍNIO

CONTEXTO:
- ABA 1 (Dashboard - Avisos) está 100% funcional ✅
- Continuando teste sistemático das 16 ABAs
- Admin: admin@admin.com / senha: 102030@ab
- Backend: https://wppconnect-fix.preview.emergentagent.com/api

ABA 2 - DOMÍNIO - FUNCIONALIDADES A TESTAR:

ADMIN DOMAIN CONFIG:
1. LOGIN ADMIN
   - POST /api/auth/admin/login
   - Body: {"password": "102030@ab"}

2. GET ADMIN DOMAIN CONFIG
   - GET /api/admin/domain-config
   - Header: Authorization: Bearer {admin_token}

3. SAVE ADMIN DOMAIN CONFIG
   - POST /api/admin/domain-config
   - Header: Authorization: Bearer {admin_token}
   - Body: {"mainDomain": "test.com", "resellerPath": "/login"}

RESELLER DOMAIN MANAGEMENT:
4. LOGIN RESELLER
   - POST /api/auth/reseller/login (try common passwords)

5. OBTER INFORMAÇÕES DE DOMÍNIO
   - GET /api/reseller/domain-info
   - Header: Authorization: Bearer {reseller_token}
   - Deve retornar: test_domain, server_ip, custom_domain, ssl_status

6. ATUALIZAR DOMÍNIO CUSTOMIZADO
   - POST /api/reseller/update-domain
   - Header: Authorization: Bearer {reseller_token}
   - Body: {"custom_domain": "teste.example.com"}

7. VERIFICAR CONFIGURAÇÃO DNS
   - GET /api/reseller/verify-domain?domain=teste.example.com
   - Header: Authorization: Bearer {reseller_token}

CRITÉRIOS DE SUCESSO:
✅ Todas as funcionalidades devem funcionar sem erro
✅ Admin pode configurar domínios globais
✅ Reseller pode gerenciar seu próprio domínio
✅ Domain info retorna dados corretos
✅ Update domain funciona e persiste
✅ DNS verification funciona
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Configuração
BACKEND_URL = "https://wppconnect-fix.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "102030@ab"

class DomainTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.reseller_token = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_result(self, test_name: str, success: bool, details: str, response_data=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        print(f"   {details}")
        if response_data:
            print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
        print()
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
    
    async def test_admin_login(self):
        """1. LOGIN ADMIN"""
        print("🔑 TESTE 1: LOGIN ADMIN")
        print("=" * 50)
        
        try:
            async with self.session.post(
                f"{BACKEND_URL}/auth/admin/login",
                json={"password": ADMIN_PASSWORD},
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    self.admin_token = data.get("token")
                    
                    if self.admin_token:
                        self.log_result(
                            "Admin Login",
                            True,
                            f"Login successful with admin@admin.com / {ADMIN_PASSWORD}",
                            {"token_preview": self.admin_token[:50] + "...", "user_type": data.get("user_type")}
                        )
                        return True
                    else:
                        self.log_result("Admin Login", False, "Token not returned in response", data)
                        return False
                else:
                    error_data = await response.text()
                    self.log_result("Admin Login", False, f"HTTP {response.status}: {error_data}")
                    return False
                    
        except Exception as e:
            self.log_result("Admin Login", False, f"Exception: {str(e)}")
            return False
    
    async def test_admin_domain_config_get(self):
        """2. GET ADMIN DOMAIN CONFIG"""
        print("📋 TESTE 2: GET ADMIN DOMAIN CONFIG")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_result("Admin Domain Config Get", False, "No admin token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.get(
                f"{BACKEND_URL}/admin/domain-config",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    if "config" in data:
                        self.log_result(
                            "Admin Domain Config Get",
                            True,
                            "Admin domain config retrieved successfully",
                            data
                        )
                        return True
                    else:
                        self.log_result(
                            "Admin Domain Config Get", 
                            False, 
                            "Response missing 'config' field",
                            data
                        )
                        return False
                else:
                    error_data = await response.text()
                    self.log_result("Admin Domain Config Get", False, f"HTTP {response.status}: {error_data}")
                    return False
                    
        except Exception as e:
            self.log_result("Admin Domain Config Get", False, f"Exception: {str(e)}")
            return False
    
    async def test_admin_domain_config_save(self):
        """3. SAVE ADMIN DOMAIN CONFIG"""
        print("💾 TESTE 3: SAVE ADMIN DOMAIN CONFIG")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_result("Admin Domain Config Save", False, "No admin token available")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            }
            
            test_config = {
                "mainDomain": "teste.iaze.com",
                "resellerPath": "/admin",
                "agentPath": "/atendente",
                "clientPath": "/"
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/admin/domain-config",
                json=test_config,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("ok") and "message" in data:
                        self.log_result(
                            "Admin Domain Config Save",
                            True,
                            "Admin domain config saved successfully",
                            data
                        )
                        return True
                    else:
                        self.log_result(
                            "Admin Domain Config Save",
                            False,
                            "Response missing 'ok' or 'message' fields",
                            data
                        )
                        return False
                else:
                    error_data = await response.text()
                    self.log_result("Admin Domain Config Save", False, f"HTTP {response.status}: {error_data}")
                    return False
                    
        except Exception as e:
            self.log_result("Admin Domain Config Save", False, f"Exception: {str(e)}")
            return False
    
    async def test_reseller_login(self):
        """4. LOGIN RESELLER"""
        print("🔑 TESTE 4: LOGIN RESELLER")
        print("=" * 50)
        
        # Try common reseller credentials
        test_credentials = [
            {"email": "michaelrv@gmail.com", "password": "ab181818ab"},
            {"email": "michaelrv@gmail.com", "password": "123456"},
            {"email": "michaelrv@gmail.com", "password": "102030@ab"},
            {"email": "teste.ativa@example.com", "password": "teste123"},
            {"email": "fabio@gmail.com", "password": "ab181818ab"},
        ]
        
        for cred in test_credentials:
            try:
                async with self.session.post(
                    f"{BACKEND_URL}/resellers/login",
                    json=cred,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        self.reseller_token = data.get("token")
                        
                        if self.reseller_token:
                            self.log_result(
                                "Reseller Login",
                                True,
                                f"Login successful with {cred['email']} / {cred['password']}",
                                {"token_preview": self.reseller_token[:50] + "...", "user_type": data.get("user_type")}
                            )
                            return True
                        
            except Exception as e:
                continue
        
        self.log_result("Reseller Login", False, "Could not login with any test credentials")
        return False
    
    async def test_reseller_domain_info(self):
        """5. OBTER INFORMAÇÕES DE DOMÍNIO (RESELLER)"""
        print("📋 TESTE 5: OBTER INFORMAÇÕES DE DOMÍNIO (RESELLER)")
        print("=" * 50)
        
        if not self.reseller_token:
            self.log_result("Reseller Domain Info", False, "No reseller token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.reseller_token}"}
            
            async with self.session.get(
                f"{BACKEND_URL}/reseller/domain-info",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Verificar campos obrigatórios
                    required_fields = ["test_domain", "server_ip", "custom_domain", "ssl_enabled"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields:
                        self.log_result(
                            "Reseller Domain Info",
                            True,
                            f"All required fields present: {', '.join(required_fields)}",
                            data
                        )
                        return True
                    else:
                        self.log_result(
                            "Reseller Domain Info", 
                            False, 
                            f"Missing required fields: {missing_fields}",
                            data
                        )
                        return False
                else:
                    error_data = await response.text()
                    self.log_result("Reseller Domain Info", False, f"HTTP {response.status}: {error_data}")
                    return False
                    
        except Exception as e:
            self.log_result("Reseller Domain Info", False, f"Exception: {str(e)}")
            return False
    
    async def test_reseller_update_domain(self):
        """6. ATUALIZAR DOMÍNIO CUSTOMIZADO (RESELLER)"""
        print("🔄 TESTE 6: ATUALIZAR DOMÍNIO CUSTOMIZADO (RESELLER)")
        print("=" * 50)
        
        if not self.reseller_token:
            self.log_result("Reseller Update Domain", False, "No reseller token available")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.reseller_token}",
                "Content-Type": "application/json"
            }
            
            test_domain = "teste.example.com"
            
            async with self.session.post(
                f"{BACKEND_URL}/reseller/update-domain",
                json={"custom_domain": test_domain},
                headers=headers
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("ok") and "message" in data:
                        self.log_result(
                            "Reseller Update Domain",
                            True,
                            f"Domain updated successfully to {test_domain}",
                            data
                        )
                        return True
                    else:
                        self.log_result(
                            "Reseller Update Domain",
                            False,
                            "Response missing 'ok' or 'message' fields",
                            data
                        )
                        return False
                else:
                    error_data = await response.text()
                    self.log_result("Reseller Update Domain", False, f"HTTP {response.status}: {error_data}")
                    return False
                    
        except Exception as e:
            self.log_result("Reseller Update Domain", False, f"Exception: {str(e)}")
            return False
    
    async def test_reseller_verify_domain(self):
        """7. VERIFICAR CONFIGURAÇÃO DNS (RESELLER)"""
        print("🔍 TESTE 7: VERIFICAR CONFIGURAÇÃO DNS (RESELLER)")
        print("=" * 50)
        
        if not self.reseller_token:
            self.log_result("Reseller Verify Domain", False, "No reseller token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.reseller_token}"}
            test_domain = "teste.example.com"
            
            async with self.session.get(
                f"{BACKEND_URL}/reseller/verify-domain?domain={test_domain}",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Verificar se retorna informações de DNS
                    if "dns_configured" in data or "ip_address" in data or "message" in data:
                        self.log_result(
                            "Reseller Verify Domain",
                            True,
                            f"DNS verification completed for {test_domain}",
                            data
                        )
                        return True
                    else:
                        self.log_result(
                            "Reseller Verify Domain",
                            False,
                            "Response missing DNS verification fields",
                            data
                        )
                        return False
                else:
                    error_data = await response.text()
                    self.log_result("Reseller Verify Domain", False, f"HTTP {response.status}: {error_data}")
                    return False
                    
        except Exception as e:
            self.log_result("Reseller Verify Domain", False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Execute all domain tests"""
        print("🧪 INICIANDO TESTE SISTEMÁTICO - ABA 2: DOMÍNIO")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin Credentials: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("=" * 60)
        print()
        
        # Execute tests in sequence
        tests = [
            self.test_admin_login,
            self.test_admin_domain_config_get,
            self.test_admin_domain_config_save,
            self.test_reseller_login,
            self.test_reseller_domain_info,
            self.test_reseller_update_domain,
            self.test_reseller_verify_domain
        ]
        
        passed = 0
        total = len(tests)
        
        for test_func in tests:
            success = await test_func()
            if success:
                passed += 1
        
        # Final summary
        print("📊 RESUMO FINAL - ABA 2: DOMÍNIO")
        print("=" * 50)
        print(f"✅ Testes Passaram: {passed}/{total}")
        print(f"❌ Testes Falharam: {total - passed}/{total}")
        print(f"📈 Taxa de Sucesso: {(passed/total)*100:.1f}%")
        print()
        
        if passed == total:
            print("🎉 TODOS OS TESTES PASSARAM!")
            print("✅ ABA 2 (DOMÍNIO) está 100% funcional")
            print("✅ Pode avançar para ABA 3 (REVENDAS)")
        else:
            print("⚠️ ALGUNS TESTES FALHARAM!")
            print("❌ ABA 2 (DOMÍNIO) precisa de correções")
            print("🔧 Verificar logs acima para detalhes dos erros")
        
        print()
        print("📋 DETALHES DOS TESTES:")
        for i, result in enumerate(self.test_results, 1):
            status = "✅" if result["success"] else "❌"
            print(f"{i}. {status} {result['test']}: {result['details']}")
        
        return passed == total

async def main():
    """Main test execution"""
    async with DomainTester() as tester:
        success = await tester.run_all_tests()
        return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Teste interrompido pelo usuário")
        exit(1)
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        exit(1)