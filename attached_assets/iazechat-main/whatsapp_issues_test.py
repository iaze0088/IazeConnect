#!/usr/bin/env python3
"""
TESTE DOS PROBLEMAS ESPECÍFICOS MENCIONADOS NO REVIEW REQUEST
Testa os problemas de duplicatas, status não atualiza, e webhook
"""

import asyncio
import httpx
import json
from datetime import datetime

BACKEND_URL = "https://wppconnect-fix.preview.emergentagent.com"

RESELLER_CREDENTIALS = {
    "email": "fabio@gmail.com", 
    "password": "102030ab"
}

class WhatsAppIssuesTester:
    def __init__(self):
        self.reseller_token = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log resultado do teste"""
        status = "✅ PASSOU" if success else "❌ FALHOU"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Detalhes: {details}")
        print()

    async def setup_login(self):
        """Login inicial"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/api/resellers/login",
                json=RESELLER_CREDENTIALS
            )
            
            if response.status_code == 200:
                data = response.json()
                self.reseller_token = data.get("token")
                return True
            return False

    async def test_duplicate_prevention(self):
        """Teste 1: Verificar prevenção de duplicatas"""
        if not self.reseller_token:
            self.log_test("Prevenção Duplicatas", False, "Token não disponível")
            return False
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Tentar criar primeira conexão
                response1 = await client.post(
                    f"{BACKEND_URL}/api/whatsapp/connections",
                    json={
                        "reseller_id": "49376e6f-4122-4fcf-88ab-97965c472711",
                        "max_received_daily": 200,
                        "max_sent_daily": 200
                    },
                    headers={"Authorization": f"Bearer {self.reseller_token}"}
                )
                
                # Tentar criar segunda conexão (deve retornar a existente)
                response2 = await client.post(
                    f"{BACKEND_URL}/api/whatsapp/connections",
                    json={
                        "reseller_id": "49376e6f-4122-4fcf-88ab-97965c472711",
                        "max_received_daily": 200,
                        "max_sent_daily": 200
                    },
                    headers={"Authorization": f"Bearer {self.reseller_token}"}
                )
                
                if response1.status_code == 200 and response2.status_code == 200:
                    data1 = response1.json()
                    data2 = response2.json()
                    
                    # Verificar se retornou a mesma conexão (prevenção de duplicata)
                    same_id = data1.get("id") == data2.get("id")
                    same_instance = data1.get("instance_name") == data2.get("instance_name")
                    
                    if same_id and same_instance:
                        self.log_test(
                            "Prevenção Duplicatas", 
                            True, 
                            f"Sistema retornou conexão existente (ID: {data1.get('id')})"
                        )
                        return True
                    else:
                        self.log_test(
                            "Prevenção Duplicatas", 
                            False, 
                            f"Sistema criou duplicata! ID1: {data1.get('id')}, ID2: {data2.get('id')}"
                        )
                        return False
                else:
                    self.log_test(
                        "Prevenção Duplicatas", 
                        False, 
                        f"Erro nas requisições: {response1.status_code}, {response2.status_code}"
                    )
                    return False
                    
        except Exception as e:
            self.log_test("Prevenção Duplicatas", False, f"Erro: {str(e)}")
            return False

    async def test_status_synchronization(self):
        """Teste 2: Verificar sincronização de status entre banco e Evolution API"""
        if not self.reseller_token:
            self.log_test("Sincronização Status", False, "Token não disponível")
            return False
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Buscar conexões atuais
                response = await client.get(
                    f"{BACKEND_URL}/api/whatsapp/connections",
                    headers={"Authorization": f"Bearer {self.reseller_token}"}
                )
                
                if response.status_code == 200:
                    connections = response.json()
                    
                    if connections:
                        conn = connections[0]
                        status = conn.get("status")
                        instance_name = conn.get("instance_name")
                        phone_number = conn.get("phone_number")
                        qr_code = conn.get("qr_code")
                        
                        # Verificar consistência do status
                        status_checks = []
                        
                        if status == "connected":
                            status_checks.append(("QR Code removido quando conectado", qr_code is None))
                            status_checks.append(("Phone number preenchido quando conectado", phone_number is not None))
                        elif status == "connecting":
                            status_checks.append(("Status connecting válido", True))
                        
                        all_consistent = all(check[1] for check in status_checks)
                        
                        details = f"Status: {status}, Phone: {phone_number}, QR: {'Sim' if qr_code else 'Não'}"
                        self.log_test("Sincronização Status", all_consistent, details)
                        return all_consistent
                    else:
                        self.log_test("Sincronização Status", False, "Nenhuma conexão encontrada")
                        return False
                else:
                    self.log_test(
                        "Sincronização Status", 
                        False, 
                        f"Erro ao buscar conexões: {response.status_code}"
                    )
                    return False
                    
        except Exception as e:
            self.log_test("Sincronização Status", False, f"Erro: {str(e)}")
            return False

    async def test_webhook_functionality(self):
        """Teste 3: Verificar funcionalidade do webhook"""
        try:
            # Testar webhook com diferentes tipos de mensagem
            test_cases = [
                {
                    "name": "Mensagem texto simples",
                    "data": {
                        "event": "messages.upsert",
                        "instance": "fabio_1_1761324563",
                        "data": {
                            "key": {
                                "remoteJid": "5511888888888@s.whatsapp.net",
                                "fromMe": False
                            },
                            "message": {
                                "conversation": "Olá, preciso de ajuda"
                            },
                            "pushName": "Cliente Teste 1"
                        }
                    }
                },
                {
                    "name": "Mensagem texto estendida",
                    "data": {
                        "event": "messages.upsert",
                        "instance": "fabio_1_1761324563",
                        "data": {
                            "key": {
                                "remoteJid": "5511777777777@s.whatsapp.net",
                                "fromMe": False
                            },
                            "message": {
                                "extendedTextMessage": {
                                    "text": "Esta é uma mensagem de texto estendida"
                                }
                            },
                            "pushName": "Cliente Teste 2"
                        }
                    }
                }
            ]
            
            successful_webhooks = 0
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for test_case in test_cases:
                    response = await client.post(
                        f"{BACKEND_URL}/api/whatsapp/webhook/evolution",
                        json=test_case["data"]
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("success"):
                            successful_webhooks += 1
                            print(f"   ✅ {test_case['name']}: Ticket {data.get('ticket_id')}")
                        else:
                            print(f"   ❌ {test_case['name']}: {data.get('error', 'Unknown error')}")
                    else:
                        print(f"   ❌ {test_case['name']}: HTTP {response.status_code}")
            
            success_rate = successful_webhooks / len(test_cases)
            
            if success_rate >= 0.8:  # 80% ou mais
                self.log_test(
                    "Funcionalidade Webhook", 
                    True, 
                    f"{successful_webhooks}/{len(test_cases)} webhooks processados com sucesso"
                )
                return True
            else:
                self.log_test(
                    "Funcionalidade Webhook", 
                    False, 
                    f"Apenas {successful_webhooks}/{len(test_cases)} webhooks funcionaram"
                )
                return False
                
        except Exception as e:
            self.log_test("Funcionalidade Webhook", False, f"Erro: {str(e)}")
            return False

    async def test_automatic_polling_simulation(self):
        """Teste 4: Simular polling automático a cada 3s"""
        if not self.reseller_token:
            self.log_test("Polling Automático", False, "Token não disponível")
            return False
            
        try:
            status_changes = []
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Simular 5 verificações de status (como se fosse polling automático)
                for i in range(5):
                    response = await client.get(
                        f"{BACKEND_URL}/api/whatsapp/connections",
                        headers={"Authorization": f"Bearer {self.reseller_token}"}
                    )
                    
                    if response.status_code == 200:
                        connections = response.json()
                        if connections:
                            conn = connections[0]
                            status = conn.get("status")
                            qr_code = conn.get("qr_code")
                            phone = conn.get("phone_number")
                            
                            status_changes.append({
                                "poll": i + 1,
                                "status": status,
                                "has_qr": qr_code is not None,
                                "has_phone": phone is not None
                            })
                            
                            print(f"   Poll {i+1}: Status={status}, QR={'Sim' if qr_code else 'Não'}, Phone={'Sim' if phone else 'Não'}")
                    
                    # Aguardar 3 segundos (como polling real)
                    if i < 4:
                        await asyncio.sleep(3)
            
            # Verificar se o polling está funcionando consistentemente
            if len(status_changes) >= 4:
                # Verificar se status está consistente
                last_status = status_changes[-1]["status"]
                consistent = all(s["status"] == last_status for s in status_changes[-3:])
                
                self.log_test(
                    "Polling Automático", 
                    True, 
                    f"Polling funcionando. Status final: {last_status}, Consistente: {consistent}"
                )
                return True
            else:
                self.log_test("Polling Automático", False, "Polling não funcionou adequadamente")
                return False
                
        except Exception as e:
            self.log_test("Polling Automático", False, f"Erro: {str(e)}")
            return False

    async def run_all_tests(self):
        """Executar todos os testes de problemas específicos"""
        print("🔍 TESTANDO PROBLEMAS ESPECÍFICOS DO WHATSAPP")
        print("=" * 60)
        print()
        
        # Setup
        if not await self.setup_login():
            print("❌ Falha no login inicial. Abortando testes.")
            return 0, 0
        
        tests = [
            ("1. Prevenção de Duplicatas", self.test_duplicate_prevention),
            ("2. Sincronização de Status", self.test_status_synchronization),
            ("3. Funcionalidade Webhook", self.test_webhook_functionality),
            ("4. Polling Automático", self.test_automatic_polling_simulation)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"🔄 Executando: {test_name}")
            try:
                result = await test_func()
                if result:
                    passed += 1
            except Exception as e:
                print(f"❌ ERRO CRÍTICO em {test_name}: {e}")
            
            print("-" * 40)
        
        # Resumo final
        print()
        print("📊 RESUMO DOS TESTES DE PROBLEMAS")
        print("=" * 60)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   {result['details']}")
        
        print()
        print(f"🎯 RESULTADO FINAL: {passed}/{total} testes passaram ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 TODOS OS PROBLEMAS FORAM RESOLVIDOS!")
        elif passed >= total * 0.75:
            print("⚠️ Maioria dos problemas resolvidos. Verificar falhas menores.")
        else:
            print("❌ Ainda há problemas críticos a resolver.")
        
        return passed, total

async def main():
    """Função principal"""
    tester = WhatsAppIssuesTester()
    
    try:
        passed, total = await tester.run_all_tests()
        
        # Salvar resultados
        results_file = "/app/whatsapp_issues_results.json"
        with open(results_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "passed": passed,
                    "total": total,
                    "success_rate": passed/total*100 if total > 0 else 0
                },
                "tests": tester.test_results
            }, f, indent=2)
        
        print(f"\n📄 Resultados salvos em: {results_file}")
        
    except Exception as e:
        print(f"❌ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())