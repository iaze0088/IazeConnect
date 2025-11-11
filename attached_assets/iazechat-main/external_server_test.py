#!/usr/bin/env python3
"""
TESTE COMPLETO DO SERVIDOR EXTERNO - https://suporte.help

OBJETIVOS:
Testar TODAS as funcionalidades principais do sistema no servidor externo.

TESTES A REALIZAR:

### 1. AUTENTICAÇÃO
- Admin login (POST /api/auth/admin/login) - senha: 102030@ab
- Atendente login (POST /api/auth/agent/login) - login: leticiaatt, senha: ab181818ab

### 2. DEPARTAMENTOS
- Listar departamentos (GET /api/ai/departments)
- Criar departamento (POST /api/ai/departments) com:
  - name: "Teste Completo"
  - agent_ids: [pegar ID de um atendente via GET /api/agents]
  - origin: "wa_suporte"

### 3. OFFICE SYNC
- Verificar estatísticas (GET /api/office-sync/statistics)
- Buscar cliente (POST /api/office-sync/search-clients) com query: "teste"
- Iniciar sincronização (POST /api/office-sync/sync)

### 4. BACKUP
- Listar backups (GET /api/backup/list)
- Criar backup (POST /api/backup/create)

### 5. MÍDIA/UPLOAD
- Health check de uploads (GET /api/media/health ou /api/uploads/test)
- Se houver endpoint de upload, testar upload simples

### 6. HEALTH CHECK
- GET /api/health - verificar se MongoDB está conectado

SERVIDOR:
- URL Base: https://suporte.help
- Todas rotas com prefixo /api

CREDENCIAIS:
- Admin: password=102030@ab
- Atendente: login=leticiaatt, password=ab181818ab
"""

import asyncio
import aiohttp
import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, Optional, List, Tuple
import uuid

# Configurações do servidor externo
EXTERNAL_SERVER_URL = "https://suporte.help"
API_BASE = f"{EXTERNAL_SERVER_URL}/api"

# Credenciais conforme review request
ADMIN_PASSWORD = "102030@ab"
AGENT_LOGIN = "leticiaatt"
AGENT_PASSWORD = "ab181818ab"

class ExternalServerTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.agent_token = None
        self.test_results = []
        self.created_department_id = None
        
    async def setup_session(self):
        """Configurar sessão HTTP com timeout adequado"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        
    async def cleanup_session(self):
        """Limpar sessão HTTP"""
        if self.session:
            await self.session.close()
            
    def log_result(self, test_name: str, success: bool, message: str = "", details: dict = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}"
        if message:
            result += f" - {message}"
        print(result)
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {}
        })
        
    async def make_request(self, method: str, endpoint: str, data: dict = None, 
                          token: str = None, headers: dict = None, files: dict = None) -> Tuple[bool, dict, int]:
        """Make HTTP request with error handling"""
        url = f"{API_BASE}{endpoint}"
        
        request_headers = {}
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        if headers:
            request_headers.update(headers)
            
        try:
            if method.upper() == "GET":
                async with self.session.get(url, headers=request_headers) as response:
                    status = response.status
                    try:
                        data = await response.json()
                    except:
                        data = {"text": await response.text()}
                    return status < 400, data, status
                    
            elif method.upper() == "POST":
                if files:
                    # For file uploads
                    form_data = aiohttp.FormData()
                    for key, value in files.items():
                        form_data.add_field(key, value)
                    if data:
                        for key, value in data.items():
                            form_data.add_field(key, value)
                    
                    async with self.session.post(url, data=form_data, headers=request_headers) as response:
                        status = response.status
                        try:
                            data = await response.json()
                        except:
                            data = {"text": await response.text()}
                        return status < 400, data, status
                else:
                    # Regular JSON POST
                    if not headers or "Content-Type" not in headers:
                        request_headers["Content-Type"] = "application/json"
                    
                    async with self.session.post(url, json=data, headers=request_headers) as response:
                        status = response.status
                        try:
                            response_data = await response.json()
                        except:
                            response_data = {"text": await response.text()}
                        return status < 400, response_data, status
                        
            elif method.upper() == "PUT":
                request_headers["Content-Type"] = "application/json"
                async with self.session.put(url, json=data, headers=request_headers) as response:
                    status = response.status
                    try:
                        data = await response.json()
                    except:
                        data = {"text": await response.text()}
                    return status < 400, data, status
                    
            elif method.upper() == "DELETE":
                async with self.session.delete(url, headers=request_headers) as response:
                    status = response.status
                    try:
                        data = await response.json()
                    except:
                        data = {"text": await response.text()}
                    return status < 400, data, status
                    
            else:
                return False, {"error": f"Unsupported method: {method}"}, 400
                
        except asyncio.TimeoutError:
            return False, {"error": "Request timeout"}, 408
        except Exception as e:
            return False, {"error": str(e)}, 500
    
    # ============================================
    # 1. TESTES DE AUTENTICAÇÃO
    # ============================================
    
    async def test_admin_login(self) -> bool:
        """Teste 1: Admin login (POST /api/auth/admin/login) - senha: 102030@ab"""
        print("\n🔐 TESTE 1: Admin Login")
        print("=" * 50)
        
        success, response, status = await self.make_request("POST", "/auth/admin/login", {
            "password": ADMIN_PASSWORD
        })
        
        print(f"📊 Status: {status}")
        print(f"📄 Response: {json.dumps(response, indent=2)}")
        
        if success and "token" in response:
            self.admin_token = response["token"]
            self.log_result("Admin Login", True, f"Admin logged in successfully (status: {status})")
            print(f"🔑 Token obtido: {self.admin_token[:50]}...")
            return True
        else:
            self.log_result("Admin Login", False, f"Failed with status {status}: {response}")
            return False
    
    async def test_agent_login(self) -> bool:
        """Teste 2: Atendente login (POST /api/auth/agent/login) - login: leticiaatt, senha: ab181818ab"""
        print("\n👤 TESTE 2: Agent Login")
        print("=" * 50)
        
        success, response, status = await self.make_request("POST", "/auth/agent/login", {
            "login": AGENT_LOGIN,
            "password": AGENT_PASSWORD
        })
        
        print(f"📊 Status: {status}")
        print(f"📄 Response: {json.dumps(response, indent=2)}")
        
        if success and "token" in response:
            self.agent_token = response["token"]
            reseller_id = response.get("reseller_id", "N/A")
            self.log_result("Agent Login", True, f"Agent logged in successfully (status: {status}, reseller_id: {reseller_id})")
            print(f"🔑 Token obtido: {self.agent_token[:50]}...")
            return True
        else:
            self.log_result("Agent Login", False, f"Failed with status {status}: {response}")
            return False
    
    # ============================================
    # 2. TESTES DE DEPARTAMENTOS
    # ============================================
    
    async def test_list_departments(self) -> bool:
        """Teste 3: Listar departamentos (GET /api/ai/departments)"""
        print("\n📂 TESTE 3: Listar Departamentos")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_result("List Departments", False, "Admin token required")
            return False
        
        success, response, status = await self.make_request("GET", "/ai/departments", token=self.admin_token)
        
        print(f"📊 Status: {status}")
        print(f"📄 Response: {json.dumps(response, indent=2)}")
        
        if success and isinstance(response, list):
            department_count = len(response)
            self.log_result("List Departments", True, f"Found {department_count} departments (status: {status})")
            return True
        else:
            self.log_result("List Departments", False, f"Failed with status {status}: {response}")
            return False
    
    async def test_get_agents_for_department(self) -> Optional[str]:
        """Obter ID de um atendente para usar na criação do departamento"""
        print("\n👥 Obtendo lista de agentes...")
        
        if not self.admin_token:
            print("❌ Admin token required")
            return None
        
        success, response, status = await self.make_request("GET", "/agents", token=self.admin_token)
        
        if success and isinstance(response, list) and len(response) > 0:
            agent_id = response[0].get("id")
            agent_name = response[0].get("name", "N/A")
            print(f"✅ Encontrado agente: {agent_name} (ID: {agent_id})")
            return agent_id
        else:
            print(f"⚠️ Nenhum agente encontrado ou erro: {response}")
            return None
    
    async def test_create_department(self) -> bool:
        """Teste 4: Criar departamento com dados específicos"""
        print("\n➕ TESTE 4: Criar Departamento")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_result("Create Department", False, "Admin token required")
            return False
        
        # Obter ID de um agente
        agent_id = await self.test_get_agents_for_department()
        agent_ids = [agent_id] if agent_id else []
        
        department_data = {
            "name": "Teste Completo",
            "agent_ids": agent_ids,
            "origin": "wa_suporte"
        }
        
        success, response, status = await self.make_request("POST", "/ai/departments", department_data, token=self.admin_token)
        
        print(f"📊 Status: {status}")
        print(f"📄 Response: {json.dumps(response, indent=2)}")
        
        if success and response.get("ok"):
            self.created_department_id = response.get("id")
            self.log_result("Create Department", True, f"Department created successfully (status: {status}, ID: {self.created_department_id})")
            return True
        else:
            self.log_result("Create Department", False, f"Failed with status {status}: {response}")
            return False
    
    # ============================================
    # 3. TESTES DE OFFICE SYNC
    # ============================================
    
    async def test_office_sync_statistics(self) -> bool:
        """Teste 5: Verificar estatísticas (GET /api/office-sync/statistics)"""
        print("\n📊 TESTE 5: Office Sync Statistics")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_result("Office Sync Statistics", False, "Admin token required")
            return False
        
        success, response, status = await self.make_request("GET", "/office-sync/statistics", token=self.admin_token)
        
        print(f"📊 Status: {status}")
        print(f"📄 Response: {json.dumps(response, indent=2)}")
        
        if success:
            self.log_result("Office Sync Statistics", True, f"Statistics retrieved successfully (status: {status})")
            return True
        else:
            self.log_result("Office Sync Statistics", False, f"Failed with status {status}: {response}")
            return False
    
    async def test_office_sync_search_clients(self) -> bool:
        """Teste 6: Buscar cliente (POST /api/office-sync/search-clients) com query: "teste" """
        print("\n🔍 TESTE 6: Office Sync Search Clients")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_result("Office Sync Search Clients", False, "Admin token required")
            return False
        
        search_data = {"query": "teste"}
        
        success, response, status = await self.make_request("POST", "/office-sync/search-clients", search_data, token=self.admin_token)
        
        print(f"📊 Status: {status}")
        print(f"📄 Response: {json.dumps(response, indent=2)}")
        
        if success:
            results_count = len(response) if isinstance(response, list) else "N/A"
            self.log_result("Office Sync Search Clients", True, f"Search completed successfully (status: {status}, results: {results_count})")
            return True
        else:
            self.log_result("Office Sync Search Clients", False, f"Failed with status {status}: {response}")
            return False
    
    async def test_office_sync_start_sync(self) -> bool:
        """Teste 7: Iniciar sincronização (POST /api/office-sync/sync-now)"""
        print("\n🔄 TESTE 7: Office Sync Start Sync")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_result("Office Sync Start Sync", False, "Admin token required")
            return False
        
        success, response, status = await self.make_request("POST", "/office-sync/sync-now", {}, token=self.admin_token)
        
        print(f"📊 Status: {status}")
        print(f"📄 Response: {json.dumps(response, indent=2)}")
        
        if success:
            self.log_result("Office Sync Start Sync", True, f"Sync started successfully (status: {status})")
            return True
        else:
            self.log_result("Office Sync Start Sync", False, f"Failed with status {status}: {response}")
            return False
    
    # ============================================
    # 4. TESTES DE BACKUP
    # ============================================
    
    async def test_backup_list(self) -> bool:
        """Teste 8: Listar backups (GET /api/admin/backup/list)"""
        print("\n💾 TESTE 8: Backup List")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_result("Backup List", False, "Admin token required")
            return False
        
        success, response, status = await self.make_request("GET", "/admin/backup/list", token=self.admin_token)
        
        print(f"📊 Status: {status}")
        print(f"📄 Response: {json.dumps(response, indent=2)}")
        
        if success:
            backup_count = len(response) if isinstance(response, list) else "N/A"
            self.log_result("Backup List", True, f"Backup list retrieved successfully (status: {status}, count: {backup_count})")
            return True
        else:
            self.log_result("Backup List", False, f"Failed with status {status}: {response}")
            return False
    
    async def test_backup_create(self) -> bool:
        """Teste 9: Criar backup (POST /api/admin/backup/create)"""
        print("\n💾 TESTE 9: Backup Create")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_result("Backup Create", False, "Admin token required")
            return False
        
        success, response, status = await self.make_request("POST", "/admin/backup/create", {}, token=self.admin_token)
        
        print(f"📊 Status: {status}")
        print(f"📄 Response: {json.dumps(response, indent=2)}")
        
        if success:
            self.log_result("Backup Create", True, f"Backup created successfully (status: {status})")
            return True
        else:
            self.log_result("Backup Create", False, f"Failed with status {status}: {response}")
            return False
    
    # ============================================
    # 5. TESTES DE MÍDIA/UPLOAD
    # ============================================
    
    async def test_media_health_check(self) -> bool:
        """Teste 10: Health check de uploads"""
        print("\n📁 TESTE 10: Media Health Check")
        print("=" * 50)
        
        # Tentar diferentes endpoints possíveis
        endpoints_to_try = ["/media/health", "/uploads/test", "/uploads/health"]
        
        for endpoint in endpoints_to_try:
            print(f"🔍 Tentando endpoint: {endpoint}")
            success, response, status = await self.make_request("GET", endpoint, token=self.admin_token)
            
            print(f"   📊 Status: {status}")
            print(f"   📄 Response: {json.dumps(response, indent=2)}")
            
            if success:
                self.log_result("Media Health Check", True, f"Health check successful on {endpoint} (status: {status})")
                return True
        
        self.log_result("Media Health Check", False, "All media health endpoints failed")
        return False
    
    async def test_upload_simple_file(self) -> bool:
        """Teste 11: Upload simples se houver endpoint"""
        print("\n📤 TESTE 11: Simple File Upload")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_result("Simple File Upload", False, "Admin token required")
            return False
        
        # Criar um arquivo de teste simples
        test_content = b"Teste de upload - " + str(datetime.now()).encode()
        
        # Tentar diferentes endpoints de upload
        upload_endpoints = ["/upload", "/media/upload", "/uploads"]
        
        for endpoint in upload_endpoints:
            print(f"🔍 Tentando upload em: {endpoint}")
            
            files = {"file": test_content}
            success, response, status = await self.make_request("POST", endpoint, files=files, token=self.admin_token)
            
            print(f"   📊 Status: {status}")
            print(f"   📄 Response: {json.dumps(response, indent=2)}")
            
            if success:
                self.log_result("Simple File Upload", True, f"Upload successful on {endpoint} (status: {status})")
                return True
        
        self.log_result("Simple File Upload", False, "All upload endpoints failed")
        return False
    
    # ============================================
    # 6. TESTE DE HEALTH CHECK
    # ============================================
    
    async def test_health_check(self) -> bool:
        """Teste 12: GET /api/health - verificar se MongoDB está conectado"""
        print("\n❤️ TESTE 12: Health Check")
        print("=" * 50)
        
        success, response, status = await self.make_request("GET", "/health")
        
        print(f"📊 Status: {status}")
        print(f"📄 Response: {json.dumps(response, indent=2)}")
        
        if success:
            mongodb_status = response.get("mongodb", "unknown")
            service_status = response.get("status", "unknown")
            
            if mongodb_status == "connected" and service_status == "healthy":
                self.log_result("Health Check", True, f"System healthy, MongoDB connected (status: {status})")
                return True
            else:
                self.log_result("Health Check", False, f"System issues detected: mongodb={mongodb_status}, status={service_status}")
                return False
        else:
            self.log_result("Health Check", False, f"Health check failed with status {status}: {response}")
            return False
    
    # ============================================
    # CLEANUP
    # ============================================
    
    async def cleanup_created_data(self):
        """Limpar dados criados durante os testes"""
        print("\n🧹 Limpando dados de teste...")
        
        if self.created_department_id and self.admin_token:
            print(f"🗑️ Removendo departamento criado: {self.created_department_id}")
            success, response, status = await self.make_request("DELETE", f"/ai/departments/{self.created_department_id}", token=self.admin_token)
            if success:
                print("✅ Departamento removido com sucesso")
            else:
                print(f"⚠️ Falha ao remover departamento: {response}")
    
    # ============================================
    # EXECUÇÃO PRINCIPAL
    # ============================================
    
    async def run_all_tests(self):
        """Executar todos os testes do servidor externo"""
        print("🚀 INICIANDO TESTE COMPLETO DO SERVIDOR EXTERNO")
        print("=" * 80)
        print(f"🌐 Servidor: {EXTERNAL_SERVER_URL}")
        print(f"🔑 Credenciais: Admin ({ADMIN_PASSWORD}), Agent ({AGENT_LOGIN}/{AGENT_PASSWORD})")
        print("=" * 80)
        
        start_time = time.time()
        
        try:
            await self.setup_session()
            
            # Lista de todos os testes
            tests = [
                # 1. AUTENTICAÇÃO
                ("Admin Login", self.test_admin_login),
                ("Agent Login", self.test_agent_login),
                
                # 2. DEPARTAMENTOS
                ("List Departments", self.test_list_departments),
                ("Create Department", self.test_create_department),
                
                # 3. OFFICE SYNC
                ("Office Sync Statistics", self.test_office_sync_statistics),
                ("Office Sync Search Clients", self.test_office_sync_search_clients),
                ("Office Sync Start Sync", self.test_office_sync_start_sync),
                
                # 4. BACKUP
                ("Backup List", self.test_backup_list),
                ("Backup Create", self.test_backup_create),
                
                # 5. MÍDIA/UPLOAD
                ("Media Health Check", self.test_media_health_check),
                ("Simple File Upload", self.test_upload_simple_file),
                
                # 6. HEALTH CHECK
                ("Health Check", self.test_health_check),
            ]
            
            passed = 0
            total = len(tests)
            failed_tests = []
            
            for test_name, test_func in tests:
                try:
                    print(f"\n🔄 Executando: {test_name}")
                    if await test_func():
                        passed += 1
                        print(f"✅ {test_name} PASSOU")
                    else:
                        failed_tests.append(test_name)
                        print(f"❌ {test_name} FALHOU")
                    
                    # Pequena pausa entre testes
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    self.log_result(test_name, False, f"Exception: {str(e)}")
                    failed_tests.append(test_name)
                    print(f"💥 {test_name} ERRO: {str(e)}")
            
            # Cleanup
            await self.cleanup_created_data()
            
            # Resumo final
            end_time = time.time()
            duration = end_time - start_time
            
            print("\n" + "=" * 80)
            print("📊 RESUMO FINAL DOS TESTES")
            print("=" * 80)
            print(f"⏱️ Duração total: {duration:.2f} segundos")
            print(f"📈 Total de testes: {total}")
            print(f"✅ Testes passaram: {passed}")
            print(f"❌ Testes falharam: {total - passed}")
            print(f"📊 Taxa de sucesso: {(passed/total)*100:.1f}%")
            
            print("\n📋 DETALHES DOS TESTES:")
            for i, result in enumerate(self.test_results, 1):
                status_icon = "✅" if result["success"] else "❌"
                print(f"{i:2d}. {status_icon} {result['test']}")
                if result["message"]:
                    print(f"     {result['message']}")
            
            if failed_tests:
                print(f"\n⚠️ TESTES QUE FALHARAM:")
                for i, failed_test in enumerate(failed_tests, 1):
                    print(f"{i:2d}. ❌ {failed_test}")
            
            # Análise específica
            print("\n🎯 ANÁLISE ESPECÍFICA:")
            
            # Verificar se autenticação funcionou
            auth_working = self.admin_token and self.agent_token
            if auth_working:
                print("✅ Sistema de autenticação funcionando (Admin + Agent)")
            else:
                print("❌ Problemas no sistema de autenticação")
            
            # Verificar se endpoints críticos funcionaram
            critical_endpoints = ["Health Check", "List Departments", "Backup List"]
            critical_working = all(any(r["test"] == endpoint and r["success"] for r in self.test_results) for endpoint in critical_endpoints)
            
            if critical_working:
                print("✅ Endpoints críticos funcionando")
            else:
                print("❌ Alguns endpoints críticos com problemas")
            
            # Resultado geral
            if passed == total:
                print("\n🎉 RESULTADO FINAL: SERVIDOR EXTERNO 100% FUNCIONAL!")
                print("✅ Todos os testes passaram - sistema pronto para produção")
                return True
            elif passed >= total * 0.8:  # 80% ou mais
                print("\n🟡 RESULTADO FINAL: SERVIDOR EXTERNO MAJORITARIAMENTE FUNCIONAL")
                print(f"✅ {passed}/{total} testes passaram - alguns ajustes podem ser necessários")
                return True
            else:
                print("\n❌ RESULTADO FINAL: PROBLEMAS SIGNIFICATIVOS DETECTADOS")
                print(f"⚠️ Apenas {passed}/{total} testes passaram - investigação necessária")
                return False
            
        except Exception as e:
            print(f"💥 ERRO CRÍTICO durante execução dos testes: {e}")
            return False
        finally:
            await self.cleanup_session()

async def main():
    """Função principal"""
    tester = ExternalServerTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎯 CONCLUSÃO: Servidor externo funcionando adequadamente!")
        exit(0)
    else:
        print("\n⚠️ CONCLUSÃO: Problemas detectados no servidor externo!")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())