#!/usr/bin/env python3
"""
TESTE COMPLETO: WhatsApp WPPConnect Integration
Migração completa de Evolution API para WPPConnect realizada.
Testando fluxo completo via API do IAZE.

Backend URL: https://suporte.help/api
Credenciais Admin: admin@admin.com / 102030@ab
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

# Configurações
BACKEND_URL = "https://suporte.help/api"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "102030@ab"

class WPPConnectTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.connection_id = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60)  # 60s timeout
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, success: bool, details: str, response_data=None):
        """Log test result"""
        status = "✅" if success else "❌"
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": timestamp,
            "response_data": response_data
        }
        
        self.test_results.append(result)
        print(f"{status} [{timestamp}] {test_name}")
        print(f"   {details}")
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
        print()
    
    async def test_admin_login(self):
        """1. Admin Login"""
        try:
            url = f"{BACKEND_URL}/auth/admin/login"
            payload = {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
            
            async with self.session.post(url, json=payload) as response:
                data = await response.json()
                
                if response.status == 200 and "token" in data:
                    self.admin_token = data["token"]
                    self.log_test(
                        "Admin Login",
                        True,
                        f"Status: {response.status}, Token obtido com sucesso"
                    )
                    return True
                else:
                    self.log_test(
                        "Admin Login", 
                        False,
                        f"Status: {response.status}, Erro no login",
                        data
                    )
                    return False
                    
        except Exception as e:
            self.log_test("Admin Login", False, f"Exceção: {str(e)}")
            return False
    
    async def test_create_connection(self):
        """2. Criar Nova Conexão WhatsApp"""
        if not self.admin_token:
            self.log_test("Create Connection", False, "Token admin não disponível")
            return False
            
        try:
            url = f"{BACKEND_URL}/whatsapp/connections"
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            payload = {"name": "Teste Automated"}
            
            # Timeout estendido para criação de conexão (pode demorar até 30s)
            timeout = aiohttp.ClientTimeout(total=35)
            
            async with self.session.post(url, json=payload, headers=headers, timeout=timeout) as response:
                data = await response.json()
                
                if response.status in [200, 201]:
                    # Check if response has nested structure
                    connection_data = data.get("connection", data)
                    
                    # Verificar campos obrigatórios
                    required_fields = ["id", "instance_name", "status"]
                    missing_fields = [field for field in required_fields if field not in connection_data]
                    
                    if missing_fields:
                        self.log_test(
                            "Create Connection",
                            False,
                            f"Status: {response.status}, Campos obrigatórios ausentes: {missing_fields}",
                            data
                        )
                        return False
                    
                    self.connection_id = connection_data.get("id")
                    qr_code = connection_data.get("qr_code")
                    status = connection_data.get("status")
                    
                    # Verificar critérios de sucesso
                    success_criteria = [
                        ("connection_id", bool(self.connection_id)),
                        ("instance_name", bool(connection_data.get("instance_name"))),
                        ("status", status == "connecting"),
                        ("qr_code_present", qr_code is not None)
                    ]
                    
                    failed_criteria = [name for name, passed in success_criteria if not passed]
                    
                    if failed_criteria:
                        self.log_test(
                            "Create Connection",
                            False,
                            f"Status: {response.status}, Critérios falharam: {failed_criteria}. QR code: {'presente' if qr_code else 'NULL'}",
                            data
                        )
                        return False
                    
                    self.log_test(
                        "Create Connection",
                        True,
                        f"Status: {response.status}, Connection ID: {self.connection_id}, Status: {status}, QR code: {'presente' if qr_code else 'ausente'}"
                    )
                    return True
                    
                else:
                    self.log_test(
                        "Create Connection",
                        False,
                        f"Status: {response.status}, Falha na criação",
                        data
                    )
                    return False
                    
        except asyncio.TimeoutError:
            self.log_test(
                "Create Connection",
                False,
                "Timeout de 35s atingido (esperado até 30s para gerar QR code)"
            )
            return False
        except Exception as e:
            self.log_test("Create Connection", False, f"Exceção: {str(e)}")
            return False
    
    async def test_list_connections(self):
        """3. Listar Conexões"""
        if not self.admin_token:
            self.log_test("List Connections", False, "Token admin não disponível")
            return False
            
        try:
            url = f"{BACKEND_URL}/whatsapp/connections"
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.get(url, headers=headers) as response:
                data = await response.json()
                
                if response.status == 200:
                    if isinstance(data, list):
                        connection_found = False
                        if self.connection_id:
                            connection_found = any(conn.get("id") == self.connection_id for conn in data)
                        
                        self.log_test(
                            "List Connections",
                            True,
                            f"Status: {response.status}, {len(data)} conexões encontradas, Conexão criada presente: {connection_found}"
                        )
                        return True
                    else:
                        self.log_test(
                            "List Connections",
                            False,
                            f"Status: {response.status}, Response não é array",
                            data
                        )
                        return False
                else:
                    self.log_test(
                        "List Connections",
                        False,
                        f"Status: {response.status}, Falha na listagem",
                        data
                    )
                    return False
                    
        except Exception as e:
            self.log_test("List Connections", False, f"Exceção: {str(e)}")
            return False
    
    async def test_check_status(self):
        """4. Verificar Status da Conexão"""
        if not self.admin_token or not self.connection_id:
            self.log_test("Check Status", False, "Token admin ou connection_id não disponível")
            return False
            
        try:
            url = f"{BACKEND_URL}/whatsapp/connections/{self.connection_id}/check-status"
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.get(url, headers=headers) as response:
                data = await response.json()
                
                if response.status == 200:
                    # Verificar campos obrigatórios
                    required_fields = ["connection_id", "status"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test(
                            "Check Status",
                            False,
                            f"Status: {response.status}, Campos obrigatórios ausentes: {missing_fields}",
                            data
                        )
                        return False
                    
                    status = data.get("status")
                    qr_code = data.get("qr_code")
                    
                    # Status deve ser "connecting" ou "connected"
                    valid_statuses = ["connecting", "connected"]
                    status_valid = status in valid_statuses
                    
                    self.log_test(
                        "Check Status",
                        status_valid,
                        f"Status: {response.status}, Connection status: {status}, QR code: {'presente' if qr_code else 'ausente'}, Status válido: {status_valid}"
                    )
                    return status_valid
                    
                else:
                    self.log_test(
                        "Check Status",
                        False,
                        f"Status: {response.status}, Falha na verificação",
                        data
                    )
                    return False
                    
        except Exception as e:
            self.log_test("Check Status", False, f"Exceção: {str(e)}")
            return False
    
    async def test_delete_connection(self):
        """5. Deletar Conexão"""
        if not self.admin_token or not self.connection_id:
            self.log_test("Delete Connection", False, "Token admin ou connection_id não disponível")
            return False
            
        try:
            url = f"{BACKEND_URL}/whatsapp/connections/{self.connection_id}"
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.delete(url, headers=headers) as response:
                data = await response.json()
                
                if response.status == 200:
                    message = data.get("message", "")
                    success_message = "success" in message.lower() or "deleted" in message.lower()
                    
                    self.log_test(
                        "Delete Connection",
                        success_message,
                        f"Status: {response.status}, Mensagem: {message}"
                    )
                    return success_message
                    
                else:
                    self.log_test(
                        "Delete Connection",
                        False,
                        f"Status: {response.status}, Falha na deleção",
                        data
                    )
                    return False
                    
        except Exception as e:
            self.log_test("Delete Connection", False, f"Exceção: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Executar todos os testes em sequência"""
        print("🚀 INICIANDO TESTE COMPLETO: WhatsApp WPPConnect Integration")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin: {ADMIN_EMAIL}")
        print("=" * 80)
        print()
        
        # Executar testes em ordem
        tests = [
            self.test_admin_login,
            self.test_create_connection,
            self.test_list_connections,
            self.test_check_status,
            self.test_delete_connection
        ]
        
        for test in tests:
            await test()
            # Pequena pausa entre testes
            await asyncio.sleep(1)
        
        # Resumo final
        self.print_summary()
    
    def print_summary(self):
        """Imprimir resumo dos testes"""
        print("=" * 80)
        print("📊 RESUMO DOS TESTES")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total de testes: {total_tests}")
        print(f"✅ Passou: {passed_tests}")
        print(f"❌ Falhou: {failed_tests}")
        print(f"Taxa de sucesso: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Detalhes dos testes que falharam
        if failed_tests > 0:
            print("🔍 TESTES QUE FALHARAM:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"❌ {result['test']}: {result['details']}")
            print()
        
        # Pontos críticos verificados
        print("🎯 PONTOS CRÍTICOS VERIFICADOS:")
        critical_points = [
            ("QR code gerado", any("QR code: presente" in r["details"] for r in self.test_results if r["success"])),
            ("Token JWT salvo", any("Token obtido" in r["details"] for r in self.test_results if r["success"])),
            ("Status connecting/connected", any("Status válido: True" in r["details"] for r in self.test_results if r["success"])),
            ("Timeout 30s respeitado", not any("Timeout" in r["details"] for r in self.test_results)),
            ("Deleção funcionando", any("Delete Connection" in r["test"] and r["success"] for r in self.test_results))
        ]
        
        for point, status in critical_points:
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {point}")
        
        print()
        print("🏁 TESTE COMPLETO FINALIZADO")

async def main():
    """Função principal"""
    try:
        async with WPPConnectTester() as tester:
            await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n⚠️ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())