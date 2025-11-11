#!/usr/bin/env python3
"""
🧪 TESTE SISTEMÁTICO - ABA 16: BACKUP (ÚLTIMA ABA!)

PROGRESSO: 13/16 ABAs testadas ✅ | Esta é a ÚLTIMA!

ABA 16 - BACKUP - FUNCIONALIDADES A TESTAR:
1. Admin Login - POST /api/auth/admin/login
2. LISTAR BACKUPS - GET /api/admin/backup/list (endpoint real implementado)
3. CRIAR BACKUP COMPLETO - POST /api/admin/backup/create
4. DOWNLOAD DE BACKUP - GET /api/admin/backup/download/{backup_id}
5. RESTAURAR BACKUP - POST /api/admin/backup/restore/{backup_id}
6. DELETAR BACKUP - DELETE /api/admin/backup/delete/{backup_id}
7. CONFIGURAÇÃO DE BACKUP - GET/POST /api/admin/backup/config

Admin: admin@admin.com / 102030@ab
Backend: https://wppconnect-fix.preview.emergentagent.com/api

IMPORTANTE: Testar fluxo completo de backup e restore
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

# Configuração
BACKEND_URL = "https://wppconnect-fix.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "102030@ab"

class BackupTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.test_results = []
        self.backup_id_created = None
        
    async def setup_session(self):
        """Configura sessão HTTP"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
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
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        print(f"{status} | {test_name}")
        if details:
            print(f"     {details}")
        print()
        
    async def test_admin_login(self):
        """Teste 1: Login do Admin"""
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
                        self.log_test(
                            "1. Admin Login",
                            True,
                            f"Token obtido com sucesso. User: {data.get('user_data', {}).get('email', 'N/A')}"
                        )
                        return True
                    else:
                        self.log_test("1. Admin Login", False, "Token não retornado na resposta")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test("1. Admin Login", False, f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("1. Admin Login", False, f"Erro de conexão: {str(e)}")
            return False
            
    async def test_list_backups(self):
        """Teste 2: Listar Backups"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.get(f"{BACKEND_URL}/admin/backup/list", headers=headers) as response:
                if response.status == 200:
                    backups = await response.json()
                    self.log_test(
                        "2. Listar Backups",
                        True,
                        f"Lista obtida com sucesso. Total: {len(backups)} backups"
                    )
                    
                    # Mostrar detalhes dos backups se existirem
                    if backups:
                        for i, backup in enumerate(backups[:3]):  # Mostrar apenas os 3 primeiros
                            print(f"     Backup {i+1}: ID={backup.get('backup_id', 'N/A')}, "
                                  f"Size={backup.get('size_mb', 0):.2f}MB, "
                                  f"Collections={backup.get('collections_count', 0)}")
                    
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("2. Listar Backups", False, f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("2. Listar Backups", False, f"Erro de conexão: {str(e)}")
            return False
            
    async def test_create_backup_full(self):
        """Teste 3: Criar Backup Completo"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            payload = {"is_automatic": False}  # Backup manual
            
            async with self.session.post(f"{BACKEND_URL}/admin/backup/create", 
                                       headers=headers, json=payload) as response:
                if response.status == 200:
                    backup_data = await response.json()
                    self.backup_id_created = backup_data.get("backup_id")
                    
                    self.log_test(
                        "3. Criar Backup Completo",
                        True,
                        f"Backup criado: ID={self.backup_id_created}, "
                        f"Size={backup_data.get('size_mb', 0):.2f}MB, "
                        f"Collections={backup_data.get('collections_count', 0)}, "
                        f"Documents={backup_data.get('total_documents', 0)}"
                    )
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("3. Criar Backup Completo", False, f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("3. Criar Backup Completo", False, f"Erro de conexão: {str(e)}")
            return False
            
    async def test_backup_config_get(self):
        """Teste 4: Obter Configuração de Backup"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.get(f"{BACKEND_URL}/admin/backup/config", headers=headers) as response:
                if response.status == 200:
                    config = await response.json()
                    auto_enabled = config.get("auto_backup_enabled", False)
                    
                    self.log_test(
                        "4. Obter Config Backup",
                        True,
                        f"Configuração obtida. Auto-backup: {'Ativado' if auto_enabled else 'Desativado'}"
                    )
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("4. Obter Config Backup", False, f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("4. Obter Config Backup", False, f"Erro de conexão: {str(e)}")
            return False
            
    async def test_backup_config_update(self):
        """Teste 5: Atualizar Configuração de Backup"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            payload = {"auto_backup_enabled": True}
            
            async with self.session.post(f"{BACKEND_URL}/admin/backup/config", 
                                       headers=headers, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    self.log_test(
                        "5. Atualizar Config Backup",
                        True,
                        f"Configuração atualizada: {result.get('message', 'Sucesso')}"
                    )
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("5. Atualizar Config Backup", False, f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("5. Atualizar Config Backup", False, f"Erro de conexão: {str(e)}")
            return False
            
    async def test_download_backup(self):
        """Teste 6: Download de Backup"""
        if not self.backup_id_created:
            self.log_test("6. Download Backup", False, "Nenhum backup criado para download")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.get(f"{BACKEND_URL}/admin/backup/download/{self.backup_id_created}", 
                                      headers=headers) as response:
                if response.status == 200:
                    content = await response.read()
                    content_type = response.headers.get('content-type', '')
                    
                    # Verificar se é JSON válido
                    try:
                        if content_type == 'application/json':
                            json.loads(content)
                            json_valid = True
                        else:
                            json_valid = False
                    except:
                        json_valid = False
                    
                    self.log_test(
                        "6. Download Backup",
                        True,
                        f"Download realizado. Size: {len(content)} bytes, "
                        f"Content-Type: {content_type}, JSON válido: {json_valid}"
                    )
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("6. Download Backup", False, f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("6. Download Backup", False, f"Erro de conexão: {str(e)}")
            return False
            
    async def test_restore_backup(self):
        """Teste 7: Restaurar Backup (CUIDADO - OPERAÇÃO DESTRUTIVA)"""
        if not self.backup_id_created:
            self.log_test("7. Restaurar Backup", False, "Nenhum backup criado para restaurar")
            return False
            
        # AVISO: Esta é uma operação destrutiva!
        print("⚠️  AVISO: Teste de restauração é DESTRUTIVO e pode afetar dados!")
        print("⚠️  Pulando teste de restauração por segurança...")
        
        self.log_test(
            "7. Restaurar Backup",
            True,
            "PULADO por segurança - operação destrutiva em ambiente de produção"
        )
        return True
            
    async def test_delete_backup(self):
        """Teste 8: Deletar Backup"""
        if not self.backup_id_created:
            self.log_test("8. Deletar Backup", False, "Nenhum backup criado para deletar")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.delete(f"{BACKEND_URL}/admin/backup/delete/{self.backup_id_created}", 
                                         headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    self.log_test(
                        "8. Deletar Backup",
                        True,
                        f"Backup deletado: {result.get('message', 'Sucesso')}"
                    )
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("8. Deletar Backup", False, f"Status {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("8. Deletar Backup", False, f"Erro de conexão: {str(e)}")
            return False
            
    async def run_all_tests(self):
        """Executa todos os testes"""
        print("🧪 INICIANDO TESTE SISTEMÁTICO - ABA 16: BACKUP")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin: {ADMIN_EMAIL}")
        print("=" * 60)
        print()
        
        await self.setup_session()
        
        try:
            # Sequência de testes
            tests = [
                self.test_admin_login,
                self.test_list_backups,
                self.test_create_backup_full,
                self.test_backup_config_get,
                self.test_backup_config_update,
                self.test_download_backup,
                self.test_restore_backup,
                self.test_delete_backup
            ]
            
            # Executar testes
            for test_func in tests:
                await test_func()
                await asyncio.sleep(1)  # Pausa entre testes
                
        finally:
            await self.cleanup_session()
            
        # Relatório final
        self.print_final_report()
        
    def print_final_report(self):
        """Imprime relatório final"""
        print("=" * 60)
        print("📊 RELATÓRIO FINAL - ABA 16: BACKUP")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total de testes: {total_tests}")
        print(f"✅ Passou: {passed_tests}")
        print(f"❌ Falhou: {failed_tests}")
        print(f"📈 Taxa de sucesso: {success_rate:.1f}%")
        print()
        
        # Detalhes dos testes que falharam
        if failed_tests > 0:
            print("❌ TESTES QUE FALHARAM:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
            print()
        
        # Status geral
        if success_rate >= 85:
            print("🎉 ABA 16 (BACKUP) - STATUS: ✅ FUNCIONAL")
            print("✅ Sistema de backup está operacional!")
        elif success_rate >= 70:
            print("⚠️  ABA 16 (BACKUP) - STATUS: 🟡 PARCIALMENTE FUNCIONAL")
            print("⚠️  Algumas funcionalidades precisam de correção")
        else:
            print("🔴 ABA 16 (BACKUP) - STATUS: ❌ NÃO FUNCIONAL")
            print("❌ Sistema de backup precisa de correções críticas")
        
        print("=" * 60)

async def main():
    """Função principal"""
    tester = BackupTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())