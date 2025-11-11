#!/usr/bin/env python3
"""
🧪 TESTE COMPLETO E SISTEMÁTICO - TODAS AS 16 ABAS DO ADMIN DASHBOARD

OBJETIVO: Testar TODAS as abas do Admin Dashboard, aba por aba, fazendo:
1. Criar/Configurar dados de teste
2. Salvar (POST/PUT)
3. Recarregar dados (GET)
4. Verificar persistência no MongoDB
5. Testar update
6. Testar delete (quando aplicável)

CREDENCIAIS: admin@admin.com / 102030@ab
BACKEND URL: https://wppconnect-fix.preview.emergentagent.com/api
"""

import asyncio
import aiohttp
import json
import uuid
from datetime import datetime, timezone
import time

# Configurações
BACKEND_URL = "https://wppconnect-fix.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "102030@ab"

class AdminDashboardTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.test_results = {}
        
    async def setup(self):
        """Configurar sessão HTTP e fazer login admin"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(ssl=False)
        )
        
        print("🔑 Fazendo login como admin...")
        await self.admin_login()
        
    async def cleanup(self):
        """Limpar recursos"""
        if self.session:
            await self.session.close()
            
    async def admin_login(self):
        """Login como admin"""
        try:
            async with self.session.post(f"{BACKEND_URL}/auth/admin/login", json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }) as response:
                if response.status == 200:
                    data = await response.json()
                    self.admin_token = data["token"]
                    print(f"✅ Admin login successful: {ADMIN_EMAIL}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Admin login failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Admin login error: {e}")
            return False
            
    def get_headers(self):
        """Headers com token de autenticação"""
        return {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
        
    async def test_get_endpoint(self, endpoint, description):
        """Testa endpoint GET"""
        try:
            async with self.session.get(f"{BACKEND_URL}{endpoint}", headers=self.get_headers()) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"  ✅ GET {endpoint} - {description}")
                    return data
                else:
                    error_text = await response.text()
                    print(f"  ❌ GET {endpoint} - Status: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"  ❌ GET {endpoint} - Error: {e}")
            return None
            
    async def test_post_endpoint(self, endpoint, data, description):
        """Testa endpoint POST"""
        try:
            async with self.session.post(f"{BACKEND_URL}{endpoint}", json=data, headers=self.get_headers()) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    print(f"  ✅ POST {endpoint} - {description}")
                    return result
                else:
                    error_text = await response.text()
                    print(f"  ❌ POST {endpoint} - Status: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"  ❌ POST {endpoint} - Error: {e}")
            return None
            
    async def test_put_endpoint(self, endpoint, data, description):
        """Testa endpoint PUT"""
        try:
            async with self.session.put(f"{BACKEND_URL}{endpoint}", json=data, headers=self.get_headers()) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"  ✅ PUT {endpoint} - {description}")
                    return result
                else:
                    error_text = await response.text()
                    print(f"  ❌ PUT {endpoint} - Status: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"  ❌ PUT {endpoint} - Error: {e}")
            return None
            
    async def test_delete_endpoint(self, endpoint, description):
        """Testa endpoint DELETE"""
        try:
            async with self.session.delete(f"{BACKEND_URL}{endpoint}", headers=self.get_headers()) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"  ✅ DELETE {endpoint} - {description}")
                    return result
                else:
                    error_text = await response.text()
                    print(f"  ❌ DELETE {endpoint} - Status: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"  ❌ DELETE {endpoint} - Error: {e}")
            return None

    async def test_aba_1_dashboard_avisos(self):
        """ABA 1: DASHBOARD (AVISOS)"""
        print("\n" + "="*80)
        print("🧪 ABA 1: DASHBOARD (AVISOS)")
        print("="*80)
        
        results = {
            "get_notices": False,
            "post_notice": False,
            "put_notice": False,
            "delete_notice": False,
            "persistence": False
        }
        
        # 1. GET /api/notices
        notices = await self.test_get_endpoint("/notices", "Listar avisos")
        if notices is not None:
            results["get_notices"] = True
            
        # 2. POST /api/notices
        notice_data = {
            "title": "Teste Sistemático - Aviso de Manutenção",
            "message": "Sistema em manutenção programada das 02:00 às 04:00. Pedimos desculpas pelo inconveniente.",
            "type": "warning"
        }
        
        created_notice = await self.test_post_endpoint("/notices", notice_data, "Criar aviso")
        notice_id = None
        if created_notice and created_notice.get("id"):
            results["post_notice"] = True
            notice_id = created_notice["id"]
            print(f"    📋 Notice ID criado: {notice_id}")
            
        # 3. PUT /api/notices/{id}
        if notice_id:
            update_data = {
                "title": "Teste Sistemático - Aviso ATUALIZADO",
                "message": "Manutenção CONCLUÍDA com sucesso. Sistema funcionando normalmente.",
                "type": "info"
            }
            updated_notice = await self.test_put_endpoint(f"/notices/{notice_id}", update_data, "Atualizar aviso")
            if updated_notice:
                results["put_notice"] = True
                
        # 4. Verificar persistência
        updated_notices = await self.test_get_endpoint("/notices", "Verificar persistência")
        if updated_notices:
            found_notice = next((n for n in updated_notices if n.get("id") == notice_id), None)
            if found_notice and found_notice.get("title") == "Teste Sistemático - Aviso ATUALIZADO":
                results["persistence"] = True
                print(f"    ✅ Persistência verificada: Aviso atualizado encontrado")
                
        # 5. DELETE /api/notices/{id}
        if notice_id:
            deleted = await self.test_delete_endpoint(f"/notices/{notice_id}", "Deletar aviso")
            if deleted:
                results["delete_notice"] = True
                
        self.test_results["aba_1_avisos"] = results
        success_rate = sum(results.values()) / len(results) * 100
        status = "✅ FUNCIONAL" if success_rate >= 80 else "⚠️ PARCIAL" if success_rate >= 50 else "❌ COM ERROS"
        print(f"\n📊 ABA 1 - Status: {status} ({success_rate:.1f}% dos testes passaram)")
        
    async def test_aba_2_dominio(self):
        """ABA 2: DOMÍNIO"""
        print("\n" + "="*80)
        print("🧪 ABA 2: DOMÍNIO")
        print("="*80)
        
        results = {
            "get_admin_domain_config": False,
            "post_admin_domain_config": False,
            "get_reseller_domain_info": False,
            "post_reseller_update_domain": False
        }
        
        # 1. GET /api/admin/domain-config
        domain_config = await self.test_get_endpoint("/admin/domain-config", "Obter configuração de domínio admin")
        if domain_config is not None:
            results["get_admin_domain_config"] = True
            
        # 2. POST /api/admin/domain-config
        config_data = {
            "mainDomain": "whatsapp-livechat.preview.emergentagent.com",
            "paths": {
                "admin": "/admin",
                "agent": "/atendente", 
                "client": "/chat",
                "vendas": "/vendas"
            }
        }
        
        updated_config = await self.test_post_endpoint("/admin/domain-config", config_data, "Atualizar configuração de domínio")
        if updated_config:
            results["post_admin_domain_config"] = True
            
        # 3. GET /api/reseller/domain-info (precisa de reseller token)
        # Vamos tentar com admin token mesmo
        domain_info = await self.test_get_endpoint("/reseller/domain-info", "Obter info de domínio reseller")
        if domain_info is not None:
            results["get_reseller_domain_info"] = True
            
        # 4. POST /api/reseller/update-domain
        update_domain_data = {
            "custom_domain": "teste-sistematico.example.com"
        }
        
        updated_domain = await self.test_post_endpoint("/reseller/update-domain", update_domain_data, "Atualizar domínio customizado")
        if updated_domain:
            results["post_reseller_update_domain"] = True
            
        self.test_results["aba_2_dominio"] = results
        success_rate = sum(results.values()) / len(results) * 100
        status = "✅ FUNCIONAL" if success_rate >= 80 else "⚠️ PARCIAL" if success_rate >= 50 else "❌ COM ERROS"
        print(f"\n📊 ABA 2 - Status: {status} ({success_rate:.1f}% dos testes passaram)")

    async def test_aba_3_revendas(self):
        """ABA 3: REVENDAS"""
        print("\n" + "="*80)
        print("🧪 ABA 3: REVENDAS")
        print("="*80)
        
        results = {
            "get_resellers": False,
            "post_reseller": False,
            "get_reseller_by_id": False,
            "put_reseller": False,
            "get_hierarchy": False,
            "delete_reseller": False
        }
        
        # 1. GET /api/resellers
        resellers = await self.test_get_endpoint("/resellers", "Listar revendas")
        if resellers is not None:
            results["get_resellers"] = True
            
        # 2. POST /api/resellers
        reseller_data = {
            "name": "Revenda Teste Sistemático",
            "email": f"teste-sistematico-{int(time.time())}@example.com",
            "password": "teste123",
            "custom_domain": f"teste-{int(time.time())}.example.com"
        }
        
        created_reseller = await self.test_post_endpoint("/resellers", reseller_data, "Criar revenda")
        reseller_id = None
        if created_reseller and created_reseller.get("id"):
            results["post_reseller"] = True
            reseller_id = created_reseller["id"]
            print(f"    📋 Reseller ID criado: {reseller_id}")
            
        # 3. GET /api/resellers/{id}
        if reseller_id:
            reseller_info = await self.test_get_endpoint(f"/resellers/{reseller_id}", "Obter info da revenda")
            if reseller_info:
                results["get_reseller_by_id"] = True
                
        # 4. PUT /api/resellers/{id}
        if reseller_id:
            update_data = {
                "name": "Revenda Teste ATUALIZADA",
                "email": reseller_data["email"],  # Manter mesmo email
                "custom_domain": f"teste-atualizado-{int(time.time())}.example.com"
            }
            updated_reseller = await self.test_put_endpoint(f"/resellers/{reseller_id}", update_data, "Atualizar revenda")
            if updated_reseller:
                results["put_reseller"] = True
                
        # 5. GET /api/resellers/hierarchy
        hierarchy = await self.test_get_endpoint("/resellers/hierarchy", "Visualizar hierarquia")
        if hierarchy is not None:
            results["get_hierarchy"] = True
            
        # 6. DELETE /api/resellers/{id}
        if reseller_id:
            deleted = await self.test_delete_endpoint(f"/resellers/{reseller_id}", "Deletar revenda")
            if deleted:
                results["delete_reseller"] = True
                
        self.test_results["aba_3_revendas"] = results
        success_rate = sum(results.values()) / len(results) * 100
        status = "✅ FUNCIONAL" if success_rate >= 80 else "⚠️ PARCIAL" if success_rate >= 50 else "❌ COM ERROS"
        print(f"\n📊 ABA 3 - Status: {status} ({success_rate:.1f}% dos testes passaram)")

    async def test_aba_4_atendentes(self):
        """ABA 4: ATENDENTES"""
        print("\n" + "="*80)
        print("🧪 ABA 4: ATENDENTES")
        print("="*80)
        
        results = {
            "get_agents": False,
            "post_agent": False,
            "put_agent": False,
            "delete_agent": False,
            "agent_login": False
        }
        
        # 1. GET /api/agents
        agents = await self.test_get_endpoint("/agents", "Listar atendentes")
        if agents is not None:
            results["get_agents"] = True
            
        # 2. POST /api/agents
        agent_data = {
            "name": "Atendente Teste Sistemático",
            "username": f"teste-sistematico-{int(time.time())}",
            "password": "teste123",
            "department_ids": []
        }
        
        created_agent = await self.test_post_endpoint("/agents", agent_data, "Criar atendente")
        agent_id = None
        if created_agent and created_agent.get("id"):
            results["post_agent"] = True
            agent_id = created_agent["id"]
            print(f"    📋 Agent ID criado: {agent_id}")
            
        # 3. PUT /api/agents/{id}
        if agent_id:
            update_data = {
                "name": "Atendente Teste ATUALIZADO",
                "username": agent_data["username"],  # Manter mesmo username
                "department_ids": []
            }
            updated_agent = await self.test_put_endpoint(f"/agents/{agent_id}", update_data, "Atualizar atendente")
            if updated_agent:
                results["put_agent"] = True
                
        # 4. Testar login do atendente
        try:
            async with self.session.post(f"{BACKEND_URL}/auth/agent/login", json={
                "login": agent_data["username"],
                "password": agent_data["password"]
            }) as response:
                if response.status == 200:
                    results["agent_login"] = True
                    print(f"  ✅ Login atendente funcionando")
                else:
                    print(f"  ❌ Login atendente falhou: {response.status}")
        except Exception as e:
            print(f"  ❌ Erro no login atendente: {e}")
            
        # 5. DELETE /api/agents/{id}
        if agent_id:
            deleted = await self.test_delete_endpoint(f"/agents/{agent_id}", "Deletar atendente")
            if deleted:
                results["delete_agent"] = True
                
        self.test_results["aba_4_atendentes"] = results
        success_rate = sum(results.values()) / len(results) * 100
        status = "✅ FUNCIONAL" if success_rate >= 80 else "⚠️ PARCIAL" if success_rate >= 50 else "❌ COM ERROS"
        print(f"\n📊 ABA 4 - Status: {status} ({success_rate:.1f}% dos testes passaram)")

    async def test_aba_5_ia_departamentos(self):
        """ABA 5: I.A / DEPARTAMENTOS"""
        print("\n" + "="*80)
        print("🧪 ABA 5: I.A / DEPARTAMENTOS")
        print("="*80)
        
        results = {
            "get_departments": False,
            "post_department": False,
            "put_department": False,
            "delete_department": False,
            "get_ai_agents": False,
            "post_ai_agent": False,
            "put_ai_agent": False,
            "delete_ai_agent": False
        }
        
        # DEPARTAMENTOS
        # 1. GET /api/ai/departments
        departments = await self.test_get_endpoint("/ai/departments", "Listar departamentos")
        if departments is not None:
            results["get_departments"] = True
            
        # 2. POST /api/ai/departments
        dept_data = {
            "name": "Departamento Teste Sistemático",
            "description": "Departamento criado para teste sistemático",
            "origin": "wa_suporte",
            "ai_enabled": True
        }
        
        created_dept = await self.test_post_endpoint("/ai/departments", dept_data, "Criar departamento")
        dept_id = None
        if created_dept and created_dept.get("id"):
            results["post_department"] = True
            dept_id = created_dept["id"]
            print(f"    📋 Department ID criado: {dept_id}")
            
        # 3. PUT /api/ai/departments/{id}
        if dept_id:
            update_data = {
                "name": "Departamento Teste ATUALIZADO",
                "description": "Departamento atualizado no teste sistemático",
                "origin": "wa_suporte",
                "ai_enabled": False
            }
            updated_dept = await self.test_put_endpoint(f"/ai/departments/{dept_id}", update_data, "Atualizar departamento")
            if updated_dept:
                results["put_department"] = True
                
        # AGENTES IA
        # 4. GET /api/ai/agents
        ai_agents = await self.test_get_endpoint("/ai/agents", "Listar agentes IA")
        if ai_agents is not None:
            results["get_ai_agents"] = True
            
        # 5. POST /api/ai/agents
        ai_agent_data = {
            "name": "IA Teste Sistemático",
            "personality": "Assistente prestativo e educado para testes",
            "instructions": "Responda sempre de forma clara e objetiva durante os testes",
            "llm_provider": "openai",
            "llm_model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 500,
            "is_active": True
        }
        
        created_ai = await self.test_post_endpoint("/ai/agents", ai_agent_data, "Criar agente IA")
        ai_id = None
        if created_ai and created_ai.get("id"):
            results["post_ai_agent"] = True
            ai_id = created_ai["id"]
            print(f"    📋 AI Agent ID criado: {ai_id}")
            
        # 6. PUT /api/ai/agents/{id}
        if ai_id:
            update_ai_data = {
                "name": "IA Teste ATUALIZADA",
                "personality": "Assistente atualizado para testes sistemáticos",
                "instructions": "Instruções atualizadas para teste",
                "llm_provider": "openai",
                "llm_model": "gpt-4",
                "temperature": 0.5,
                "max_tokens": 1000,
                "is_active": True
            }
            updated_ai = await self.test_put_endpoint(f"/ai/agents/{ai_id}", update_ai_data, "Atualizar agente IA")
            if updated_ai:
                results["put_ai_agent"] = True
                
        # 7. Vincular IA ao departamento (se ambos existem)
        if dept_id and ai_id:
            link_data = {
                "name": "Departamento Teste ATUALIZADO",
                "description": "Departamento com IA vinculada",
                "origin": "wa_suporte",
                "ai_enabled": True,
                "ai_agent_id": ai_id
            }
            await self.test_put_endpoint(f"/ai/departments/{dept_id}", link_data, "Vincular IA ao departamento")
            
        # 8. DELETE /api/ai/agents/{id}
        if ai_id:
            deleted_ai = await self.test_delete_endpoint(f"/ai/agents/{ai_id}", "Deletar agente IA")
            if deleted_ai:
                results["delete_ai_agent"] = True
                
        # 9. DELETE /api/ai/departments/{id}
        if dept_id:
            deleted_dept = await self.test_delete_endpoint(f"/ai/departments/{dept_id}", "Deletar departamento")
            if deleted_dept:
                results["delete_department"] = True
                
        self.test_results["aba_5_ia_departamentos"] = results
        success_rate = sum(results.values()) / len(results) * 100
        status = "✅ FUNCIONAL" if success_rate >= 80 else "⚠️ PARCIAL" if success_rate >= 50 else "❌ COM ERROS"
        print(f"\n📊 ABA 5 - Status: {status} ({success_rate:.1f}% dos testes passaram)")

    async def test_aba_6_msg_rapidas(self):
        """ABA 6: MSG RÁPIDAS"""
        print("\n" + "="*80)
        print("🧪 ABA 6: MSG RÁPIDAS")
        print("="*80)
        
        results = {
            "get_config": False,
            "put_config_quick_blocks": False,
            "persistence_check": False
        }
        
        # 1. GET /api/config
        config = await self.test_get_endpoint("/config", "Obter configuração atual")
        if config is not None:
            results["get_config"] = True
            
        # 2. PUT /api/config com quick_blocks
        quick_blocks_data = {
            "quick_blocks": [
                {
                    "id": str(uuid.uuid4()),
                    "title": "Saudação",
                    "message": "Olá! Como posso ajudá-lo hoje?"
                },
                {
                    "id": str(uuid.uuid4()),
                    "title": "Horário de Funcionamento",
                    "message": "Nosso horário de atendimento é de segunda a sexta, das 8h às 18h."
                },
                {
                    "id": str(uuid.uuid4()),
                    "title": "Suporte Técnico",
                    "message": "Para suporte técnico, por favor informe o modelo do seu aparelho e descreva o problema."
                }
            ]
        }
        
        # Manter outros campos da config se existirem
        if config:
            config.update(quick_blocks_data)
            update_data = config
        else:
            update_data = quick_blocks_data
            
        updated_config = await self.test_put_endpoint("/config", update_data, "Salvar mensagens rápidas")
        if updated_config:
            results["put_config_quick_blocks"] = True
            
        # 3. Verificar persistência
        reloaded_config = await self.test_get_endpoint("/config", "Verificar persistência das mensagens rápidas")
        if reloaded_config and reloaded_config.get("quick_blocks"):
            if len(reloaded_config["quick_blocks"]) == 3:
                results["persistence_check"] = True
                print(f"    ✅ Persistência verificada: {len(reloaded_config['quick_blocks'])} mensagens rápidas salvas")
                
        self.test_results["aba_6_msg_rapidas"] = results
        success_rate = sum(results.values()) / len(results) * 100
        status = "✅ FUNCIONAL" if success_rate >= 80 else "⚠️ PARCIAL" if success_rate >= 50 else "❌ COM ERROS"
        print(f"\n📊 ABA 6 - Status: {status} ({success_rate:.1f}% dos testes passaram)")

    async def test_aba_7_dados_permitidos(self):
        """ABA 7: DADOS PERMITIDOS"""
        print("\n" + "="*80)
        print("🧪 ABA 7: DADOS PERMITIDOS")
        print("="*80)
        
        results = {
            "get_config": False,
            "put_config_allowed_data": False,
            "persistence_check": False
        }
        
        # 1. GET /api/config
        config = await self.test_get_endpoint("/config", "Obter configuração atual")
        if config is not None:
            results["get_config"] = True
            
        # 2. PUT /api/config com allowed_data
        allowed_data = {
            "allowed_data": {
                "cpfs": ["123.456.789-00", "987.654.321-00"],
                "emails": ["teste@example.com", "admin@teste.com"],
                "phones": ["11999999999", "11888888888"],
                "random_keys": ["12345678-1234-1234-1234-123456789abc", "87654321-4321-4321-4321-cba987654321"]
            }
        }
        
        # Manter outros campos da config se existirem
        if config:
            config.update(allowed_data)
            update_data = config
        else:
            update_data = allowed_data
            
        updated_config = await self.test_put_endpoint("/config", update_data, "Salvar dados permitidos")
        if updated_config:
            results["put_config_allowed_data"] = True
            
        # 3. Verificar persistência
        reloaded_config = await self.test_get_endpoint("/config", "Verificar persistência dos dados permitidos")
        if reloaded_config and reloaded_config.get("allowed_data"):
            allowed = reloaded_config["allowed_data"]
            if (allowed.get("cpfs") and allowed.get("emails") and 
                allowed.get("phones") and allowed.get("random_keys")):
                results["persistence_check"] = True
                print(f"    ✅ Persistência verificada: Dados permitidos salvos corretamente")
                
        self.test_results["aba_7_dados_permitidos"] = results
        success_rate = sum(results.values()) / len(results) * 100
        status = "✅ FUNCIONAL" if success_rate >= 80 else "⚠️ PARCIAL" if success_rate >= 50 else "❌ COM ERROS"
        print(f"\n📊 ABA 7 - Status: {status} ({success_rate:.1f}% dos testes passaram)")

    async def test_aba_9_auto_responder(self):
        """ABA 9: AUTO-RESPONDER"""
        print("\n" + "="*80)
        print("🧪 ABA 9: AUTO-RESPONDER")
        print("="*80)
        
        results = {
            "get_sequences": False,
            "post_sequence": False,
            "delete_sequence": False,
            "get_config_auto_reply": False,
            "put_config_auto_reply": False
        }
        
        # 1. GET /api/config/auto-responder-sequences
        sequences = await self.test_get_endpoint("/config/auto-responder-sequences", "Listar sequências de auto-responder")
        if sequences is not None:
            results["get_sequences"] = True
            
        # 2. POST /api/config/auto-responder-sequences
        sequence_data = {
            "name": "Sequência Teste Sistemático",
            "trigger": "oi",
            "responses": [
                {
                    "type": "text",
                    "content": "Olá! Bem-vindo ao nosso atendimento.",
                    "delay": 1
                },
                {
                    "type": "image",
                    "content": "https://via.placeholder.com/300x200/0066cc/ffffff?text=Bem-vindo",
                    "delay": 3
                },
                {
                    "type": "text",
                    "content": "Como posso ajudá-lo hoje?",
                    "delay": 2
                }
            ]
        }
        
        created_sequence = await self.test_post_endpoint("/config/auto-responder-sequences", sequence_data, "Criar sequência de auto-responder")
        sequence_id = None
        if created_sequence and created_sequence.get("id"):
            results["post_sequence"] = True
            sequence_id = created_sequence["id"]
            print(f"    📋 Sequence ID criado: {sequence_id}")
            
        # 3. GET /api/config (campo auto_reply)
        config = await self.test_get_endpoint("/config", "Obter configuração de auto-reply")
        if config is not None:
            results["get_config_auto_reply"] = True
            
        # 4. PUT /api/config (atualizar auto_reply)
        auto_reply_data = {
            "auto_reply": {
                "enabled": True,
                "message": "Obrigado pela sua mensagem! Em breve retornaremos o contato.",
                "delay_seconds": 5
            }
        }
        
        if config:
            config.update(auto_reply_data)
            update_data = config
        else:
            update_data = auto_reply_data
            
        updated_config = await self.test_put_endpoint("/config", update_data, "Atualizar configuração de auto-reply")
        if updated_config:
            results["put_config_auto_reply"] = True
            
        # 5. DELETE /api/config/auto-responder-sequences/{id}
        if sequence_id:
            deleted = await self.test_delete_endpoint(f"/config/auto-responder-sequences/{sequence_id}", "Deletar sequência")
            if deleted:
                results["delete_sequence"] = True
                
        self.test_results["aba_9_auto_responder"] = results
        success_rate = sum(results.values()) / len(results) * 100
        status = "✅ FUNCIONAL" if success_rate >= 80 else "⚠️ PARCIAL" if success_rate >= 50 else "❌ COM ERROS"
        print(f"\n📊 ABA 9 - Status: {status} ({success_rate:.1f}% dos testes passaram)")

    async def test_aba_10_tutoriais_apps(self):
        """ABA 10: TUTORIAIS/APPS"""
        print("\n" + "="*80)
        print("🧪 ABA 10: TUTORIAIS/APPS")
        print("="*80)
        
        results = {
            "get_config_apps": False,
            "put_config_apps": False,
            "get_tutorials_advanced": False,
            "post_tutorial_advanced": False,
            "delete_tutorial_advanced": False
        }
        
        # 1. GET /api/config (campo apps)
        config = await self.test_get_endpoint("/config", "Obter configuração de apps")
        if config is not None:
            results["get_config_apps"] = True
            
        # 2. PUT /api/config (atualizar apps)
        apps_data = {
            "apps": [
                {
                    "id": str(uuid.uuid4()),
                    "category": "Smart TV",
                    "name": "Netflix",
                    "instructions": "Acesse a loja de aplicativos da sua Smart TV e procure por Netflix. Faça o download e instale."
                },
                {
                    "id": str(uuid.uuid4()),
                    "category": "Android",
                    "name": "WhatsApp",
                    "instructions": "Baixe o WhatsApp na Google Play Store e configure com seu número de telefone."
                }
            ]
        }
        
        if config:
            config.update(apps_data)
            update_data = config
        else:
            update_data = apps_data
            
        updated_config = await self.test_put_endpoint("/config", update_data, "Atualizar configuração de apps")
        if updated_config:
            results["put_config_apps"] = True
            
        # 3. GET /api/config/tutorials-advanced
        tutorials = await self.test_get_endpoint("/config/tutorials-advanced", "Listar tutoriais avançados")
        if tutorials is not None:
            results["get_tutorials_advanced"] = True
            
        # 4. POST /api/config/tutorials-advanced
        tutorial_data = {
            "category": "Smart TV Samsung",
            "name": "Configuração IPTV",
            "instructions": "1. Acesse as configurações de rede\n2. Configure o DNS\n3. Instale o aplicativo IPTV",
            "video_url": "https://www.youtube.com/watch?v=exemplo",
            "items": [
                {
                    "type": "text",
                    "content": "Primeiro, acesse o menu de configurações da sua Smart TV Samsung.",
                    "delay": 0
                },
                {
                    "type": "image",
                    "content": "https://via.placeholder.com/400x300/ff6600/ffffff?text=Menu+Configurações",
                    "delay": 3
                },
                {
                    "type": "text",
                    "content": "Agora vá em Rede > Configurações de DNS",
                    "delay": 2
                }
            ]
        }
        
        created_tutorial = await self.test_post_endpoint("/config/tutorials-advanced", tutorial_data, "Criar tutorial avançado")
        tutorial_id = None
        if created_tutorial and created_tutorial.get("id"):
            results["post_tutorial_advanced"] = True
            tutorial_id = created_tutorial["id"]
            print(f"    📋 Tutorial ID criado: {tutorial_id}")
            
        # 5. DELETE /api/config/tutorials-advanced/{id}
        if tutorial_id:
            deleted = await self.test_delete_endpoint(f"/config/tutorials-advanced/{tutorial_id}", "Deletar tutorial")
            if deleted:
                results["delete_tutorial_advanced"] = True
                
        self.test_results["aba_10_tutoriais_apps"] = results
        success_rate = sum(results.values()) / len(results) * 100
        status = "✅ FUNCIONAL" if success_rate >= 80 else "⚠️ PARCIAL" if success_rate >= 50 else "❌ COM ERROS"
        print(f"\n📊 ABA 10 - Status: {status} ({success_rate:.1f}% dos testes passaram)")

    async def test_aba_11_aplicativos_iptv(self):
        """ABA 11: APLICATIVOS (IPTV)"""
        print("\n" + "="*80)
        print("🧪 ABA 11: APLICATIVOS (IPTV)")
        print("="*80)
        
        results = {
            "get_iptv_apps": False,
            "post_iptv_app": False,
            "put_iptv_app": False,
            "delete_iptv_app": False
        }
        
        # 1. GET /api/iptv/apps
        iptv_apps = await self.test_get_endpoint("/iptv/apps", "Listar apps IPTV")
        if iptv_apps is not None:
            results["get_iptv_apps"] = True
            
        # 2. POST /api/iptv/apps
        iptv_app_data = {
            "name": "App IPTV Teste Sistemático",
            "category": "Smart TV",
            "provider": "Teste Provider",
            "instructions": "Instruções de instalação do app IPTV de teste",
            "download_url": "https://example.com/app-teste.apk",
            "is_active": True
        }
        
        created_app = await self.test_post_endpoint("/iptv/apps", iptv_app_data, "Criar app IPTV")
        app_id = None
        if created_app and created_app.get("id"):
            results["post_iptv_app"] = True
            app_id = created_app["id"]
            print(f"    📋 IPTV App ID criado: {app_id}")
            
        # 3. PUT /api/iptv/apps/{id}
        if app_id:
            update_data = {
                "name": "App IPTV Teste ATUALIZADO",
                "category": "Android TV",
                "provider": "Teste Provider Atualizado",
                "instructions": "Instruções atualizadas do app IPTV",
                "download_url": "https://example.com/app-teste-v2.apk",
                "is_active": True
            }
            updated_app = await self.test_put_endpoint(f"/iptv/apps/{app_id}", update_data, "Atualizar app IPTV")
            if updated_app:
                results["put_iptv_app"] = True
                
        # 4. DELETE /api/iptv/apps/{id}
        if app_id:
            deleted = await self.test_delete_endpoint(f"/iptv/apps/{app_id}", "Deletar app IPTV")
            if deleted:
                results["delete_iptv_app"] = True
                
        self.test_results["aba_11_aplicativos_iptv"] = results
        success_rate = sum(results.values()) / len(results) * 100
        status = "✅ FUNCIONAL" if success_rate >= 80 else "⚠️ PARCIAL" if success_rate >= 50 else "❌ COM ERROS"
        print(f"\n📊 ABA 11 - Status: {status} ({success_rate:.1f}% dos testes passaram)")

    async def test_aba_12_planos_whatsapp(self):
        """ABA 12: PLANOS WHATSAPP"""
        print("\n" + "="*80)
        print("🧪 ABA 12: PLANOS WHATSAPP")
        print("="*80)
        
        results = {
            "get_whatsapp_plans": False,
            "post_whatsapp_plan": False,
            "put_whatsapp_plan": False,
            "delete_whatsapp_plan": False
        }
        
        # 1. GET /api/whatsapp/plans
        plans = await self.test_get_endpoint("/whatsapp/plans", "Listar planos WhatsApp")
        if plans is not None:
            results["get_whatsapp_plans"] = True
            
        # 2. POST /api/whatsapp/plans
        plan_data = {
            "name": "Plano Teste Sistemático",
            "description": "Plano criado para teste sistemático do sistema",
            "price": 29.90,
            "features": [
                "1 instância WhatsApp",
                "Suporte 24/7",
                "API completa"
            ],
            "max_instances": 1,
            "is_active": True
        }
        
        created_plan = await self.test_post_endpoint("/whatsapp/plans", plan_data, "Criar plano WhatsApp")
        plan_id = None
        if created_plan and created_plan.get("id"):
            results["post_whatsapp_plan"] = True
            plan_id = created_plan["id"]
            print(f"    📋 WhatsApp Plan ID criado: {plan_id}")
            
        # 3. PUT /api/whatsapp/plans/{id}
        if plan_id:
            update_data = {
                "name": "Plano Teste ATUALIZADO",
                "description": "Plano atualizado no teste sistemático",
                "price": 39.90,
                "features": [
                    "2 instâncias WhatsApp",
                    "Suporte 24/7",
                    "API completa",
                    "Relatórios avançados"
                ],
                "max_instances": 2,
                "is_active": True
            }
            updated_plan = await self.test_put_endpoint(f"/whatsapp/plans/{plan_id}", update_data, "Atualizar plano WhatsApp")
            if updated_plan:
                results["put_whatsapp_plan"] = True
                
        # 4. DELETE /api/whatsapp/plans/{id}
        if plan_id:
            deleted = await self.test_delete_endpoint(f"/whatsapp/plans/{plan_id}", "Deletar plano WhatsApp")
            if deleted:
                results["delete_whatsapp_plan"] = True
                
        self.test_results["aba_12_planos_whatsapp"] = results
        success_rate = sum(results.values()) / len(results) * 100
        status = "✅ FUNCIONAL" if success_rate >= 80 else "⚠️ PARCIAL" if success_rate >= 50 else "❌ COM ERROS"
        print(f"\n📊 ABA 12 - Status: {status} ({success_rate:.1f}% dos testes passaram)")

    async def test_aba_13_whatsapp(self):
        """ABA 13: WHATSAPP"""
        print("\n" + "="*80)
        print("🧪 ABA 13: WHATSAPP")
        print("="*80)
        
        results = {
            "get_whatsapp_instances": False,
            "post_whatsapp_instance": False,
            "put_whatsapp_instance": False,
            "delete_whatsapp_instance": False
        }
        
        # 1. GET /api/whatsapp/instances
        instances = await self.test_get_endpoint("/whatsapp/instances", "Listar instâncias WhatsApp")
        if instances is not None:
            results["get_whatsapp_instances"] = True
            
        # 2. POST /api/whatsapp/instances
        instance_data = {
            "name": "Instância Teste Sistemático",
            "phone": "5511999999999",
            "status": "disconnected",
            "webhook_url": "https://example.com/webhook",
            "is_active": True
        }
        
        created_instance = await self.test_post_endpoint("/whatsapp/instances", instance_data, "Criar instância WhatsApp")
        instance_id = None
        if created_instance and created_instance.get("id"):
            results["post_whatsapp_instance"] = True
            instance_id = created_instance["id"]
            print(f"    📋 WhatsApp Instance ID criado: {instance_id}")
            
        # 3. PUT /api/whatsapp/instances/{id}
        if instance_id:
            update_data = {
                "name": "Instância Teste ATUALIZADA",
                "phone": "5511888888888",
                "status": "connected",
                "webhook_url": "https://example.com/webhook-updated",
                "is_active": True
            }
            updated_instance = await self.test_put_endpoint(f"/whatsapp/instances/{instance_id}", update_data, "Atualizar instância WhatsApp")
            if updated_instance:
                results["put_whatsapp_instance"] = True
                
        # 4. DELETE /api/whatsapp/instances/{id}
        if instance_id:
            deleted = await self.test_delete_endpoint(f"/whatsapp/instances/{instance_id}", "Deletar instância WhatsApp")
            if deleted:
                results["delete_whatsapp_instance"] = True
                
        self.test_results["aba_13_whatsapp"] = results
        success_rate = sum(results.values()) / len(results) * 100
        status = "✅ FUNCIONAL" if success_rate >= 80 else "⚠️ PARCIAL" if success_rate >= 50 else "❌ COM ERROS"
        print(f"\n📊 ABA 13 - Status: {status} ({success_rate:.1f}% dos testes passaram)")

    async def test_aba_14_mercado_pago(self):
        """ABA 14: MERCADO PAGO"""
        print("\n" + "="*80)
        print("🧪 ABA 14: MERCADO PAGO")
        print("="*80)
        
        results = {
            "get_mercadopago_config": False,
            "post_mercadopago_config": False,
            "get_subscriptions": False
        }
        
        # 1. GET /api/mercadopago/config
        mp_config = await self.test_get_endpoint("/mercadopago/config", "Obter configuração Mercado Pago")
        if mp_config is not None:
            results["get_mercadopago_config"] = True
            
        # 2. POST /api/mercadopago/config
        mp_config_data = {
            "access_token": "TEST-1234567890-fake-token-for-testing",
            "public_key": "TEST-fake-public-key-for-testing",
            "webhook_url": "https://example.com/mercadopago/webhook",
            "enabled": True
        }
        
        updated_mp_config = await self.test_post_endpoint("/mercadopago/config", mp_config_data, "Atualizar configuração Mercado Pago")
        if updated_mp_config:
            results["post_mercadopago_config"] = True
            
        # 3. GET /api/subscriptions
        subscriptions = await self.test_get_endpoint("/subscriptions", "Listar assinaturas")
        if subscriptions is not None:
            results["get_subscriptions"] = True
            
        self.test_results["aba_14_mercado_pago"] = results
        success_rate = sum(results.values()) / len(results) * 100
        status = "✅ FUNCIONAL" if success_rate >= 80 else "⚠️ PARCIAL" if success_rate >= 50 else "❌ COM ERROS"
        print(f"\n📊 ABA 14 - Status: {status} ({success_rate:.1f}% dos testes passaram)")

    async def test_aba_15_wa_site(self):
        """ABA 15: WA SITE"""
        print("\n" + "="*80)
        print("🧪 ABA 15: WA SITE")
        print("="*80)
        
        results = {
            "get_vendas_bot_config": False,
            "post_vendas_bot_config": False,
            "put_vendas_bot_config": False,
            "get_vendas_buttons": False,
            "post_vendas_button": False,
            "put_vendas_button": False,
            "delete_vendas_button": False
        }
        
        # 1. GET /api/admin/vendas-bot/config
        bot_config = await self.test_get_endpoint("/admin/vendas-bot/config", "Obter configuração do bot WA Site")
        if bot_config is not None:
            results["get_vendas_bot_config"] = True
            
        # 2. POST /api/admin/vendas-bot/config
        bot_config_data = {
            "instructions": "Você é um assistente de vendas especializado em IPTV. Seja sempre educado e prestativo.",
            "link": "https://wa.me/5511999999999",
            "memory": "Lembre-se sempre de perguntar sobre o tipo de dispositivo do cliente.",
            "enabled": True
        }
        
        created_bot_config = await self.test_post_endpoint("/admin/vendas-bot/config", bot_config_data, "Criar configuração do bot")
        if created_bot_config:
            results["post_vendas_bot_config"] = True
            
        # 3. PUT /api/admin/vendas-bot/config
        updated_bot_config_data = {
            "instructions": "Você é um assistente de vendas ATUALIZADO especializado em IPTV e streaming.",
            "link": "https://wa.me/5511888888888",
            "memory": "Lembre-se de perguntar sobre dispositivo e velocidade da internet.",
            "enabled": True
        }
        
        updated_bot_config = await self.test_put_endpoint("/admin/vendas-bot/config", updated_bot_config_data, "Atualizar configuração do bot")
        if updated_bot_config:
            results["put_vendas_bot_config"] = True
            
        # 4. GET /api/vendas-buttons/buttons
        buttons = await self.test_get_endpoint("/vendas-buttons/buttons", "Listar botões interativos")
        if buttons is not None:
            results["get_vendas_buttons"] = True
            
        # 5. POST /api/vendas-buttons/buttons
        button_data = {
            "title": "Teste Grátis",
            "description": "Experimente nosso serviço por 24 horas grátis",
            "action": "redirect",
            "value": "https://example.com/teste-gratis",
            "is_active": True
        }
        
        created_button = await self.test_post_endpoint("/vendas-buttons/buttons", button_data, "Criar botão interativo")
        button_id = None
        if created_button and created_button.get("id"):
            results["post_vendas_button"] = True
            button_id = created_button["id"]
            print(f"    📋 Button ID criado: {button_id}")
            
        # 6. PUT /api/vendas-buttons/buttons/{id}
        if button_id:
            update_button_data = {
                "title": "Teste Grátis ATUALIZADO",
                "description": "Experimente nosso serviço premium por 48 horas grátis",
                "action": "redirect",
                "value": "https://example.com/teste-gratis-premium",
                "is_active": True
            }
            updated_button = await self.test_put_endpoint(f"/vendas-buttons/buttons/{button_id}", update_button_data, "Atualizar botão")
            if updated_button:
                results["put_vendas_button"] = True
                
        # 7. DELETE /api/vendas-buttons/buttons/{id}
        if button_id:
            deleted = await self.test_delete_endpoint(f"/vendas-buttons/buttons/{button_id}", "Deletar botão")
            if deleted:
                results["delete_vendas_button"] = True
                
        self.test_results["aba_15_wa_site"] = results
        success_rate = sum(results.values()) / len(results) * 100
        status = "✅ FUNCIONAL" if success_rate >= 80 else "⚠️ PARCIAL" if success_rate >= 50 else "❌ COM ERROS"
        print(f"\n📊 ABA 15 - Status: {status} ({success_rate:.1f}% dos testes passaram)")

    async def test_aba_16_backup(self):
        """ABA 16: BACKUP"""
        print("\n" + "="*80)
        print("🧪 ABA 16: BACKUP")
        print("="*80)
        
        results = {
            "get_backups": False,
            "post_create_backup": False,
            "post_restore_backup": False
        }
        
        # 1. GET /api/backups
        backups = await self.test_get_endpoint("/backups", "Listar backups existentes")
        if backups is not None:
            results["get_backups"] = True
            
        # 2. POST /api/backups/create
        backup_data = {
            "name": f"Backup Teste Sistemático {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "description": "Backup criado durante teste sistemático das 16 abas"
        }
        
        created_backup = await self.test_post_endpoint("/backups/create", backup_data, "Criar novo backup")
        backup_id = None
        if created_backup and created_backup.get("id"):
            results["post_create_backup"] = True
            backup_id = created_backup["id"]
            print(f"    📋 Backup ID criado: {backup_id}")
            
        # 3. POST /api/backups/restore/{backup_id} (apenas testar se endpoint existe, não executar)
        if backup_id:
            # Não vamos realmente restaurar, apenas verificar se o endpoint responde
            try:
                async with self.session.post(f"{BACKEND_URL}/backups/restore/{backup_id}", 
                                           json={"confirm": False}, headers=self.get_headers()) as response:
                    # Qualquer resposta (mesmo erro) indica que o endpoint existe
                    if response.status in [200, 400, 422]:  # 400/422 = validação, mas endpoint existe
                        results["post_restore_backup"] = True
                        print(f"  ✅ POST /backups/restore/{backup_id} - Endpoint existe (não executado)")
                    else:
                        print(f"  ❌ POST /backups/restore/{backup_id} - Status: {response.status}")
            except Exception as e:
                print(f"  ❌ POST /backups/restore/{backup_id} - Error: {e}")
                
        self.test_results["aba_16_backup"] = results
        success_rate = sum(results.values()) / len(results) * 100
        status = "✅ FUNCIONAL" if success_rate >= 80 else "⚠️ PARCIAL" if success_rate >= 50 else "❌ COM ERROS"
        print(f"\n📊 ABA 16 - Status: {status} ({success_rate:.1f}% dos testes passaram)")

    async def run_all_tests(self):
        """Executa todos os testes das 16 abas"""
        print("🚀 INICIANDO TESTE COMPLETO E SISTEMÁTICO - TODAS AS 16 ABAS DO ADMIN DASHBOARD")
        print("="*100)
        print(f"🔗 Backend URL: {BACKEND_URL}")
        print(f"👤 Admin: {ADMIN_EMAIL}")
        print("="*100)
        
        start_time = time.time()
        
        try:
            await self.setup()
            
            if not self.admin_token:
                print("❌ ERRO CRÍTICO: Não foi possível fazer login como admin!")
                return
                
            # Executar testes das 16 abas
            await self.test_aba_1_dashboard_avisos()
            await self.test_aba_2_dominio()
            await self.test_aba_3_revendas()
            await self.test_aba_4_atendentes()
            await self.test_aba_5_ia_departamentos()
            await self.test_aba_6_msg_rapidas()
            await self.test_aba_7_dados_permitidos()
            # ABA 8 é igual à ABA 1 (Avisos)
            await self.test_aba_9_auto_responder()
            await self.test_aba_10_tutoriais_apps()
            await self.test_aba_11_aplicativos_iptv()
            await self.test_aba_12_planos_whatsapp()
            await self.test_aba_13_whatsapp()
            await self.test_aba_14_mercado_pago()
            await self.test_aba_15_wa_site()
            await self.test_aba_16_backup()
            
        finally:
            await self.cleanup()
            
        # Relatório final
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "="*100)
        print("📊 RELATÓRIO FINAL - TESTE SISTEMÁTICO DAS 16 ABAS")
        print("="*100)
        
        total_tests = 0
        passed_tests = 0
        
        for aba_name, results in self.test_results.items():
            aba_passed = sum(results.values())
            aba_total = len(results)
            total_tests += aba_total
            passed_tests += aba_passed
            
            success_rate = (aba_passed / aba_total * 100) if aba_total > 0 else 0
            status = "✅ FUNCIONAL" if success_rate >= 80 else "⚠️ PARCIAL" if success_rate >= 50 else "❌ COM ERROS"
            
            print(f"{aba_name.upper()}: {status} ({aba_passed}/{aba_total} testes - {success_rate:.1f}%)")
            
        overall_success = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        overall_status = "✅ SISTEMA FUNCIONAL" if overall_success >= 80 else "⚠️ PARCIALMENTE FUNCIONAL" if overall_success >= 50 else "❌ SISTEMA COM PROBLEMAS"
        
        print("="*100)
        print(f"🎯 RESULTADO GERAL: {overall_status}")
        print(f"📈 Taxa de Sucesso: {overall_success:.1f}% ({passed_tests}/{total_tests} testes)")
        print(f"⏱️ Tempo Total: {duration:.1f} segundos")
        print("="*100)

async def main():
    """Função principal"""
    tester = AdminDashboardTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())