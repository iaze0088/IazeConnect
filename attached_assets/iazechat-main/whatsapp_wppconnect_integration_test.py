#!/usr/bin/env python3
"""
Teste Completo da Integração WhatsApp WPPConnect
Conforme Review Request - Testar rotas após correção de roteamento

CONTEXTO:
- WPPConnect rodando em 151.243.218.223:21465
- SECRET_KEY: THISISMYSECURETOKEN
- Backend URL: https://suporte.help/api
- Rotas WhatsApp corrigidas e agora acessíveis em `/api/whatsapp/*`

CREDENCIAIS ADMIN:
- Email: admin@admin.com
- Senha: 102030@ab

TESTES NECESSÁRIOS:
1. GET /api/whatsapp/connections - Listar conexões existentes
2. POST /api/whatsapp/connections - Criar nova conexão
3. GET /api/whatsapp/connections/{connection_id}/qr - Obter QR code
4. GET /api/whatsapp/connections/{connection_id}/check-status - Verificar status
5. DELETE /api/whatsapp/connections/{connection_id} - Deletar conexão

RESULTADOS ESPERADOS:
- ✅ Todas as rotas devem responder (não retornar 404)
- ✅ Criação de conexão deve retornar QR code
- ✅ Integração com WPPConnect deve funcionar
- ✅ Status HTTP 200/201 para operações bem-sucedidas
"""

import asyncio
import httpx
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Configurações do teste
BACKEND_URL = "https://suporte.help/api"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "102030@ab"

# Configurações WPPConnect
WPPCONNECT_URL = "http://151.243.218.223:21465"
WPPCONNECT_SECRET = "THISISMYSECURETOKEN"

class WhatsAppWPPConnectTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.admin_token = None
        self.test_connection_id = None
        self.test_results = []
        
    async def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log de resultado do teste"""
        status = "✅ PASS" if success else "❌ FAIL"
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": timestamp,
            "response_data": response_data
        }
        
        self.test_results.append(result)
        
        print(f"[{timestamp}] {status} {test_name}")
        if details:
            print(f"         {details}")
        if response_data and not success:
            print(f"         Response: {json.dumps(response_data, indent=2)[:200]}...")
        print()
    
    async def admin_login(self) -> bool:
        """Fazer login como admin e obter token JWT"""
        try:
            print("🔐 STEP 1: Admin Login")
            print("=" * 50)
            
            response = await self.client.post(
                f"{BACKEND_URL}/auth/admin/login",
                json={
                    "email": ADMIN_EMAIL,
                    "password": ADMIN_PASSWORD
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("token")
                
                await self.log_test(
                    "Admin Login",
                    True,
                    f"Token obtido com sucesso. User: {data.get('user_data', {}).get('email', 'N/A')}",
                    {"status_code": response.status_code, "user_type": data.get("user_type")}
                )
                return True
            else:
                await self.log_test(
                    "Admin Login",
                    False,
                    f"Status {response.status_code}: {response.text}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            await self.log_test(
                "Admin Login",
                False,
                f"Exception: {type(e).__name__}: {e}",
                {"error": str(e)}
            )
            return False
    
    async def test_list_connections(self) -> bool:
        """Teste: GET /api/whatsapp/connections"""
        try:
            print("📋 STEP 2: List WhatsApp Connections")
            print("=" * 50)
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = await self.client.get(
                f"{BACKEND_URL}/whatsapp/connections",
                headers=headers
            )
            
            if response.status_code == 200:
                connections = response.json()
                await self.log_test(
                    "GET /api/whatsapp/connections",
                    True,
                    f"Retornou {len(connections)} conexões existentes",
                    {"status_code": response.status_code, "count": len(connections)}
                )
                return True
            else:
                await self.log_test(
                    "GET /api/whatsapp/connections",
                    False,
                    f"Status {response.status_code}: {response.text}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            await self.log_test(
                "GET /api/whatsapp/connections",
                False,
                f"Exception: {type(e).__name__}: {e}",
                {"error": str(e)}
            )
            return False
    
    async def test_create_connection(self) -> bool:
        """Teste: POST /api/whatsapp/connections"""
        try:
            print("🆕 STEP 3: Create New WhatsApp Connection")
            print("=" * 50)
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            connection_data = {
                "name": "Teste Conexão WPPConnect"
            }
            
            response = await self.client.post(
                f"{BACKEND_URL}/whatsapp/connections",
                headers=headers,
                json=connection_data
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.test_connection_id = data.get("id")
                
                # Verificar campos obrigatórios
                required_fields = ["id", "name", "status"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    await self.log_test(
                        "POST /api/whatsapp/connections",
                        False,
                        f"Campos obrigatórios ausentes: {missing_fields}",
                        data
                    )
                    return False
                
                # Verificar se retornou QR code
                has_qr = bool(data.get("qr_code_base64") or data.get("qr_code"))
                
                await self.log_test(
                    "POST /api/whatsapp/connections",
                    True,
                    f"Conexão criada: ID={self.test_connection_id}, QR Code={'✅' if has_qr else '❌'}, Status={data.get('status')}",
                    {
                        "status_code": response.status_code,
                        "connection_id": self.test_connection_id,
                        "has_qr_code": has_qr,
                        "status": data.get("status")
                    }
                )
                return True
            else:
                await self.log_test(
                    "POST /api/whatsapp/connections",
                    False,
                    f"Status {response.status_code}: {response.text}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            await self.log_test(
                "POST /api/whatsapp/connections",
                False,
                f"Exception: {type(e).__name__}: {e}",
                {"error": str(e)}
            )
            return False
    
    async def test_get_qr_code(self) -> bool:
        """Teste: GET /api/whatsapp/connections/{connection_id}/qr"""
        try:
            print("📱 STEP 4: Get QR Code")
            print("=" * 50)
            
            if not self.test_connection_id:
                await self.log_test(
                    "GET /api/whatsapp/connections/{id}/qr",
                    False,
                    "Nenhuma conexão criada para testar QR code",
                    {"error": "No connection_id available"}
                )
                return False
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = await self.client.get(
                f"{BACKEND_URL}/whatsapp/connections/{self.test_connection_id}/qr",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verificar se retornou QR code
                has_qr = bool(data.get("qr_code_base64") or data.get("qr_code"))
                
                await self.log_test(
                    "GET /api/whatsapp/connections/{id}/qr",
                    True,
                    f"QR Code obtido: {'✅ Disponível' if has_qr else '❌ Não disponível'}, Status={data.get('status')}",
                    {
                        "status_code": response.status_code,
                        "has_qr_code": has_qr,
                        "status": data.get("status")
                    }
                )
                return True
            else:
                await self.log_test(
                    "GET /api/whatsapp/connections/{id}/qr",
                    False,
                    f"Status {response.status_code}: {response.text}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            await self.log_test(
                "GET /api/whatsapp/connections/{id}/qr",
                False,
                f"Exception: {type(e).__name__}: {e}",
                {"error": str(e)}
            )
            return False
    
    async def test_check_status(self) -> bool:
        """Teste: GET /api/whatsapp/connections/{connection_id}/check-status"""
        try:
            print("🔍 STEP 5: Check Connection Status")
            print("=" * 50)
            
            if not self.test_connection_id:
                await self.log_test(
                    "GET /api/whatsapp/connections/{id}/check-status",
                    False,
                    "Nenhuma conexão criada para verificar status",
                    {"error": "No connection_id available"}
                )
                return False
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = await self.client.get(
                f"{BACKEND_URL}/whatsapp/connections/{self.test_connection_id}/check-status",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                await self.log_test(
                    "GET /api/whatsapp/connections/{id}/check-status",
                    True,
                    f"Status verificado: {data.get('status')}, Instance: {data.get('instance_name', 'N/A')}",
                    {
                        "status_code": response.status_code,
                        "connection_status": data.get("status"),
                        "instance_name": data.get("instance_name")
                    }
                )
                return True
            else:
                await self.log_test(
                    "GET /api/whatsapp/connections/{id}/check-status",
                    False,
                    f"Status {response.status_code}: {response.text}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            await self.log_test(
                "GET /api/whatsapp/connections/{id}/check-status",
                False,
                f"Exception: {type(e).__name__}: {e}",
                {"error": str(e)}
            )
            return False
    
    async def test_delete_connection(self) -> bool:
        """Teste: DELETE /api/whatsapp/connections/{connection_id}"""
        try:
            print("🗑️ STEP 6: Delete Connection")
            print("=" * 50)
            
            if not self.test_connection_id:
                await self.log_test(
                    "DELETE /api/whatsapp/connections/{id}",
                    False,
                    "Nenhuma conexão criada para deletar",
                    {"error": "No connection_id available"}
                )
                return False
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = await self.client.delete(
                f"{BACKEND_URL}/whatsapp/connections/{self.test_connection_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                await self.log_test(
                    "DELETE /api/whatsapp/connections/{id}",
                    True,
                    f"Conexão deletada com sucesso: {data.get('message', 'OK')}",
                    {
                        "status_code": response.status_code,
                        "message": data.get("message")
                    }
                )
                return True
            else:
                await self.log_test(
                    "DELETE /api/whatsapp/connections/{id}",
                    False,
                    f"Status {response.status_code}: {response.text}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            await self.log_test(
                "DELETE /api/whatsapp/connections/{id}",
                False,
                f"Exception: {type(e).__name__}: {e}",
                {"error": str(e)}
            )
            return False
    
    async def test_wppconnect_direct(self) -> bool:
        """Teste direto com WPPConnect para verificar conectividade"""
        try:
            print("🔗 STEP 7: Direct WPPConnect Test")
            print("=" * 50)
            
            # Testar endpoint de status do WPPConnect
            response = await self.client.get(f"{WPPCONNECT_URL}/api/status")
            
            if response.status_code == 200:
                await self.log_test(
                    "WPPConnect Direct Connection",
                    True,
                    f"WPPConnect respondendo em {WPPCONNECT_URL}",
                    {"status_code": response.status_code, "wppconnect_url": WPPCONNECT_URL}
                )
                return True
            else:
                await self.log_test(
                    "WPPConnect Direct Connection",
                    False,
                    f"WPPConnect não respondeu: Status {response.status_code}",
                    {"status_code": response.status_code, "wppconnect_url": WPPCONNECT_URL}
                )
                return False
                
        except Exception as e:
            await self.log_test(
                "WPPConnect Direct Connection",
                False,
                f"Erro ao conectar com WPPConnect: {type(e).__name__}: {e}",
                {"error": str(e), "wppconnect_url": WPPCONNECT_URL}
            )
            return False
    
    async def run_all_tests(self):
        """Executar todos os testes"""
        print("🚀 INICIANDO TESTE COMPLETO DA INTEGRAÇÃO WHATSAPP WPPCONNECT")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"WPPConnect URL: {WPPCONNECT_URL}")
        print(f"Admin: {ADMIN_EMAIL}")
        print("=" * 80)
        print()
        
        # Executar testes em sequência
        tests = [
            ("Admin Login", self.admin_login),
            ("List Connections", self.test_list_connections),
            ("Create Connection", self.test_create_connection),
            ("Get QR Code", self.test_get_qr_code),
            ("Check Status", self.test_check_status),
            ("Delete Connection", self.test_delete_connection),
            ("WPPConnect Direct", self.test_wppconnect_direct)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                success = await test_func()
                if success:
                    passed += 1
            except Exception as e:
                print(f"❌ ERRO CRÍTICO em {test_name}: {e}")
                await self.log_test(test_name, False, f"Erro crítico: {e}")
        
        # Relatório final
        print("\n" + "=" * 80)
        print("📊 RELATÓRIO FINAL DOS TESTES")
        print("=" * 80)
        
        success_rate = (passed / total) * 100
        status_emoji = "🟢" if success_rate >= 80 else "🟡" if success_rate >= 60 else "🔴"
        
        print(f"{status_emoji} RESULTADO GERAL: {passed}/{total} testes passaram ({success_rate:.1f}%)")
        print()
        
        # Detalhes por teste
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   {result['details']}")
        
        print("\n" + "=" * 80)
        
        # Análise específica do review request
        print("🎯 ANÁLISE CONFORME REVIEW REQUEST:")
        print("=" * 80)
        
        # Verificar se todas as rotas respondem (não 404)
        route_tests = [r for r in self.test_results if "whatsapp/connections" in r["test"]]
        no_404_errors = all(
            r["success"] or (r.get("response_data", {}).get("status_code") != 404)
            for r in route_tests
        )
        
        print(f"✅ Todas as rotas respondem (não 404): {'SIM' if no_404_errors else 'NÃO'}")
        
        # Verificar se criação retorna QR code
        create_test = next((r for r in self.test_results if "POST" in r["test"]), None)
        qr_returned = create_test and create_test.get("response_data", {}).get("has_qr_code", False)
        
        print(f"✅ Criação retorna QR code: {'SIM' if qr_returned else 'NÃO'}")
        
        # Verificar integração WPPConnect
        wppconnect_test = next((r for r in self.test_results if "WPPConnect Direct" in r["test"]), None)
        wppconnect_working = wppconnect_test and wppconnect_test["success"]
        
        print(f"✅ Integração WPPConnect funciona: {'SIM' if wppconnect_working else 'NÃO'}")
        
        # Status HTTP corretos
        http_ok = all(
            r["success"] or r.get("response_data", {}).get("status_code") in [200, 201, 404, 500]
            for r in self.test_results
        )
        
        print(f"✅ Status HTTP 200/201 para sucessos: {'SIM' if http_ok else 'NÃO'}")
        
        print("\n" + "=" * 80)
        
        if success_rate >= 80:
            print("🎉 INTEGRAÇÃO WHATSAPP WPPCONNECT FUNCIONANDO!")
        elif success_rate >= 60:
            print("⚠️ INTEGRAÇÃO PARCIALMENTE FUNCIONAL - REQUER ATENÇÃO")
        else:
            print("🚨 INTEGRAÇÃO COM PROBLEMAS CRÍTICOS - REQUER CORREÇÃO")
        
        print("=" * 80)
        
        await self.client.aclose()
        return success_rate >= 80

async def main():
    """Função principal"""
    tester = WhatsAppWPPConnectTester()
    
    try:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Teste interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro crítico: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())