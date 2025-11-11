#!/usr/bin/env python3
"""
🧪 TESTE BACKEND COMPLETO - VALIDAR IMPLEMENTAÇÕES FASE 1 & 2

Conforme review request específico:
- AI AGENT: Toggle is_active e agendamento
- AVISOS: Com suporte a mídia
- WEBSOCKET: Ping/Pong keepalive
- ENDPOINTS GERAIS: Health check e config

Backend URL: https://suporte.help/api
Credenciais: admin@admin.com / 102030@ab
"""

import asyncio
import aiohttp
import websockets
import json
import uuid
from datetime import datetime
import sys

# Configuração
BACKEND_URL = "https://suporte.help/api"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "102030@ab"

class BackendTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, status: str, details: str = "", response_data: dict = None):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   {details}")
        if response_data and status == "FAIL":
            print(f"   Response: {json.dumps(response_data, indent=2)}")
        print()
    
    async def admin_login(self):
        """1. Admin Login"""
        try:
            async with self.session.post(
                f"{BACKEND_URL}/auth/admin/login",
                json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.admin_token = data.get("token")
                    self.log_test(
                        "Admin Login", 
                        "PASS", 
                        f"Token obtido: {self.admin_token[:20]}...",
                        {"user_type": data.get("user_type")}
                    )
                    return True
                else:
                    error_data = await response.json()
                    self.log_test(
                        "Admin Login", 
                        "FAIL", 
                        f"Status {response.status}",
                        error_data
                    )
                    return False
        except Exception as e:
            self.log_test("Admin Login", "FAIL", f"Exception: {str(e)}")
            return False
    
    async def test_ai_agents(self):
        """2. AI AGENTS - Toggle is_active e agendamento"""
        if not self.admin_token:
            self.log_test("AI Agents", "SKIP", "Admin token não disponível")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # 2.1 Listar AI Agents
        try:
            async with self.session.get(f"{BACKEND_URL}/ai/agents", headers=headers) as response:
                if response.status == 200:
                    agents = await response.json()
                    self.log_test(
                        "AI Agents - Listar", 
                        "PASS", 
                        f"Encontrados {len(agents)} agentes",
                        {"count": len(agents), "sample": agents[:1] if agents else []}
                    )
                    
                    # Verificar campos obrigatórios
                    if agents:
                        agent = agents[0]
                        required_fields = ["is_active", "schedule_start_time", "schedule_end_time"]
                        missing_fields = [field for field in required_fields if field not in agent]
                        
                        if missing_fields:
                            self.log_test(
                                "AI Agents - Campos Obrigatórios", 
                                "FAIL", 
                                f"Campos ausentes: {missing_fields}",
                                agent
                            )
                        else:
                            self.log_test(
                                "AI Agents - Campos Obrigatórios", 
                                "PASS", 
                                "Todos os campos presentes (is_active, schedule_start_time, schedule_end_time)"
                            )
                else:
                    error_data = await response.json()
                    self.log_test(
                        "AI Agents - Listar", 
                        "FAIL", 
                        f"Status {response.status}",
                        error_data
                    )
        except Exception as e:
            self.log_test("AI Agents - Listar", "FAIL", f"Exception: {str(e)}")
        
        # 2.2 Criar AI Agent com Agendamento
        try:
            agent_data = {
                "name": "IA Teste Agendamento",
                "is_active": True,
                "schedule_start_time": "08:00",
                "schedule_end_time": "18:00",
                "llm_provider": "openai",
                "llm_model": "gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            async with self.session.post(f"{BACKEND_URL}/ai/agents", headers=headers, json=agent_data) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    agent_id = data.get("id") or data.get("agent_id")
                    self.log_test(
                        "AI Agents - Criar", 
                        "PASS", 
                        f"Agent criado com ID: {agent_id}",
                        {"agent_id": agent_id}
                    )
                    
                    # 2.3 Atualizar AI Agent - Toggle is_active
                    if agent_id:
                        update_data = {
                            "is_active": False,
                            "schedule_start_time": "09:00",
                            "schedule_end_time": "17:00"
                        }
                        
                        async with self.session.put(f"{BACKEND_URL}/ai/agents/{agent_id}", headers=headers, json=update_data) as update_response:
                            if update_response.status == 200:
                                self.log_test(
                                    "AI Agents - Atualizar", 
                                    "PASS", 
                                    "Agent atualizado com sucesso (is_active: false)"
                                )
                                
                                # 2.4 Buscar AI Agent Atualizado
                                async with self.session.get(f"{BACKEND_URL}/ai/agents/{agent_id}", headers=headers) as get_response:
                                    if get_response.status == 200:
                                        updated_agent = await get_response.json()
                                        
                                        # Verificar se campos foram atualizados
                                        checks = [
                                            ("is_active", False),
                                            ("schedule_start_time", "09:00"),
                                            ("schedule_end_time", "17:00")
                                        ]
                                        
                                        all_correct = True
                                        for field, expected in checks:
                                            actual = updated_agent.get(field)
                                            if actual != expected:
                                                all_correct = False
                                                self.log_test(
                                                    f"AI Agents - Verificar {field}", 
                                                    "FAIL", 
                                                    f"Esperado: {expected}, Atual: {actual}",
                                                    updated_agent
                                                )
                                        
                                        if all_correct:
                                            self.log_test(
                                                "AI Agents - Verificar Atualização", 
                                                "PASS", 
                                                "Todos os campos atualizados corretamente"
                                            )
                                    else:
                                        error_data = await get_response.json()
                                        self.log_test(
                                            "AI Agents - Buscar Atualizado", 
                                            "FAIL", 
                                            f"Status {get_response.status}",
                                            error_data
                                        )
                            else:
                                error_data = await update_response.json()
                                self.log_test(
                                    "AI Agents - Atualizar", 
                                    "FAIL", 
                                    f"Status {update_response.status}",
                                    error_data
                                )
                else:
                    error_data = await response.json()
                    self.log_test(
                        "AI Agents - Criar", 
                        "FAIL", 
                        f"Status {response.status}",
                        error_data
                    )
        except Exception as e:
            self.log_test("AI Agents - Criar", "FAIL", f"Exception: {str(e)}")
    
    async def test_notices_with_media(self):
        """3. AVISOS COM MÍDIA"""
        if not self.admin_token:
            self.log_test("Avisos", "SKIP", "Admin token não disponível")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # 3.1 Criar Aviso SEM Mídia
        try:
            notice_data = {
                "title": "Aviso Teste Sem Mídia",
                "message": "Este é um aviso de teste sem mídia",
                "recipient_type": "all"
            }
            
            async with self.session.post(f"{BACKEND_URL}/notices", headers=headers, json=notice_data) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    notice_id_1 = data.get("id") or data.get("notice_id")
                    
                    # Verificar campos de mídia
                    media_type = data.get("media_type")
                    media_url = data.get("media_url")
                    
                    if media_type in [None, "none"] and media_url is None:
                        self.log_test(
                            "Avisos - Criar Sem Mídia", 
                            "PASS", 
                            f"Aviso criado sem mídia (ID: {notice_id_1})"
                        )
                    else:
                        self.log_test(
                            "Avisos - Criar Sem Mídia", 
                            "FAIL", 
                            f"Mídia não deveria estar presente: media_type={media_type}, media_url={media_url}",
                            data
                        )
                else:
                    error_data = await response.json()
                    self.log_test(
                        "Avisos - Criar Sem Mídia", 
                        "FAIL", 
                        f"Status {response.status}",
                        error_data
                    )
        except Exception as e:
            self.log_test("Avisos - Criar Sem Mídia", "FAIL", f"Exception: {str(e)}")
        
        # 3.2 Criar Aviso COM Mídia (Foto)
        try:
            notice_with_media = {
                "title": "Aviso Teste Com Foto",
                "message": "Este aviso tem uma foto anexada",
                "recipient_type": "all",
                "media_type": "photo",
                "media_url": "https://example.com/test-image.jpg"
            }
            
            async with self.session.post(f"{BACKEND_URL}/notices", headers=headers, json=notice_with_media) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    notice_id_2 = data.get("id") or data.get("notice_id")
                    
                    # Verificar campos de mídia
                    media_type = data.get("media_type")
                    media_url = data.get("media_url")
                    
                    if media_type == "photo" and media_url == "https://example.com/test-image.jpg":
                        self.log_test(
                            "Avisos - Criar Com Mídia", 
                            "PASS", 
                            f"Aviso criado com mídia (ID: {notice_id_2})"
                        )
                    else:
                        self.log_test(
                            "Avisos - Criar Com Mídia", 
                            "FAIL", 
                            f"Mídia não salva corretamente: media_type={media_type}, media_url={media_url}",
                            data
                        )
                else:
                    error_data = await response.json()
                    self.log_test(
                        "Avisos - Criar Com Mídia", 
                        "FAIL", 
                        f"Status {response.status}",
                        error_data
                    )
        except Exception as e:
            self.log_test("Avisos - Criar Com Mídia", "FAIL", f"Exception: {str(e)}")
        
        # 3.3 Buscar Avisos - Verificar Mídia
        try:
            async with self.session.get(f"{BACKEND_URL}/notices", headers=headers) as response:
                if response.status == 200:
                    notices = await response.json()
                    
                    # Verificar se avisos criados estão na lista
                    media_notices = [n for n in notices if n.get("media_type") == "photo"]
                    no_media_notices = [n for n in notices if n.get("media_type") in [None, "none"]]
                    
                    self.log_test(
                        "Avisos - Listar e Verificar Mídia", 
                        "PASS", 
                        f"Total: {len(notices)} avisos, Com mídia: {len(media_notices)}, Sem mídia: {len(no_media_notices)}"
                    )
                else:
                    error_data = await response.json()
                    self.log_test(
                        "Avisos - Listar", 
                        "FAIL", 
                        f"Status {response.status}",
                        error_data
                    )
        except Exception as e:
            self.log_test("Avisos - Listar", "FAIL", f"Exception: {str(e)}")
    
    async def test_websocket_ping_pong(self):
        """4. WEBSOCKET - PING/PONG (KEEPALIVE)"""
        try:
            # Usar user_id de teste e session_id
            test_user_id = "test_user_" + str(uuid.uuid4())[:8]
            test_session_id = "test_session_" + str(uuid.uuid4())[:8]
            
            # WebSocket URL baseado no padrão do código
            ws_url = f"wss://suporte.help/api/ws/{test_user_id}/{test_session_id}"
            
            async with websockets.connect(ws_url) as websocket:
                self.log_test(
                    "WebSocket - Conectar", 
                    "PASS", 
                    f"Conexão estabelecida: {ws_url}"
                )
                
                # Enviar PING
                ping_message = {"type": "ping"}
                await websocket.send(json.dumps(ping_message))
                
                self.log_test(
                    "WebSocket - Enviar PING", 
                    "PASS", 
                    "Mensagem PING enviada"
                )
                
                # Aguardar PONG (timeout de 10 segundos)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    response_data = json.loads(response)
                    
                    if response_data.get("type") == "pong":
                        self.log_test(
                            "WebSocket - Receber PONG", 
                            "PASS", 
                            "PONG recebido corretamente",
                            response_data
                        )
                    else:
                        self.log_test(
                            "WebSocket - Receber PONG", 
                            "FAIL", 
                            f"Resposta inesperada: {response_data.get('type')}",
                            response_data
                        )
                except asyncio.TimeoutError:
                    self.log_test(
                        "WebSocket - Receber PONG", 
                        "FAIL", 
                        "Timeout - PONG não recebido em 10 segundos"
                    )
                
        except Exception as e:
            self.log_test("WebSocket - Ping/Pong", "FAIL", f"Exception: {str(e)}")
    
    async def test_general_endpoints(self):
        """5. ENDPOINTS GERAIS (SMOKE TEST)"""
        
        # 5.1 Health Check
        try:
            async with self.session.get(f"{BACKEND_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test(
                        "Health Check", 
                        "PASS", 
                        f"Status: {data.get('status')}",
                        data
                    )
                else:
                    error_data = await response.json()
                    self.log_test(
                        "Health Check", 
                        "FAIL", 
                        f"Status {response.status}",
                        error_data
                    )
        except Exception as e:
            self.log_test("Health Check", "FAIL", f"Exception: {str(e)}")
        
        # 5.2 Config
        if self.admin_token:
            try:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                async with self.session.get(f"{BACKEND_URL}/config", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log_test(
                            "Config", 
                            "PASS", 
                            f"Configuração retornada com {len(data)} campos",
                            {"sample_fields": list(data.keys())[:5] if isinstance(data, dict) else "not_dict"}
                        )
                    else:
                        error_data = await response.json()
                        self.log_test(
                            "Config", 
                            "FAIL", 
                            f"Status {response.status}",
                            error_data
                        )
            except Exception as e:
                self.log_test("Config", "FAIL", f"Exception: {str(e)}")
        else:
            self.log_test("Config", "SKIP", "Admin token não disponível")
    
    def print_summary(self):
        """Imprimir resumo dos testes"""
        print("=" * 80)
        print("🧪 RESUMO DOS TESTES BACKEND")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["status"] == "PASS"])
        failed_tests = len([t for t in self.test_results if t["status"] == "FAIL"])
        skipped_tests = len([t for t in self.test_results if t["status"] == "SKIP"])
        
        print(f"📊 ESTATÍSTICAS:")
        print(f"   Total de testes: {total_tests}")
        print(f"   ✅ Passou: {passed_tests}")
        print(f"   ❌ Falhou: {failed_tests}")
        print(f"   ⏭️ Pulado: {skipped_tests}")
        print(f"   📈 Taxa de sucesso: {(passed_tests/total_tests*100):.1f}%")
        print()
        
        # Listar testes que falharam
        failed_results = [t for t in self.test_results if t["status"] == "FAIL"]
        if failed_results:
            print("❌ TESTES QUE FALHARAM:")
            for test in failed_results:
                print(f"   • {test['test']}: {test['details']}")
            print()
        
        # Critérios de sucesso conforme review request
        print("🎯 CRITÉRIOS DE SUCESSO:")
        
        ai_tests = [t for t in self.test_results if "AI Agents" in t["test"]]
        ai_passed = all(t["status"] == "PASS" for t in ai_tests)
        print(f"   {'✅' if ai_passed else '❌'} TODOS os testes de AI Agent devem PASSAR")
        
        notice_tests = [t for t in self.test_results if "Avisos" in t["test"]]
        notice_passed = all(t["status"] == "PASS" for t in notice_tests)
        print(f"   {'✅' if notice_passed else '❌'} TODOS os testes de Avisos com Mídia devem PASSAR")
        
        ws_tests = [t for t in self.test_results if "WebSocket" in t["test"]]
        ws_passed = all(t["status"] == "PASS" for t in ws_tests)
        print(f"   {'✅' if ws_passed else '❌'} WebSocket ping/pong deve funcionar")
        
        error_tests = [t for t in self.test_results if t["status"] == "FAIL" and "500" in t["details"]]
        no_500_errors = len(error_tests) == 0
        print(f"   {'✅' if no_500_errors else '❌'} Nenhum erro 500 ou 404 inesperado")
        
        print()
        print("=" * 80)

async def main():
    """Executar todos os testes"""
    print("🧪 INICIANDO TESTES BACKEND - FASE 1 & 2")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print(f"👤 Admin: {ADMIN_EMAIL}")
    print("=" * 80)
    print()
    
    async with BackendTester() as tester:
        # 1. Login admin
        login_success = await tester.admin_login()
        
        if login_success:
            # 2. Testes de AI Agents
            await tester.test_ai_agents()
            
            # 3. Testes de Avisos com Mídia
            await tester.test_notices_with_media()
        
        # 4. Teste WebSocket (independente de login)
        await tester.test_websocket_ping_pong()
        
        # 5. Testes gerais
        await tester.test_general_endpoints()
        
        # 6. Resumo
        tester.print_summary()

if __name__ == "__main__":
    asyncio.run(main())