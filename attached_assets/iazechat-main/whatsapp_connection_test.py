#!/usr/bin/env python3
"""
Teste do endpoint de criação de conexão WhatsApp no backend IAZE
Conforme review request específico do usuário

Endpoint testado: POST /api/whatsapp/connections
Backend: https://wppconnect-fix.preview.emergentagent.com
Evolution API: http://151.243.218.223:9000
API Key: iaze-evolution-2025-secure-key
"""

import asyncio
import httpx
import json
import sys
from datetime import datetime

# Configurações do teste
BACKEND_URL = "https://wppconnect-fix.preview.emergentagent.com"
EVOLUTION_API_URL = "http://151.243.218.223:9000"
EVOLUTION_API_KEY = "iaze-evolution-2025-secure-key"

# Credenciais de admin (conforme test_result.md)
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "102030@ab"

class WhatsAppConnectionTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.admin_token = None
        self.test_results = []
        
    async def log_test(self, test_name: str, success: bool, details: str):
        """Log de resultado do teste"""
        status = "✅ PASSOU" if success else "❌ FALHOU"
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": timestamp
        }
        self.test_results.append(result)
        
        print(f"[{timestamp}] {status} - {test_name}")
        print(f"         {details}")
        print()
        
    async def test_admin_login(self):
        """Teste 1: Login como admin para obter token JWT"""
        try:
            response = await self.client.post(
                f"{BACKEND_URL}/api/auth/admin/login",
                json={
                    "email": ADMIN_EMAIL,
                    "password": ADMIN_PASSWORD
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("token")
                
                if self.admin_token:
                    await self.log_test(
                        "Admin Login",
                        True,
                        f"Login realizado com sucesso. Token obtido: {self.admin_token[:20]}..."
                    )
                    return True
                else:
                    await self.log_test(
                        "Admin Login",
                        False,
                        "Login OK mas token não retornado na resposta"
                    )
                    return False
            else:
                await self.log_test(
                    "Admin Login",
                    False,
                    f"Status {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            await self.log_test(
                "Admin Login",
                False,
                f"Erro na requisição: {str(e)}"
            )
            return False
    
    async def test_evolution_api_connectivity(self):
        """Teste 2: Verificar conectividade com Evolution API"""
        try:
            # Testar endpoint de status da Evolution API
            response = await self.client.get(
                f"{EVOLUTION_API_URL}/manager/status",
                headers={"apikey": EVOLUTION_API_KEY}
            )
            
            if response.status_code == 200:
                await self.log_test(
                    "Evolution API Connectivity",
                    True,
                    f"Evolution API respondeu: {response.status_code} - {response.text[:100]}"
                )
                return True
            else:
                await self.log_test(
                    "Evolution API Connectivity",
                    False,
                    f"Evolution API retornou status {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            await self.log_test(
                "Evolution API Connectivity",
                False,
                f"Erro ao conectar com Evolution API: {str(e)}"
            )
            return False
    
    async def test_create_whatsapp_connection(self):
        """Teste 3: Criar nova conexão WhatsApp"""
        if not self.admin_token:
            await self.log_test(
                "Create WhatsApp Connection",
                False,
                "Token de admin não disponível. Execute o login primeiro."
            )
            return False
            
        try:
            # Payload conforme especificado no review request
            payload = {
                "name": "Teste Backend"
            }
            
            response = await self.client.post(
                f"{BACKEND_URL}/api/whatsapp/connections",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.admin_token}",
                    "Content-Type": "application/json"
                }
            )
            
            print(f"🔍 Status da resposta: {response.status_code}")
            print(f"🔍 Headers da resposta: {dict(response.headers)}")
            
            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                print(f"🔍 Dados da resposta: {json.dumps(data, indent=2)}")
                
                # Verificar campos obrigatórios conforme review request
                required_fields = ["id", "instance_name", "status"]
                optional_fields = ["qr_code", "qr_code_base64"]
                
                missing_fields = []
                present_fields = []
                
                # Verificar campos obrigatórios
                for field in required_fields:
                    if field in data:
                        present_fields.append(field)
                    else:
                        # Tentar variações do nome do campo
                        if field == "id" and "connection_id" in data:
                            present_fields.append("connection_id (como id)")
                        else:
                            missing_fields.append(field)
                
                # Verificar campos opcionais
                for field in optional_fields:
                    if field in data and data[field]:
                        present_fields.append(field)
                
                # Verificar se status é "connecting"
                status_ok = data.get("status") == "connecting"
                
                if not missing_fields and status_ok:
                    await self.log_test(
                        "Create WhatsApp Connection",
                        True,
                        f"Conexão criada com sucesso!\n" +
                        f"         Connection ID: {data.get('id') or data.get('connection_id')}\n" +
                        f"         Instance Name: {data.get('instance_name')}\n" +
                        f"         Status: {data.get('status')}\n" +
                        f"         Campos presentes: {', '.join(present_fields)}\n" +
                        f"         QR Code disponível: {'Sim' if data.get('qr_code') or data.get('qr_code_base64') else 'Não'}"
                    )
                    return True
                else:
                    issues = []
                    if missing_fields:
                        issues.append(f"Campos obrigatórios ausentes: {', '.join(missing_fields)}")
                    if not status_ok:
                        issues.append(f"Status incorreto: '{data.get('status')}' (esperado: 'connecting')")
                    
                    await self.log_test(
                        "Create WhatsApp Connection",
                        False,
                        f"Resposta incompleta: {'; '.join(issues)}\n" +
                        f"         Dados recebidos: {json.dumps(data, indent=2)}"
                    )
                    return False
                    
            elif response.status_code == 500:
                # Erro 500 - capturar detalhes conforme solicitado
                try:
                    error_data = response.json()
                    await self.log_test(
                        "Create WhatsApp Connection",
                        False,
                        f"ERRO 500 - Detalhes capturados:\n" +
                        f"         Response: {json.dumps(error_data, indent=2)}\n" +
                        f"         Possível problema de conectividade com Evolution API"
                    )
                except:
                    await self.log_test(
                        "Create WhatsApp Connection",
                        False,
                        f"ERRO 500 - Resposta não é JSON válido:\n" +
                        f"         Raw response: {response.text}"
                    )
                return False
            else:
                await self.log_test(
                    "Create WhatsApp Connection",
                    False,
                    f"Status inesperado {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            await self.log_test(
                "Create WhatsApp Connection",
                False,
                f"Erro na requisição: {str(e)}"
            )
            return False
    
    async def test_backend_logs(self):
        """Teste 4: Verificar logs do backend (se possível)"""
        try:
            # Tentar acessar endpoint de health para verificar se backend está respondendo
            response = await self.client.get(f"{BACKEND_URL}/health")
            
            if response.status_code == 200:
                data = response.json()
                await self.log_test(
                    "Backend Health Check",
                    True,
                    f"Backend está saudável: {json.dumps(data, indent=2)}"
                )
                return True
            else:
                await self.log_test(
                    "Backend Health Check",
                    False,
                    f"Health check falhou: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            await self.log_test(
                "Backend Health Check",
                False,
                f"Erro ao verificar saúde do backend: {str(e)}"
            )
            return False
    
    async def run_all_tests(self):
        """Executar todos os testes em sequência"""
        print("🚀 INICIANDO TESTE DO ENDPOINT DE CRIAÇÃO DE CONEXÃO WHATSAPP")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Evolution API: {EVOLUTION_API_URL}")
        print(f"Credenciais Admin: {ADMIN_EMAIL}")
        print("=" * 80)
        print()
        
        # Executar testes em ordem
        tests = [
            self.test_admin_login,
            self.test_evolution_api_connectivity,
            self.test_create_whatsapp_connection,
            self.test_backend_logs
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            success = await test()
            if success:
                passed += 1
        
        # Resumo final
        print("=" * 80)
        print("📊 RESUMO DOS TESTES")
        print("=" * 80)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
        
        print()
        print(f"📈 RESULTADO FINAL: {passed}/{total} testes passaram ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            print("🎉 TODOS OS TESTES PASSARAM! Endpoint funcionando corretamente.")
        else:
            print("⚠️ ALGUNS TESTES FALHARAM. Verifique os detalhes acima.")
            
            # Se o teste de criação falhou, dar recomendações
            creation_test = next((r for r in self.test_results if r["test"] == "Create WhatsApp Connection"), None)
            if creation_test and not creation_test["success"]:
                print()
                print("🔧 RECOMENDAÇÕES PARA CORREÇÃO:")
                print("1. Verificar se Evolution API está rodando em http://151.243.218.223:9000")
                print("2. Verificar se API Key 'iaze-evolution-2025-secure-key' está correta")
                print("3. Verificar logs do backend para erros de conectividade")
                print("4. Verificar se o endpoint /api/whatsapp/connections está implementado")
        
        print("=" * 80)
        
        await self.client.aclose()
        return passed == total

async def main():
    """Função principal"""
    tester = WhatsAppConnectionTester()
    success = await tester.run_all_tests()
    
    # Exit code para CI/CD
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())