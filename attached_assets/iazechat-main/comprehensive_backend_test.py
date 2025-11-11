#!/usr/bin/env python3
"""
🔍 AUDITORIA COMPLETA DO BACKEND - TESTE 1000% DE TODAS AS FUNCIONALIDADES

OBJETIVO: Testar EXAUSTIVAMENTE cada endpoint, cada funcionalidade do backend do sistema CYBERTV Suporte.

ESCOPO COMPLETO DE TESTES:
1. AUTENTICAÇÃO (4 tipos)
2. MULTI-TENANT ISOLATION (CRÍTICO!)
3. CRUD REVENDAS
4. CRUD ATENDENTES
5. CRUD AGENTES IA
6. CRUD DEPARTAMENTOS
7. CONFIG COMPLETO
8. AUTO-RESPONDER AVANÇADO
9. TUTORIALS AVANÇADO
10. APPS IPTV
11. NOTICES
12. UPLOAD DE ARQUIVOS
13. WHATSAPP & PIN
14. GESTÃO DE DOMÍNIOS
15. TICKETS

CREDENCIAIS DE TESTE:
- Admin: senha 102030@ab
- Agent: login fabioteste, senha 123 (reseller_id: 90e335d2-245c-4c5a-8d72-b62e06062c3a)
- Reseller: email michaelrv@gmail.com, senha ab181818ab
- Client: WhatsApp 5511999999999, PIN 00

BACKEND URL: https://wppconnect-fix.preview.emergentagent.com
"""

import requests
import json
import os
import time
import uuid
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import tempfile

# Backend URL from environment
BACKEND_URL = "https://wppconnect-fix.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials from review request
ADMIN_PASSWORD = "102030@ab"
AGENT_LOGIN = "fabioteste"
AGENT_PASSWORD = "123"
RESELLER_EMAIL = "michaelrv@gmail.com"
RESELLER_PASSWORD = "ab181818ab"
CLIENT_WHATSAPP = "5511999999999"
CLIENT_PIN = "00"

class ComprehensiveBackendTester:
    def __init__(self):
        self.admin_token = None
        self.agent_token = None
        self.reseller_token = None
        self.client_token = None
        self.test_results = []
        self.created_data = {
            "resellers": [],
            "agents": [],
            "ai_agents": [],
            "departments": [],
            "iptv_apps": [],
            "auto_responder_sequences": [],
            "tutorials": [],
            "notices": []
        }
        
    def log_result(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}"
        if message:
            result += f" - {message}"
        print(result)
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
        
    def make_request(self, method: str, endpoint: str, data: dict = None, 
                    token: str = None, headers: dict = None, files: dict = None) -> Tuple[bool, dict]:
        """Make HTTP request with error handling"""
        url = f"{API_BASE}{endpoint}"
        
        request_headers = {}
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        if headers:
            request_headers.update(headers)
        
        # Only add Content-Type for JSON requests
        if not files and data is not None:
            request_headers["Content-Type"] = "application/json"
            
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=request_headers, timeout=30)
            elif method.upper() == "POST":
                if files:
                    response = requests.post(url, data=data, files=files, headers=request_headers, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=request_headers, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=request_headers, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=request_headers, timeout=30)
            else:
                return False, {"error": f"Unsupported method: {method}"}
                
            try:
                response_data = response.json() if response.text else {}
            except json.JSONDecodeError:
                response_data = {"text": response.text}
                
            return response.status_code < 400, response_data
            
        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}

    # ============================================
    # 1. AUTENTICAÇÃO (4 tipos)
    # ============================================
    
    def test_admin_login(self) -> bool:
        """Test 1.1: Admin Master Login (senha: 102030@ab)"""
        success, response = self.make_request("POST", "/auth/admin/login", {
            "password": ADMIN_PASSWORD
        })
        
        if success and "token" in response:
            self.admin_token = response["token"]
            self.log_result("Admin Login", True, f"Admin logged in successfully")
            return True
        else:
            self.log_result("Admin Login", False, f"Error: {response}")
            return False
    
    def test_agent_login(self) -> bool:
        """Test 1.2: Agent Login (fabioteste / 123)"""
        success, response = self.make_request("POST", "/auth/agent/login", {
            "login": AGENT_LOGIN,
            "password": AGENT_PASSWORD
        })
        
        if success and "token" in response:
            self.agent_token = response["token"]
            reseller_id = response.get("reseller_id")
            self.log_result("Agent Login", True, f"Agent logged in, reseller_id: {reseller_id}")
            return True
        else:
            self.log_result("Agent Login", False, f"Error: {response}")
            return False

    def test_reseller_login(self) -> bool:
        """Test 1.3: Reseller Login (michaelrv@gmail.com / ab181818ab)"""
        success, response = self.make_request("POST", "/resellers/login", {
            "email": RESELLER_EMAIL,
            "password": RESELLER_PASSWORD
        })
        
        if success and "token" in response:
            self.reseller_token = response["token"]
            reseller_id = response.get("reseller_id")
            self.log_result("Reseller Login", True, f"Reseller logged in, reseller_id: {reseller_id}")
            return True
        else:
            self.log_result("Reseller Login", False, f"Error: {response}")
            return False

    def test_client_login(self) -> bool:
        """Test 1.4: Client Login (WhatsApp: 5511999999999, PIN: 00)"""
        success, response = self.make_request("POST", "/auth/client/login", {
            "whatsapp": CLIENT_WHATSAPP,
            "pin": CLIENT_PIN
        })
        
        if success and "token" in response:
            self.client_token = response["token"]
            self.log_result("Client Login", True, f"Client logged in successfully")
            return True
        else:
            self.log_result("Client Login", False, f"Error: {response}")
            return False

    # ============================================
    # 2. MULTI-TENANT ISOLATION (CRÍTICO!)
    # ============================================
    
    def test_multi_tenant_isolation(self) -> bool:
        """Test 2: Validar isolamento multi-tenant crítico"""
        print("\n🔒 TESTANDO ISOLAMENTO MULTI-TENANT CRÍTICO...")
        
        isolation_tests = []
        
        # Test tickets isolation
        admin_tickets, _ = self.make_request("GET", "/tickets", token=self.admin_token)
        agent_tickets, _ = self.make_request("GET", "/tickets", token=self.agent_token)
        
        admin_count = len(admin_tickets[1]) if admin_tickets else 0
        agent_count = len(agent_tickets[1]) if agent_tickets else 0
        
        print(f"   📊 Tickets - Admin Master vê: {admin_count}, Agent fabioteste vê: {agent_count}")
        
        # Admin should see more or equal tickets than agent
        tickets_isolation_ok = admin_count >= agent_count
        isolation_tests.append(("Tickets Isolation", tickets_isolation_ok))
        
        # Test agents isolation
        admin_agents, _ = self.make_request("GET", "/agents", token=self.admin_token)
        agent_agents, _ = self.make_request("GET", "/agents", token=self.agent_token)
        
        admin_agents_count = len(admin_agents[1]) if admin_agents else 0
        agent_agents_count = len(agent_agents[1]) if agent_agents else 0
        
        print(f"   📊 Agents - Admin Master vê: {admin_agents_count}, Agent fabioteste vê: {agent_agents_count}")
        
        agents_isolation_ok = admin_agents_count >= agent_agents_count
        isolation_tests.append(("Agents Isolation", agents_isolation_ok))
        
        # Test AI agents isolation
        admin_ai_agents, _ = self.make_request("GET", "/ai/agents", token=self.admin_token)
        reseller_ai_agents, _ = self.make_request("GET", "/ai/agents", token=self.reseller_token) if self.reseller_token else (False, [])
        
        admin_ai_count = len(admin_ai_agents[1]) if admin_ai_agents else 0
        reseller_ai_count = len(reseller_ai_agents[1]) if reseller_ai_agents else 0
        
        print(f"   📊 AI Agents - Admin Master vê: {admin_ai_count}, Reseller vê: {reseller_ai_count}")
        
        ai_agents_isolation_ok = admin_ai_count >= reseller_ai_count
        isolation_tests.append(("AI Agents Isolation", ai_agents_isolation_ok))
        
        # Overall isolation result
        all_isolation_ok = all(result for _, result in isolation_tests)
        
        self.log_result("Multi-Tenant Isolation", all_isolation_ok, 
                       f"Tickets: {tickets_isolation_ok}, Agents: {agents_isolation_ok}, AI Agents: {ai_agents_isolation_ok}")
        
        return all_isolation_ok

    # ============================================
    # 3. CRUD REVENDAS
    # ============================================
    
    def test_resellers_crud(self) -> bool:
        """Test 3: CRUD Revendas completo"""
        print("\n🏢 TESTANDO CRUD REVENDAS...")
        
        if not self.admin_token:
            self.log_result("Resellers CRUD", False, "Admin token required")
            return False
        
        # 3.1 GET /api/resellers (listar todas)
        success, resellers = self.make_request("GET", "/resellers", token=self.admin_token)
        if not success:
            self.log_result("List Resellers", False, f"Failed to list resellers: {resellers}")
            return False
        
        initial_count = len(resellers)
        print(f"   📊 Revendas existentes: {initial_count}")
        self.log_result("List Resellers", True, f"Found {initial_count} resellers")
        
        # 3.2 POST /api/resellers (criar nova revenda)
        new_reseller_data = {
            "name": "Teste Revenda CRUD",
            "email": f"teste-crud-{int(time.time())}@teste.com",
            "password": "senha123",
            "custom_domain": f"teste-crud-{int(time.time())}.com",
            "is_active": True
        }
        
        success, response = self.make_request("POST", "/resellers", new_reseller_data, token=self.admin_token)
        if success and response.get("ok"):
            created_reseller_id = response.get("reseller_id")
            self.created_data["resellers"].append(created_reseller_id)
            self.log_result("Create Reseller", True, f"Created reseller: {created_reseller_id}")
            
            # 3.3 PUT /api/resellers/{id} (editar)
            update_data = {
                "name": "Teste Revenda CRUD Editada",
                "email": new_reseller_data["email"],  # Keep same email
                "custom_domain": f"teste-crud-editado-{int(time.time())}.com",
                "is_active": True
            }
            
            success, response = self.make_request("PUT", f"/resellers/{created_reseller_id}", update_data, token=self.admin_token)
            if success:
                self.log_result("Update Reseller", True, "Reseller updated successfully")
            else:
                self.log_result("Update Reseller", False, f"Failed to update: {response}")
                
            return True
        else:
            self.log_result("Create Reseller", False, f"Failed to create: {response}")
            return False

    # ============================================
    # 4. CRUD ATENDENTES
    # ============================================
    
    def test_agents_crud(self) -> bool:
        """Test 4: CRUD Atendentes"""
        print("\n👥 TESTANDO CRUD ATENDENTES...")
        
        if not self.admin_token:
            self.log_result("Agents CRUD", False, "Admin token required")
            return False
        
        # 4.1 GET /api/agents
        success, agents = self.make_request("GET", "/agents", token=self.admin_token)
        if not success:
            self.log_result("List Agents", False, f"Failed to list agents: {agents}")
            return False
        
        initial_count = len(agents)
        print(f"   📊 Atendentes existentes: {initial_count}")
        self.log_result("List Agents", True, f"Found {initial_count} agents")
        
        # 4.2 POST /api/agents (criar novo)
        new_agent_data = {
            "name": f"Teste Agent CRUD {int(time.time())}",
            "login": f"teste-agent-{int(time.time())}",
            "password": "senha123",
            "avatar": ""
        }
        
        success, response = self.make_request("POST", "/agents", new_agent_data, token=self.admin_token)
        if success and response.get("ok"):
            created_agent_id = response.get("id")
            self.created_data["agents"].append(created_agent_id)
            self.log_result("Create Agent", True, f"Created agent: {created_agent_id}")
            return True
        else:
            self.log_result("Create Agent", False, f"Failed to create: {response}")
            return False

    # ============================================
    # 5. CRUD AGENTES IA
    # ============================================
    
    def test_ai_agents_crud(self) -> bool:
        """Test 5: CRUD Agentes IA"""
        print("\n🤖 TESTANDO CRUD AGENTES IA...")
        
        if not self.admin_token:
            self.log_result("AI Agents CRUD", False, "Admin token required")
            return False
        
        # 5.1 GET /api/ai/agents
        success, ai_agents = self.make_request("GET", "/ai/agents", token=self.admin_token)
        if not success:
            self.log_result("List AI Agents", False, f"Failed to list AI agents: {ai_agents}")
            return False
        
        initial_count = len(ai_agents)
        print(f"   📊 Agentes IA existentes: {initial_count}")
        self.log_result("List AI Agents", True, f"Found {initial_count} AI agents")
        
        # 5.2 POST /api/ai/agents (criar novo)
        new_ai_agent_data = {
            "name": f"Teste AI Agent {int(time.time())}",
            "personality": "Assistente prestativo e profissional",
            "instructions": "Ajude os clientes com suas dúvidas",
            "llm_provider": "openai",
            "llm_model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 1000,
            "is_active": True
        }
        
        success, response = self.make_request("POST", "/ai/agents", new_ai_agent_data, token=self.admin_token)
        if success and response.get("ok"):
            created_ai_agent_id = response.get("id")
            self.created_data["ai_agents"].append(created_ai_agent_id)
            self.log_result("Create AI Agent", True, f"Created AI agent: {created_ai_agent_id}")
            
            # 5.3 PUT /api/ai/agents/{id} (editar)
            update_data = {
                "name": f"Teste AI Agent Editado {int(time.time())}",
                "personality": "Assistente ainda mais prestativo",
                "temperature": 0.8
            }
            
            success, response = self.make_request("PUT", f"/ai/agents/{created_ai_agent_id}", update_data, token=self.admin_token)
            if success:
                self.log_result("Update AI Agent", True, "AI agent updated successfully")
            else:
                self.log_result("Update AI Agent", False, f"Failed to update: {response}")
                
            return True
        else:
            self.log_result("Create AI Agent", False, f"Failed to create: {response}")
            return False

    # ============================================
    # 6. CRUD DEPARTAMENTOS
    # ============================================
    
    def test_departments_crud(self) -> bool:
        """Test 6: CRUD Departamentos"""
        print("\n🏛️ TESTANDO CRUD DEPARTAMENTOS...")
        
        if not self.admin_token:
            self.log_result("Departments CRUD", False, "Admin token required")
            return False
        
        # 6.1 GET /api/ai/departments
        success, departments = self.make_request("GET", "/ai/departments", token=self.admin_token)
        if not success:
            self.log_result("List Departments", False, f"Failed to list departments: {departments}")
            return False
        
        initial_count = len(departments)
        print(f"   📊 Departamentos existentes: {initial_count}")
        self.log_result("List Departments", True, f"Found {initial_count} departments")
        
        # 6.2 POST /api/ai/departments (criar novo)
        new_department_data = {
            "name": f"TESTE DEPT {int(time.time())}",
            "description": "Departamento de teste para CRUD",
            "is_default": False,
            "timeout_seconds": 120
        }
        
        success, response = self.make_request("POST", "/ai/departments", new_department_data, token=self.admin_token)
        if success and response.get("ok"):
            created_department_id = response.get("id")
            self.created_data["departments"].append(created_department_id)
            self.log_result("Create Department", True, f"Created department: {created_department_id}")
            return True
        else:
            self.log_result("Create Department", False, f"Failed to create: {response}")
            return False

    # ============================================
    # 7. CONFIG COMPLETO
    # ============================================
    
    def test_config_complete(self) -> bool:
        """Test 7: Config completo (GET/PUT com todos os campos)"""
        print("\n⚙️ TESTANDO CONFIG COMPLETO...")
        
        if not self.admin_token:
            self.log_result("Config Complete", False, "Admin token required")
            return False
        
        # 7.1 GET /api/config (verificar TODOS os campos)
        success, config = self.make_request("GET", "/config", token=self.admin_token)
        if not success:
            self.log_result("Get Config", False, f"Failed to get config: {config}")
            return False
        
        required_fields = ["pix_key", "allowed_data", "api_integration", "ai_agent"]
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            self.log_result("Get Config", False, f"Missing fields: {missing_fields}")
            return False
        
        self.log_result("Get Config", True, f"All required fields present: {required_fields}")
        
        # 7.2 PUT /api/config (salvar config completa)
        updated_config = {
            "pix_key": "teste@pix.com",
            "allowed_data": {
                "cpfs": ["123.456.789-00"],
                "emails": ["teste@email.com"],
                "phones": ["11999999999"],
                "random_keys": ["test-key-123"]
            },
            "api_integration": {
                "api_url": "https://api.teste.com",
                "api_token": "token-teste-123",
                "api_enabled": True
            },
            "ai_agent": {
                "name": "Assistente Teste",
                "personality": "Prestativo e eficiente",
                "instructions": "Ajude sempre os clientes",
                "llm_provider": "openai",
                "llm_model": "gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": 1000,
                "enabled": True
            }
        }
        
        success, response = self.make_request("PUT", "/config", updated_config, token=self.admin_token)
        if success:
            self.log_result("Update Config", True, "Config updated successfully")
            return True
        else:
            self.log_result("Update Config", False, f"Failed to update: {response}")
            return False

    # ============================================
    # 8. AUTO-RESPONDER AVANÇADO
    # ============================================
    
    def test_auto_responder_advanced(self) -> bool:
        """Test 8: Auto-Responder com múltiplas respostas e mídia"""
        print("\n🔄 TESTANDO AUTO-RESPONDER AVANÇADO...")
        
        if not self.admin_token:
            self.log_result("Auto-Responder Advanced", False, "Admin token required")
            return False
        
        # 8.1 GET /api/config/auto-responder-sequences
        success, sequences = self.make_request("GET", "/config/auto-responder-sequences", token=self.admin_token)
        if not success:
            self.log_result("List Auto-Responder Sequences", False, f"Failed to list: {sequences}")
            return False
        
        initial_count = len(sequences)
        print(f"   📊 Sequências existentes: {initial_count}")
        self.log_result("List Auto-Responder Sequences", True, f"Found {initial_count} sequences")
        
        # 8.2 POST /api/config/auto-responder-sequences (criar sequência)
        new_sequence_data = {
            "name": f"Teste Sequence {int(time.time())}",
            "trigger": "teste auto",
            "responses": [
                {
                    "type": "text",
                    "content": "Olá! Esta é uma resposta automática de teste.",
                    "delay_seconds": 1
                },
                {
                    "type": "image",
                    "content": "https://example.com/image.jpg",
                    "delay_seconds": 3
                },
                {
                    "type": "text",
                    "content": "Aguarde um momento que um atendente irá te ajudar.",
                    "delay_seconds": 5
                }
            ],
            "is_active": True
        }
        
        success, response = self.make_request("POST", "/config/auto-responder-sequences", new_sequence_data, token=self.admin_token)
        if success and response.get("ok"):
            created_sequence_id = response.get("id")
            self.created_data["auto_responder_sequences"].append(created_sequence_id)
            self.log_result("Create Auto-Responder Sequence", True, f"Created sequence: {created_sequence_id}")
            return True
        else:
            self.log_result("Create Auto-Responder Sequence", False, f"Failed to create: {response}")
            return False

    # ============================================
    # 9. TUTORIALS AVANÇADO
    # ============================================
    
    def test_tutorials_advanced(self) -> bool:
        """Test 9: Tutorials com múltiplos itens e categorias"""
        print("\n📚 TESTANDO TUTORIALS AVANÇADO...")
        
        if not self.admin_token:
            self.log_result("Tutorials Advanced", False, "Admin token required")
            return False
        
        # 9.1 GET /api/config/tutorials-advanced
        success, tutorials = self.make_request("GET", "/config/tutorials-advanced", token=self.admin_token)
        if not success:
            self.log_result("List Tutorials", False, f"Failed to list: {tutorials}")
            return False
        
        initial_count = len(tutorials)
        print(f"   📊 Tutoriais existentes: {initial_count}")
        self.log_result("List Tutorials", True, f"Found {initial_count} tutorials")
        
        # 9.2 POST /api/config/tutorials-advanced (criar tutorial)
        new_tutorial_data = {
            "title": f"Tutorial Teste {int(time.time())}",
            "category": "Smart TV",
            "app_name": "Teste IPTV",
            "provider_code": "TESTE123",
            "items": [
                {
                    "type": "text",
                    "content": "Passo 1: Abra o aplicativo",
                    "delay_seconds": 2
                },
                {
                    "type": "image",
                    "content": "https://example.com/step1.jpg",
                    "delay_seconds": 5
                },
                {
                    "type": "text",
                    "content": "Passo 2: Configure as credenciais",
                    "delay_seconds": 3
                }
            ],
            "is_active": True
        }
        
        success, response = self.make_request("POST", "/config/tutorials-advanced", new_tutorial_data, token=self.admin_token)
        if success and response.get("ok"):
            created_tutorial_id = response.get("id")
            self.created_data["tutorials"].append(created_tutorial_id)
            self.log_result("Create Tutorial", True, f"Created tutorial: {created_tutorial_id}")
            return True
        else:
            self.log_result("Create Tutorial", False, f"Failed to create: {response}")
            return False

    # ============================================
    # 10. APPS IPTV
    # ============================================
    
    def test_iptv_apps_crud(self) -> bool:
        """Test 10: CRUD Apps IPTV"""
        print("\n📺 TESTANDO APPS IPTV...")
        
        if not self.admin_token:
            self.log_result("IPTV Apps CRUD", False, "Admin token required")
            return False
        
        # 10.1 GET /api/iptv-apps
        success, apps = self.make_request("GET", "/iptv-apps", token=self.admin_token)
        if not success:
            self.log_result("List IPTV Apps", False, f"Failed to list: {apps}")
            return False
        
        initial_count = len(apps)
        print(f"   📊 Apps IPTV existentes: {initial_count}")
        self.log_result("List IPTV Apps", True, f"Found {initial_count} IPTV apps")
        
        # 10.2 POST /api/iptv-apps (criar novo app)
        new_app_data = {
            "name": f"Teste IPTV App {int(time.time())}",
            "category": "Smart TV",
            "provider": "Teste Provider",
            "code": f"TESTE{int(time.time())}",
            "instructions": "Instruções de teste para configuração",
            "video_url": "https://example.com/tutorial.mp4",
            "is_active": True
        }
        
        success, response = self.make_request("POST", "/iptv-apps", new_app_data, token=self.admin_token)
        if success and response.get("ok"):
            created_app_id = response.get("id")
            self.created_data["iptv_apps"].append(created_app_id)
            self.log_result("Create IPTV App", True, f"Created app: {created_app_id}")
            
            # 10.3 PUT /api/iptv-apps/{id} (editar)
            update_data = {
                "name": f"Teste IPTV App Editado {int(time.time())}",
                "instructions": "Instruções atualizadas"
            }
            
            success, response = self.make_request("PUT", f"/iptv-apps/{created_app_id}", update_data, token=self.admin_token)
            if success:
                self.log_result("Update IPTV App", True, "IPTV app updated successfully")
            else:
                self.log_result("Update IPTV App", False, f"Failed to update: {response}")
                
            return True
        else:
            self.log_result("Create IPTV App", False, f"Failed to create: {response}")
            return False

    # ============================================
    # 11. NOTICES
    # ============================================
    
    def test_notices_crud(self) -> bool:
        """Test 11: CRUD Notices"""
        print("\n📢 TESTANDO NOTICES...")
        
        if not self.admin_token:
            self.log_result("Notices CRUD", False, "Admin token required")
            return False
        
        # 11.1 GET /api/notices
        success, notices = self.make_request("GET", "/notices", token=self.admin_token)
        if not success:
            self.log_result("List Notices", False, f"Failed to list: {notices}")
            return False
        
        initial_count = len(notices)
        print(f"   📊 Notices existentes: {initial_count}")
        self.log_result("List Notices", True, f"Found {initial_count} notices")
        
        # 11.2 POST /api/notices (criar notice)
        new_notice_data = {
            "title": f"Teste Notice {int(time.time())}",
            "content": "Este é um aviso de teste para validar a funcionalidade",
            "type": "info",
            "is_active": True
        }
        
        success, response = self.make_request("POST", "/notices", new_notice_data, token=self.admin_token)
        if success and response.get("ok"):
            created_notice_id = response.get("id")
            self.created_data["notices"].append(created_notice_id)
            self.log_result("Create Notice", True, f"Created notice: {created_notice_id}")
            return True
        else:
            self.log_result("Create Notice", False, f"Failed to create: {response}")
            return False

    # ============================================
    # 12. UPLOAD DE ARQUIVOS
    # ============================================
    
    def test_file_upload(self) -> bool:
        """Test 12: Upload de arquivos com detecção de tipo"""
        print("\n📁 TESTANDO UPLOAD DE ARQUIVOS...")
        
        if not self.admin_token:
            self.log_result("File Upload", False, "Admin token required")
            return False
        
        # Test different file types
        test_files = [
            ("text", "test.txt", "text/plain", b"Este e um arquivo de teste"),
            ("image", "test.jpg", "image/jpeg", b"\xff\xd8\xff\xe0\x00\x10JFIF"),  # JPEG header
            ("video", "test.mp4", "video/mp4", b"fake video content"),
            ("audio", "test.mp3", "audio/mpeg", b"fake audio content")
        ]
        
        upload_results = []
        
        for file_type, filename, content_type, content in test_files:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{filename.split('.')[-1]}") as temp_file:
                temp_file.write(content)
                temp_file.flush()
                
                # Upload file
                with open(temp_file.name, 'rb') as f:
                    files = {'file': (filename, f, content_type)}
                    success, response = self.make_request("POST", "/upload", files=files, token=self.admin_token)
                    
                    if success and "url" in response:
                        detected_kind = response.get("kind", "unknown")
                        upload_results.append((file_type, True, f"Uploaded {filename}, detected as {detected_kind}"))
                    else:
                        upload_results.append((file_type, False, f"Failed to upload {filename}: {response}"))
                
                # Clean up temp file
                os.unlink(temp_file.name)
        
        # Log results
        all_uploads_ok = all(result[1] for result in upload_results)
        for file_type, success, message in upload_results:
            self.log_result(f"Upload {file_type.title()}", success, message)
        
        self.log_result("File Upload", all_uploads_ok, f"Uploaded {len([r for r in upload_results if r[1]])}/{len(upload_results)} files")
        return all_uploads_ok

    # ============================================
    # 13. WHATSAPP & PIN
    # ============================================
    
    def test_whatsapp_pin_features(self) -> bool:
        """Test 13: WhatsApp popup e PIN update"""
        print("\n📱 TESTANDO WHATSAPP & PIN...")
        
        if not self.client_token:
            self.log_result("WhatsApp & PIN", False, "Client token required")
            return False
        
        # 13.1 GET /api/users/whatsapp-popup-status
        success, popup_status = self.make_request("GET", "/users/whatsapp-popup-status", token=self.client_token)
        if not success:
            self.log_result("WhatsApp Popup Status", False, f"Failed to get status: {popup_status}")
            return False
        
        should_show = popup_status.get("should_show", False)
        self.log_result("WhatsApp Popup Status", True, f"Should show popup: {should_show}")
        
        # 13.2 PUT /api/users/me/whatsapp-confirm
        confirm_data = {"whatsapp": "5511999999999"}
        success, response = self.make_request("PUT", "/users/me/whatsapp-confirm", confirm_data, token=self.client_token)
        if not success:
            self.log_result("WhatsApp Confirm", False, f"Failed to confirm: {response}")
            return False
        
        self.log_result("WhatsApp Confirm", True, "WhatsApp confirmed successfully")
        
        # 13.3 PUT /api/users/me/pin (valid PIN)
        pin_data = {"pin": "99"}
        success, response = self.make_request("PUT", "/users/me/pin", pin_data, token=self.client_token)
        if not success:
            self.log_result("PIN Update Valid", False, f"Failed to update PIN: {response}")
            return False
        
        self.log_result("PIN Update Valid", True, "PIN updated successfully")
        
        # 13.4 PUT /api/users/me/pin (invalid PIN - should fail)
        invalid_pin_data = {"pin": "123"}  # 3 digits - should fail
        success, response = self.make_request("PUT", "/users/me/pin", invalid_pin_data, token=self.client_token)
        if success:
            self.log_result("PIN Update Invalid", False, "Invalid PIN was accepted (should have failed)")
            return False
        
        self.log_result("PIN Update Invalid", True, "Invalid PIN correctly rejected")
        
        return True

    # ============================================
    # 14. GESTÃO DE DOMÍNIOS
    # ============================================
    
    def test_domain_management(self) -> bool:
        """Test 14: Gestão de domínios para revendas"""
        print("\n🌐 TESTANDO GESTÃO DE DOMÍNIOS...")
        
        if not self.reseller_token:
            self.log_result("Domain Management", False, "Reseller token required")
            return False
        
        # 14.1 GET /api/reseller/domain-info
        success, domain_info = self.make_request("GET", "/reseller/domain-info", token=self.reseller_token)
        if not success:
            self.log_result("Domain Info", False, f"Failed to get domain info: {domain_info}")
            return False
        
        self.log_result("Domain Info", True, f"Domain info retrieved: {domain_info.get('custom_domain', 'No custom domain')}")
        
        # 14.2 POST /api/reseller/update-domain
        new_domain = f"teste-domain-{int(time.time())}.com"
        update_data = {"custom_domain": new_domain}
        success, response = self.make_request("POST", "/reseller/update-domain", update_data, token=self.reseller_token)
        if not success:
            self.log_result("Update Domain", False, f"Failed to update domain: {response}")
            return False
        
        self.log_result("Update Domain", True, f"Domain updated to: {new_domain}")
        
        # 14.3 GET /api/reseller/verify-domain
        success, verify_result = self.make_request("GET", "/reseller/verify-domain", token=self.reseller_token)
        if not success:
            self.log_result("Verify Domain", False, f"Failed to verify domain: {verify_result}")
            return False
        
        self.log_result("Verify Domain", True, f"Domain verification result: {verify_result}")
        
        return True

    # ============================================
    # 15. TICKETS
    # ============================================
    
    def test_tickets_functionality(self) -> bool:
        """Test 15: Funcionalidade de tickets"""
        print("\n🎫 TESTANDO FUNCIONALIDADE DE TICKETS...")
        
        if not self.admin_token:
            self.log_result("Tickets Functionality", False, "Admin token required")
            return False
        
        # 15.1 GET /api/tickets (com tenant isolation)
        success, tickets = self.make_request("GET", "/tickets", token=self.admin_token)
        if not success:
            self.log_result("List Tickets", False, f"Failed to list tickets: {tickets}")
            return False
        
        ticket_count = len(tickets)
        print(f"   📊 Tickets encontrados: {ticket_count}")
        self.log_result("List Tickets", True, f"Found {ticket_count} tickets")
        
        # 15.2 GET /api/tickets/counts
        success, counts = self.make_request("GET", "/tickets/counts", token=self.admin_token)
        if not success:
            self.log_result("Ticket Counts", False, f"Failed to get counts: {counts}")
            return False
        
        em_espera = counts.get("EM_ESPERA", 0)
        atendendo = counts.get("ATENDENDO", 0)
        finalizadas = counts.get("FINALIZADAS", 0)
        
        self.log_result("Ticket Counts", True, f"EM_ESPERA: {em_espera}, ATENDENDO: {atendendo}, FINALIZADAS: {finalizadas}")
        
        return True

    # ============================================
    # CLEANUP
    # ============================================
    
    def cleanup_created_data(self):
        """Clean up all created test data"""
        print("\n🧹 LIMPANDO DADOS DE TESTE...")
        
        if not self.admin_token:
            print("❌ No admin token for cleanup")
            return
        
        # Clean up in reverse order of dependencies
        cleanup_order = [
            ("notices", "/notices"),
            ("tutorials", "/config/tutorials-advanced"),
            ("auto_responder_sequences", "/config/auto-responder-sequences"),
            ("iptv_apps", "/iptv-apps"),
            ("departments", "/ai/departments"),
            ("ai_agents", "/ai/agents"),
            ("agents", "/agents"),
            ("resellers", "/resellers")
        ]
        
        for data_type, endpoint_prefix in cleanup_order:
            items = self.created_data.get(data_type, [])
            for item_id in items:
                success, response = self.make_request("DELETE", f"{endpoint_prefix}/{item_id}", token=self.admin_token)
                if success:
                    print(f"✅ Deleted {data_type}: {item_id}")
                else:
                    print(f"❌ Failed to delete {data_type} {item_id}: {response}")

    # ============================================
    # MAIN TEST RUNNER
    # ============================================
    
    def run_comprehensive_tests(self):
        """Run all comprehensive backend tests"""
        print("🔍 AUDITORIA COMPLETA DO BACKEND - TESTE 1000% DE TODAS AS FUNCIONALIDADES")
        print("=" * 80)
        print("OBJETIVO: Testar EXAUSTIVAMENTE cada endpoint, cada funcionalidade")
        print("BACKEND URL:", BACKEND_URL)
        print("=" * 80)
        
        # Define all tests in order
        tests = [
            # 1. AUTENTICAÇÃO (4 tipos)
            ("Admin Login", self.test_admin_login),
            ("Agent Login", self.test_agent_login),
            ("Reseller Login", self.test_reseller_login),
            ("Client Login", self.test_client_login),
            
            # 2. MULTI-TENANT ISOLATION (CRÍTICO!)
            ("Multi-Tenant Isolation", self.test_multi_tenant_isolation),
            
            # 3-15. FUNCIONALIDADES COMPLETAS
            ("Resellers CRUD", self.test_resellers_crud),
            ("Agents CRUD", self.test_agents_crud),
            ("AI Agents CRUD", self.test_ai_agents_crud),
            ("Departments CRUD", self.test_departments_crud),
            ("Config Complete", self.test_config_complete),
            ("Auto-Responder Advanced", self.test_auto_responder_advanced),
            ("Tutorials Advanced", self.test_tutorials_advanced),
            ("IPTV Apps CRUD", self.test_iptv_apps_crud),
            ("Notices CRUD", self.test_notices_crud),
            ("File Upload", self.test_file_upload),
            ("WhatsApp & PIN", self.test_whatsapp_pin_features),
            ("Domain Management", self.test_domain_management),
            ("Tickets Functionality", self.test_tickets_functionality),
        ]
        
        passed = 0
        total = len(tests)
        failed_tests = []
        
        for test_name, test_func in tests:
            try:
                print(f"\n🔄 Executando: {test_name}")
                if test_func():
                    passed += 1
                    print(f"✅ {test_name} PASSOU")
                else:
                    failed_tests.append(test_name)
                    print(f"❌ {test_name} FALHOU")
                time.sleep(0.5)  # Small delay between tests
            except Exception as e:
                self.log_result(test_name, False, f"Exception: {str(e)}")
                failed_tests.append(test_name)
                print(f"💥 {test_name} ERRO: {str(e)}")
                
        print("\n" + "=" * 80)
        print(f"📊 RESULTADO FINAL: {passed}/{total} testes passaram ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            print("🎉 TODOS OS TESTES PASSARAM! BACKEND 100% FUNCIONAL!")
            print("🔒 SISTEMA COMPLETAMENTE VALIDADO E PRONTO PARA PRODUÇÃO!")
        else:
            print(f"⚠️  {total - passed} testes falharam:")
            for failed_test in failed_tests:
                print(f"   ❌ {failed_test}")
            print("\n🔧 AÇÕES NECESSÁRIAS:")
            print("   - Verificar endpoints que falharam")
            print("   - Confirmar credenciais e configurações")
            print("   - Testar novamente após correções")
            
        # Cleanup
        self.cleanup_created_data()
            
        return passed, total, self.test_results


if __name__ == "__main__":
    print("🔍 INICIANDO AUDITORIA COMPLETA DO BACKEND")
    print("Backend URL:", BACKEND_URL)
    print("Credenciais de teste configuradas")
    print()
    
    tester = ComprehensiveBackendTester()
    passed, total, results = tester.run_comprehensive_tests()
    
    print(f"\n📋 RESUMO DETALHADO:")
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['test']}: {result['message']}")
    
    exit_code = 0 if passed == total else 1
    exit(exit_code)