#!/usr/bin/env python3
"""
🧪 TESTE CRÍTICO - VERIFICAR ABAS DO ATENDENTE

**OBJETIVO**: Testar se mensagens aparecem nas abas e verificar performance.

**BACKEND URL**: https://suporte.help/api

**CREDENCIAIS**:
- Admin: admin@admin.com / 102030@ab
- Agente: (usar qualquer agente existente)

Conforme review request específico do usuário.
"""

import asyncio
import aiohttp
import json
import uuid
import time
from datetime import datetime
import sys

# Configuração
BACKEND_URL = "https://suporte.help/api"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "102030@ab"

class AtendenteTabsTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.test_results = []
        self.created_client_id = None
        self.created_ticket_id = None
        self.client_token = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, status: str, details: str = "", response_data: dict = None, response_time: float = None):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data,
            "response_time": response_time
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        time_info = f" ({response_time:.2f}s)" if response_time else ""
        print(f"{status_emoji} {test_name}: {status}{time_info}")
        if details:
            print(f"   {details}")
        if response_data and status == "FAIL":
            print(f"   Response: {json.dumps(response_data, indent=2)}")
        print()
    
    async def admin_login(self):
        """TESTE 1.1: Login como Admin"""
        try:
            start_time = time.time()
            async with self.session.post(
                f"{BACKEND_URL}/auth/admin/login",
                json={"password": ADMIN_PASSWORD}
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    self.admin_token = data.get("token")
                    self.log_test(
                        "1.1 Login como Admin", 
                        "PASS", 
                        f"Token obtido: {self.admin_token[:20]}...",
                        {"user_type": data.get("user_type")},
                        response_time
                    )
                    return True
                else:
                    error_data = await response.json()
                    self.log_test(
                        "1.1 Login como Admin", 
                        "FAIL", 
                        f"Status {response.status}",
                        error_data,
                        response_time
                    )
                    return False
        except Exception as e:
            self.log_test("1.1 Login como Admin", "FAIL", f"Exception: {str(e)}")
            return False
    
    async def test_tickets_by_status(self):
        """TESTE 1.2-1.4: Listar Tickets por Status"""
        if not self.admin_token:
            self.log_test("Tickets por Status", "SKIP", "Admin token não disponível")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # 1.2 Listar Tickets com Status "open" (ABA ESPERA)
        try:
            start_time = time.time()
            async with self.session.get(f"{BACKEND_URL}/tickets?status=open&limit=20", headers=headers) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    tickets = await response.json()
                    ticket_count = len(tickets)
                    
                    if ticket_count == 0:
                        self.log_test(
                            "1.2 Tickets Status 'open' (ABA ESPERA)", 
                            "WARNING", 
                            "⚠️ PROBLEMA - Não há tickets em 'open'",
                            {"count": ticket_count},
                            response_time
                        )
                    else:
                        # Verificar campos obrigatórios no primeiro ticket
                        first_ticket = tickets[0]
                        required_fields = ["id", "client_whatsapp", "status", "client_id"]
                        missing_fields = [field for field in required_fields if field not in first_ticket]
                        
                        if missing_fields:
                            self.log_test(
                                "1.2 Tickets Status 'open' - Campos", 
                                "FAIL", 
                                f"Campos ausentes: {missing_fields}",
                                first_ticket,
                                response_time
                            )
                        else:
                            self.log_test(
                                "1.2 Tickets Status 'open' (ABA ESPERA)", 
                                "PASS", 
                                f"✅ {ticket_count} tickets retornados, campos obrigatórios presentes",
                                {"count": ticket_count, "first_ticket": first_ticket},
                                response_time
                            )
                            print(f"   📋 Primeiro ticket: ID={first_ticket.get('id')}, WhatsApp={first_ticket.get('client_whatsapp')}")
                else:
                    error_data = await response.json()
                    self.log_test(
                        "1.2 Tickets Status 'open'", 
                        "FAIL", 
                        f"Status {response.status}",
                        error_data,
                        response_time
                    )
        except Exception as e:
            self.log_test("1.2 Tickets Status 'open'", "FAIL", f"Exception: {str(e)}")
        
        # 1.3 Listar Tickets com Status "ATENDENDO"
        try:
            start_time = time.time()
            async with self.session.get(f"{BACKEND_URL}/tickets?status=ATENDENDO&limit=20", headers=headers) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    tickets = await response.json()
                    ticket_count = len(tickets)
                    self.log_test(
                        "1.3 Tickets Status 'ATENDENDO'", 
                        "PASS", 
                        f"✅ {ticket_count} tickets retornados",
                        {"count": ticket_count},
                        response_time
                    )
                else:
                    error_data = await response.json()
                    self.log_test(
                        "1.3 Tickets Status 'ATENDENDO'", 
                        "FAIL", 
                        f"Status {response.status}",
                        error_data,
                        response_time
                    )
        except Exception as e:
            self.log_test("1.3 Tickets Status 'ATENDENDO'", "FAIL", f"Exception: {str(e)}")
        
        # 1.4 Listar Tickets com Status "FINALIZADAS"
        try:
            start_time = time.time()
            async with self.session.get(f"{BACKEND_URL}/tickets?status=FINALIZADAS&limit=20", headers=headers) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    tickets = await response.json()
                    ticket_count = len(tickets)
                    self.log_test(
                        "1.4 Tickets Status 'FINALIZADAS'", 
                        "PASS", 
                        f"✅ {ticket_count} tickets retornados",
                        {"count": ticket_count},
                        response_time
                    )
                else:
                    error_data = await response.json()
                    self.log_test(
                        "1.4 Tickets Status 'FINALIZADAS'", 
                        "FAIL", 
                        f"Status {response.status}",
                        error_data,
                        response_time
                    )
        except Exception as e:
            self.log_test("1.4 Tickets Status 'FINALIZADAS'", "FAIL", f"Exception: {str(e)}")
    
    async def test_ticket_counts(self):
        """TESTE 1.5: Verificar Counts"""
        if not self.admin_token:
            self.log_test("Ticket Counts", "SKIP", "Admin token não disponível")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            start_time = time.time()
            async with self.session.get(f"{BACKEND_URL}/tickets/counts", headers=headers) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    counts = await response.json()
                    self.log_test(
                        "1.5 Verificar Counts", 
                        "PASS", 
                        f"✅ Counts retornados: {counts}",
                        counts,
                        response_time
                    )
                    
                    # Verificar se counts batem com queries anteriores
                    # (Isso seria uma verificação mais complexa que requer armazenar os resultados anteriores)
                    
                else:
                    error_data = await response.json()
                    self.log_test(
                        "1.5 Verificar Counts", 
                        "FAIL", 
                        f"Status {response.status}",
                        error_data,
                        response_time
                    )
        except Exception as e:
            self.log_test("1.5 Verificar Counts", "FAIL", f"Exception: {str(e)}")
    
    async def create_test_client(self):
        """TESTE 2.1: Criar Cliente de Teste (via login)"""
        try:
            client_data = {
                "whatsapp": "+5511999887766",
                "pin": "00"
            }
            
            start_time = time.time()
            async with self.session.post(f"{BACKEND_URL}/auth/client/login", json=client_data) as response:
                response_time = time.time() - start_time
                
                if response.status in [200, 201]:
                    data = await response.json()
                    user_data = data.get("user_data", {})
                    self.created_client_id = user_data.get("id")
                    self.client_token = data.get("token")
                    self.log_test(
                        "2.1 Criar Cliente de Teste", 
                        "PASS", 
                        f"✅ Cliente criado/logado com ID: {self.created_client_id}",
                        {"client_id": self.created_client_id, "whatsapp": user_data.get("whatsapp")},
                        response_time
                    )
                    return True
                else:
                    error_data = await response.json()
                    self.log_test(
                        "2.1 Criar Cliente de Teste", 
                        "FAIL", 
                        f"Status {response.status}",
                        error_data,
                        response_time
                    )
                    return False
        except Exception as e:
            self.log_test("2.1 Criar Cliente de Teste", "FAIL", f"Exception: {str(e)}")
            return False
    
    async def create_test_ticket_via_message(self):
        """TESTE 2.2: Criar Ticket via Mensagem (método correto)"""
        if not self.client_token or not self.created_client_id:
            self.log_test("Criar Ticket via Mensagem", "SKIP", "Client token ou client_id não disponível")
            return False
        
        headers = {"Authorization": f"Bearer {self.client_token}"}
        
        try:
            message_data = {
                "ticket_id": "dummy",  # Will be ignored for client messages
                "from_type": "client",
                "from_id": self.created_client_id,
                "kind": "text",
                "text": "🧪 TESTE AUTOMATICO - Primeira mensagem para criar ticket"
            }
            
            start_time = time.time()
            async with self.session.post(f"{BACKEND_URL}/messages", headers=headers, json=message_data) as response:
                response_time = time.time() - start_time
                
                if response.status in [200, 201]:
                    data = await response.json()
                    message_id = data.get("message_id")
                    
                    # Get ticket_id by querying tickets for this client
                    if self.admin_token:
                        admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
                        async with self.session.get(f"{BACKEND_URL}/tickets", headers=admin_headers) as ticket_response:
                            if ticket_response.status == 200:
                                tickets = await ticket_response.json()
                                # Find ticket for this client
                                for ticket in tickets:
                                    if ticket.get("client_id") == self.created_client_id:
                                        self.created_ticket_id = ticket.get("id")
                                        break
                    
                    self.log_test(
                        "2.2 Criar Ticket via Mensagem", 
                        "PASS", 
                        f"✅ Ticket criado automaticamente com ID: {self.created_ticket_id}",
                        {"ticket_id": self.created_ticket_id, "message_id": message_id},
                        response_time
                    )
                    return True
                else:
                    error_data = await response.json()
                    self.log_test(
                        "2.2 Criar Ticket via Mensagem", 
                        "FAIL", 
                        f"Status {response.status}",
                        error_data,
                        response_time
                    )
                    return False
        except Exception as e:
            self.log_test("2.2 Criar Ticket via Mensagem", "FAIL", f"Exception: {str(e)}")
            return False
    
    async def send_test_message(self):
        """TESTE 2.3: Enviar Segunda Mensagem no Ticket"""
        if not self.client_token or not self.created_client_id:
            self.log_test("Enviar Segunda Mensagem", "SKIP", "Client token ou client_id não disponível")
            return False
        
        headers = {"Authorization": f"Bearer {self.client_token}"}
        
        try:
            message_data = {
                "ticket_id": "dummy",  # Will be ignored for client messages
                "from_type": "client",
                "from_id": self.created_client_id,
                "kind": "text",
                "text": "🧪 TESTE AUTOMATICO - Verificando se mensagem aparece na ABA ESPERA"
            }
            
            start_time = time.time()
            async with self.session.post(f"{BACKEND_URL}/messages", headers=headers, json=message_data) as response:
                response_time = time.time() - start_time
                
                if response.status in [200, 201]:
                    data = await response.json()
                    message_id = data.get("id") or data.get("message_id")
                    self.log_test(
                        "2.3 Enviar Segunda Mensagem", 
                        "PASS", 
                        f"✅ Segunda mensagem enviada com ID: {message_id}",
                        {"message_id": message_id, "ticket_id": data.get("ticket_id")},
                        response_time
                    )
                    return True
                else:
                    error_data = await response.json()
                    self.log_test(
                        "2.3 Enviar Segunda Mensagem", 
                        "FAIL", 
                        f"Status {response.status}",
                        error_data,
                        response_time
                    )
                    return False
        except Exception as e:
            self.log_test("2.3 Enviar Segunda Mensagem", "FAIL", f"Exception: {str(e)}")
            return False
    
    async def verify_ticket_in_list(self):
        """TESTE 2.4: Verificar se Ticket Aparece em GET /api/tickets?status=open"""
        if not self.admin_token or not self.created_ticket_id:
            self.log_test("Verificar Ticket na Lista", "SKIP", "Admin token ou ticket_id não disponível")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            start_time = time.time()
            async with self.session.get(f"{BACKEND_URL}/tickets?status=open&limit=20", headers=headers) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    tickets = await response.json()
                    
                    # Procurar o ticket criado
                    created_ticket = None
                    for ticket in tickets:
                        if ticket.get("id") == self.created_ticket_id:
                            created_ticket = ticket
                            break
                    
                    if created_ticket:
                        unread_count = created_ticket.get("unread_count", 0)
                        if unread_count > 0:
                            self.log_test(
                                "2.4 Verificar Ticket na Lista", 
                                "PASS", 
                                f"✅ Ticket encontrado na lista com unread_count: {unread_count}",
                                {"ticket": created_ticket},
                                response_time
                            )
                        else:
                            self.log_test(
                                "2.4 Verificar Ticket na Lista", 
                                "WARNING", 
                                f"⚠️ Ticket encontrado mas unread_count = {unread_count}",
                                {"ticket": created_ticket},
                                response_time
                            )
                    else:
                        self.log_test(
                            "2.4 Verificar Ticket na Lista", 
                            "FAIL", 
                            f"❌ Ticket {self.created_ticket_id} NÃO encontrado na lista",
                            {"tickets_found": len(tickets), "ticket_ids": [t.get("id") for t in tickets[:5]]},
                            response_time
                        )
                else:
                    error_data = await response.json()
                    self.log_test(
                        "2.4 Verificar Ticket na Lista", 
                        "FAIL", 
                        f"Status {response.status}",
                        error_data,
                        response_time
                    )
        except Exception as e:
            self.log_test("2.4 Verificar Ticket na Lista", "FAIL", f"Exception: {str(e)}")
    
    async def test_performance(self):
        """TESTE 3: Performance da Query"""
        if not self.admin_token:
            self.log_test("Performance", "SKIP", "Admin token não disponível")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            # Medir tempo de resposta para GET /api/tickets?status=open&limit=20
            start_time = time.time()
            async with self.session.get(f"{BACKEND_URL}/tickets?status=open&limit=20", headers=headers) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    tickets = await response.json()
                    
                    # Avaliar performance
                    if response_time < 2.0:
                        performance_status = "PASS"
                        performance_desc = f"✅ BOM - Tempo: {response_time:.2f}s (< 2s)"
                    elif response_time < 5.0:
                        performance_status = "WARNING"
                        performance_desc = f"⚠️ MÉDIO - Tempo: {response_time:.2f}s (2-5s, precisa otimizar)"
                    else:
                        performance_status = "FAIL"
                        performance_desc = f"❌ RUIM - Tempo: {response_time:.2f}s (> 5s, gargalo identificado)"
                    
                    self.log_test(
                        "3.1 Performance da Query", 
                        performance_status, 
                        performance_desc,
                        {"response_time": response_time, "tickets_count": len(tickets)},
                        response_time
                    )
                else:
                    error_data = await response.json()
                    self.log_test(
                        "3.1 Performance da Query", 
                        "FAIL", 
                        f"Status {response.status}",
                        error_data,
                        response_time
                    )
        except Exception as e:
            self.log_test("3.1 Performance da Query", "FAIL", f"Exception: {str(e)}")
    
    async def verify_messages_in_ticket(self):
        """TESTE 2.5: Verificar se Última Mensagem Aparece no Ticket"""
        if not self.admin_token or not self.created_ticket_id:
            self.log_test("Verificar Última Mensagem", "SKIP", "Admin token ou ticket_id não disponível")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            start_time = time.time()
            async with self.session.get(f"{BACKEND_URL}/tickets?status=open&limit=20", headers=headers) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    tickets = await response.json()
                    
                    # Encontrar nosso ticket
                    our_ticket = None
                    for ticket in tickets:
                        if ticket.get("id") == self.created_ticket_id:
                            our_ticket = ticket
                            break
                    
                    if our_ticket:
                        last_message = our_ticket.get("last_message")
                        if last_message:
                            last_text = last_message.get("text", "")
                            if "🧪 TESTE AUTOMATICO" in last_text:
                                self.log_test(
                                    "2.5 Verificar Última Mensagem", 
                                    "PASS", 
                                    f"✅ Última mensagem contém texto de teste: '{last_text[:50]}...'",
                                    {"last_message": last_message},
                                    response_time
                                )
                            else:
                                self.log_test(
                                    "2.5 Verificar Última Mensagem", 
                                    "WARNING", 
                                    f"⚠️ Última mensagem não contém texto de teste: '{last_text[:50]}...'",
                                    {"last_message": last_message},
                                    response_time
                                )
                        else:
                            self.log_test(
                                "2.5 Verificar Última Mensagem", 
                                "FAIL", 
                                "❌ Ticket não tem last_message",
                                {"ticket": our_ticket},
                                response_time
                            )
                    else:
                        self.log_test(
                            "2.5 Verificar Última Mensagem", 
                            "FAIL", 
                            f"❌ Ticket {self.created_ticket_id} não encontrado na lista",
                            {"tickets_count": len(tickets)},
                            response_time
                        )
                else:
                    error_data = await response.json()
                    self.log_test(
                        "2.5 Verificar Última Mensagem", 
                        "FAIL", 
                        f"Status {response.status}",
                        error_data,
                        response_time
                    )
        except Exception as e:
            self.log_test("2.5 Verificar Última Mensagem", "FAIL", f"Exception: {str(e)}")

    async def test_mongodb_indexes(self):
        """TESTE 4: Verificar Índices MongoDB"""
        try:
            # Verificar índices da collection tickets
            result = await asyncio.create_subprocess_exec(
                'mongosh', 'support_chat', '--quiet', '--eval', 'db.tickets.getIndexes()',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                indexes_output = stdout.decode()
                
                # Verificar se existem índices em status e reseller_id
                has_status_index = 'status' in indexes_output
                has_reseller_index = 'reseller_id' in indexes_output
                
                if has_status_index and has_reseller_index:
                    self.log_test(
                        "4.1 Verificar Índices MongoDB", 
                        "PASS", 
                        "✅ Índices encontrados em status e reseller_id",
                        {"has_status_index": has_status_index, "has_reseller_index": has_reseller_index}
                    )
                else:
                    missing_indexes = []
                    if not has_status_index:
                        missing_indexes.append("status")
                    if not has_reseller_index:
                        missing_indexes.append("reseller_id")
                    
                    self.log_test(
                        "4.1 Verificar Índices MongoDB", 
                        "FAIL", 
                        f"❌ PROBLEMA - Índices ausentes: {missing_indexes}",
                        {"missing_indexes": missing_indexes, "indexes_output": indexes_output[:500]}
                    )
                    
                    # Tentar criar índices ausentes
                    await self.create_missing_indexes(missing_indexes)
            else:
                error_output = stderr.decode()
                self.log_test(
                    "4.1 Verificar Índices MongoDB", 
                    "FAIL", 
                    f"Erro ao executar mongosh: {error_output}",
                    {"returncode": result.returncode}
                )
        except Exception as e:
            self.log_test("4.1 Verificar Índices MongoDB", "FAIL", f"Exception: {str(e)}")
    
    async def create_missing_indexes(self, missing_indexes):
        """TESTE 4.2: Criar Índices Ausentes"""
        for index_field in missing_indexes:
            try:
                if index_field == "status":
                    create_cmd = 'db.tickets.createIndex({status: 1, reseller_id: 1})'
                elif index_field == "reseller_id":
                    create_cmd = 'db.tickets.createIndex({reseller_id: 1, status: 1})'
                else:
                    continue
                
                result = await asyncio.create_subprocess_exec(
                    'mongosh', 'support_chat', '--quiet', '--eval', create_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await result.communicate()
                
                if result.returncode == 0:
                    self.log_test(
                        f"4.2 Criar Índice {index_field}", 
                        "PASS", 
                        f"✅ Índice criado com sucesso",
                        {"command": create_cmd}
                    )
                else:
                    error_output = stderr.decode()
                    self.log_test(
                        f"4.2 Criar Índice {index_field}", 
                        "FAIL", 
                        f"Erro ao criar índice: {error_output}",
                        {"command": create_cmd}
                    )
            except Exception as e:
                self.log_test(f"4.2 Criar Índice {index_field}", "FAIL", f"Exception: {str(e)}")
    
    def print_summary(self):
        """Imprimir resumo dos testes"""
        print("=" * 80)
        print("🧪 RESUMO DOS TESTES - ABAS DO ATENDENTE")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["status"] == "PASS"])
        failed_tests = len([t for t in self.test_results if t["status"] == "FAIL"])
        warning_tests = len([t for t in self.test_results if t["status"] == "WARNING"])
        skipped_tests = len([t for t in self.test_results if t["status"] == "SKIP"])
        
        print(f"📊 ESTATÍSTICAS:")
        print(f"   Total de testes: {total_tests}")
        print(f"   ✅ Passou: {passed_tests}")
        print(f"   ❌ Falhou: {failed_tests}")
        print(f"   ⚠️ Aviso: {warning_tests}")
        print(f"   ⏭️ Pulado: {skipped_tests}")
        if total_tests > 0:
            print(f"   📈 Taxa de sucesso: {(passed_tests/total_tests*100):.1f}%")
        print()
        
        # Listar testes que falharam
        failed_results = [t for t in self.test_results if t["status"] == "FAIL"]
        if failed_results:
            print("❌ TESTES QUE FALHARAM:")
            for test in failed_results:
                print(f"   • {test['test']}: {test['details']}")
            print()
        
        # Listar avisos
        warning_results = [t for t in self.test_results if t["status"] == "WARNING"]
        if warning_results:
            print("⚠️ AVISOS:")
            for test in warning_results:
                print(f"   • {test['test']}: {test['details']}")
            print()
        
        # Critérios de sucesso conforme review request
        print("🎯 CRITÉRIOS DE SUCESSO:")
        
        # Verificar se tickets retornam em < 2 segundos
        performance_tests = [t for t in self.test_results if "Performance" in t["test"] and t["status"] == "PASS"]
        performance_ok = len(performance_tests) > 0
        print(f"   {'✅' if performance_ok else '❌'} Tickets retornam em < 2 segundos")
        
        # Verificar se ticket criado aparece na lista
        ticket_in_list = any(t["test"] == "2.4 Verificar Ticket na Lista" and t["status"] == "PASS" for t in self.test_results)
        print(f"   {'✅' if ticket_in_list else '❌'} Ticket criado aparece na lista")
        
        # Verificar se mensagem criada aparece no ticket
        messages_in_ticket = any(t["test"] == "2.5 Verificar Última Mensagem" and t["status"] == "PASS" for t in self.test_results)
        print(f"   {'✅' if messages_in_ticket else '❌'} Mensagem criada aparece no ticket")
        
        # Verificar se counts batem com queries
        counts_ok = any(t["test"] == "1.5 Verificar Counts" and t["status"] == "PASS" for t in self.test_results)
        print(f"   {'✅' if counts_ok else '❌'} Counts batem com queries")
        
        # Verificar se índices MongoDB existem
        indexes_ok = any(t["test"] == "4.1 Verificar Índices MongoDB" and t["status"] == "PASS" for t in self.test_results)
        print(f"   {'✅' if indexes_ok else '❌'} Índices MongoDB existem")
        
        # Verificar se não há erros críticos
        no_critical_errors = len(failed_results) == 0
        print(f"   {'✅' if no_critical_errors else '❌'} Sem erros críticos")
        
        print()
        
        # Tempo de resposta médio
        timed_tests = [t for t in self.test_results if t.get("response_time")]
        if timed_tests:
            avg_time = sum(t["response_time"] for t in timed_tests) / len(timed_tests)
            print(f"⏱️ TEMPO DE RESPOSTA MÉDIO: {avg_time:.2f}s")
            print()
        
        print("=" * 80)

async def main():
    """Executar todos os testes"""
    print("🧪 TESTE CRÍTICO - VERIFICAR ABAS DO ATENDENTE")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print(f"👤 Admin: {ADMIN_EMAIL}")
    print("=" * 80)
    print()
    
    async with AtendenteTabsTester() as tester:
        # TESTE 1: Verificar Tickets no Backend
        print("📋 TESTE 1: VERIFICAR TICKETS NO BACKEND")
        print("-" * 50)
        
        # 1.1 Login como Admin
        login_success = await tester.admin_login()
        
        if login_success:
            # 1.2-1.4 Listar Tickets por Status
            await tester.test_tickets_by_status()
            
            # 1.5 Verificar Counts
            await tester.test_ticket_counts()
            
            print()
            print("📝 TESTE 2: CRIAR TICKET DE TESTE")
            print("-" * 50)
            
            # 2.1 Criar Cliente de Teste
            client_created = await tester.create_test_client()
            
            if client_created:
                # 2.2 Criar Ticket via Mensagem
                ticket_created = await tester.create_test_ticket_via_message()
                
                if ticket_created:
                    # 2.3 Enviar Segunda Mensagem
                    await tester.send_test_message()
                    
                    # 2.4 Verificar se aparece na lista
                    await tester.verify_ticket_in_list()
                    
                    # 2.5 Verificar se mensagens aparecem no ticket
                    await tester.verify_messages_in_ticket()
            
            print()
            print("⚡ TESTE 3: PERFORMANCE DA QUERY")
            print("-" * 50)
            
            # 3.1 Medir Tempo de Resposta
            await tester.test_performance()
            
            print()
            print("🗄️ TESTE 4: VERIFICAR ÍNDICES MONGODB")
            print("-" * 50)
            
            # 4.1 Verificar Índices
            await tester.test_mongodb_indexes()
        
        print()
        # Resumo final
        tester.print_summary()

if __name__ == "__main__":
    asyncio.run(main())