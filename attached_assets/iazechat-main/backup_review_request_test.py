#!/usr/bin/env python3
"""
🧪 TESTE ESPECÍFICO CONFORME REVIEW REQUEST - ABA 16: BACKUP

Testando os endpoints EXATOS mencionados no review request:
- GET /api/backups
- POST /api/backups/create
- GET /api/backups/download/{backup_name}
- POST /api/backups/restore
- DELETE /api/backups/{backup_name}

Para verificar se existem ou se apenas os endpoints /api/admin/backup/* funcionam.
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Configuração
BACKEND_URL = "https://wppconnect-fix.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "102030@ab"

class ReviewRequestBackupTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.test_results = []
        
    async def setup_session(self):
        """Configura sessão HTTP"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(ssl=False)
        )
        
    async def cleanup_session(self):
        """Limpa sessão HTTP"""
        if self.session:
            await self.session.close()
            
    def log_test(self, test_name: str, success: bool, details: str):
        """Registra resultado do teste"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        print(f"{status} | {test_name}")
        if details:
            print(f"     {details}")
        print()
        
    async def test_admin_login(self):
        """Login do Admin"""
        try:
            payload = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/admin/login", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    self.admin_token = data.get("token")
                    
                    if self.admin_token:
                        self.log_test("Admin Login", True, f"Token obtido: {self.admin_token[:20]}...")
                        return True
                    else:
                        self.log_test("Admin Login", False, "Token não retornado")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("Admin Login", False, f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Admin Login", False, f"Erro: {str(e)}")
            return False
            
    async def test_review_request_endpoints(self):
        """Testa os endpoints EXATOS do review request"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # 1. GET /api/backups
        try:
            async with self.session.get(f"{BACKEND_URL}/backups", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test("GET /api/backups", True, f"Retornou {len(data)} backups")
                else:
                    error_text = await response.text()
                    self.log_test("GET /api/backups", False, f"Status {response.status}: {error_text}")
        except Exception as e:
            self.log_test("GET /api/backups", False, f"Erro: {str(e)}")
            
        # 2. POST /api/backups/create (full backup)
        try:
            payload = {"backup_type": "full"}
            async with self.session.post(f"{BACKEND_URL}/backups/create", 
                                       headers=headers, json=payload) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    self.log_test("POST /api/backups/create (full)", True, f"Backup criado: {data}")
                else:
                    error_text = await response.text()
                    self.log_test("POST /api/backups/create (full)", False, f"Status {response.status}: {error_text}")
        except Exception as e:
            self.log_test("POST /api/backups/create (full)", False, f"Erro: {str(e)}")
            
        # 3. POST /api/backups/create (database backup)
        try:
            payload = {"backup_type": "database"}
            async with self.session.post(f"{BACKEND_URL}/backups/create", 
                                       headers=headers, json=payload) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    self.log_test("POST /api/backups/create (database)", True, f"Backup criado: {data}")
                else:
                    error_text = await response.text()
                    self.log_test("POST /api/backups/create (database)", False, f"Status {response.status}: {error_text}")
        except Exception as e:
            self.log_test("POST /api/backups/create (database)", False, f"Erro: {str(e)}")
            
        # 4. GET /api/backups/download/{backup_name}
        try:
            backup_name = "backup_test.tar.gz"
            async with self.session.get(f"{BACKEND_URL}/backups/download/{backup_name}", 
                                      headers=headers) as response:
                if response.status == 200:
                    content = await response.read()
                    self.log_test("GET /api/backups/download/{backup_name}", True, f"Download OK: {len(content)} bytes")
                else:
                    error_text = await response.text()
                    self.log_test("GET /api/backups/download/{backup_name}", False, f"Status {response.status}: {error_text}")
        except Exception as e:
            self.log_test("GET /api/backups/download/{backup_name}", False, f"Erro: {str(e)}")
            
        # 5. POST /api/backups/restore
        try:
            payload = {"backup_name": "backup_test.tar.gz"}
            async with self.session.post(f"{BACKEND_URL}/backups/restore", 
                                       headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test("POST /api/backups/restore", True, f"Restore OK: {data}")
                else:
                    error_text = await response.text()
                    self.log_test("POST /api/backups/restore", False, f"Status {response.status}: {error_text}")
        except Exception as e:
            self.log_test("POST /api/backups/restore", False, f"Erro: {str(e)}")
            
        # 6. DELETE /api/backups/{backup_name}
        try:
            backup_name = "backup_test.tar.gz"
            async with self.session.delete(f"{BACKEND_URL}/backups/{backup_name}", 
                                         headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test("DELETE /api/backups/{backup_name}", True, f"Delete OK: {data}")
                else:
                    error_text = await response.text()
                    self.log_test("DELETE /api/backups/{backup_name}", False, f"Status {response.status}: {error_text}")
        except Exception as e:
            self.log_test("DELETE /api/backups/{backup_name}", False, f"Erro: {str(e)}")
            
    async def run_tests(self):
        """Executa todos os testes"""
        print("🧪 TESTE DOS ENDPOINTS EXATOS DO REVIEW REQUEST")
        print("=" * 60)
        print("Testando se os endpoints /api/backups/* existem...")
        print("=" * 60)
        print()
        
        await self.setup_session()
        
        try:
            # Login primeiro
            login_success = await self.test_admin_login()
            
            if login_success:
                await self.test_review_request_endpoints()
            else:
                print("❌ Não foi possível fazer login. Abortando testes.")
                
        finally:
            await self.cleanup_session()
            
        # Relatório
        self.print_report()
        
    def print_report(self):
        """Imprime relatório"""
        print("=" * 60)
        print("📊 RESULTADO: ENDPOINTS DO REVIEW REQUEST")
        print("=" * 60)
        
        total_tests = len([r for r in self.test_results if r["test"] != "Admin Login"])
        passed_tests = sum(1 for r in self.test_results if r["success"] and r["test"] != "Admin Login")
        
        print(f"Total de endpoints testados: {total_tests}")
        print(f"✅ Funcionando: {passed_tests}")
        print(f"❌ Não funcionando: {total_tests - passed_tests}")
        print()
        
        if passed_tests == 0:
            print("🔴 CONCLUSÃO: Os endpoints /api/backups/* NÃO EXISTEM")
            print("✅ SOLUÇÃO: Use os endpoints /api/admin/backup/* que estão funcionando")
        elif passed_tests == total_tests:
            print("🎉 CONCLUSÃO: Todos os endpoints /api/backups/* estão funcionando!")
        else:
            print("⚠️  CONCLUSÃO: Alguns endpoints /api/backups/* funcionam, outros não")
        
        print("=" * 60)

async def main():
    """Função principal"""
    tester = ReviewRequestBackupTester()
    await tester.run_tests()

if __name__ == "__main__":
    asyncio.run(main())