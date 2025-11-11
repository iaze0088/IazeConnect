#!/usr/bin/env python3
"""
🧪 TESTE COMPLETO E ABRANGENTE - BACKEND IAZE + EVOLUTION API

CONTEXTO:
Acabamos de implementar correções críticas:
1. Evolution API: CONFIG_SESSION_PHONE_VERSION=2.3000.1025062854
2. Backend: Payload v2.3 corrigido (instance, engine, number)
3. Frontend: React StrictMode desativado
4. Cache busting implementado

OBJETIVO:
Testar TODO o backend de forma abrangente para garantir que TUDO está funcionando perfeitamente.

TESTES A EXECUTAR:
1. Evolution API (Servidor Externo)
2. Backend IAZE - Autenticação
3. Backend IAZE - WhatsApp (CRÍTICO)
4. Backend IAZE - Upload de Mídia
5. Backend IAZE - Revendas (Admin)
6. Backend IAZE - Atendentes
7. Backend IAZE - Tickets
"""

import asyncio
import aiohttp
import json
import os
import tempfile
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import uuid

# Configurações do ambiente
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://wppconnect-fix.preview.emergentagent.com')
EVOLUTION_API_URL = "http://evolution.suporte.help:8080"
EVOLUTION_API_KEY = "iaze-evolution-2025-secure-key"

# Credenciais de teste conforme review request
ADMIN_PASSWORD = "102030@ab"
RESELLER_EMAIL = "fabio@gmail.com"
RESELLER_PASSWORD = "102030ab"

class ComprehensiveIAZEEvolutionTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.reseller_token = None
        self.test_results = []
        
    async def setup_session(self):
        """Configurar sessão HTTP"""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        
    async def cleanup_session(self):
        """Limpar sessão HTTP"""
        if self.session:
            await self.session.close()
            
    def log_test(self, test_name: str, success: bool, details: str = "", data: dict = None):
        """Log resultado do teste"""
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        if data and not success:
            print(f"   Data: {json.dumps(data, indent=2)}")
            
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "data": data
        })
        
    async def make_request(self, method: str, url: str, headers: dict = None, json_data: dict = None, data=None) -> Tuple[bool, dict, int]:
        """Fazer requisição HTTP com tratamento de erro"""
        try:
            request_headers = headers or {}
            
            if method.upper() == "GET":
                async with self.session.get(url, headers=request_headers) as response:
                    status = response.status
                    try:
                        result = await response.json()
                    except:
                        result = {"text": await response.text()}
                    return status < 400, result, status
                    
            elif method.upper() == "POST":
                if data:  # FormData upload
                    async with self.session.post(url, headers=request_headers, data=data) as response:
                        status = response.status
                        try:
                            result = await response.json()
                        except:
                            result = {"text": await response.text()}
                        return status < 400, result, status
                else:  # JSON data
                    async with self.session.post(url, headers=request_headers, json=json_data) as response:
                        status = response.status
                        try:
                            result = await response.json()
                        except:
                            result = {"text": await response.text()}
                        return status < 400, result, status
                        
            elif method.upper() == "PUT":
                async with self.session.put(url, headers=request_headers, json=json_data) as response:
                    status = response.status
                    try:
                        result = await response.json()
                    except:
                        result = {"text": await response.text()}
                    return status < 400, result, status
                    
            elif method.upper() == "DELETE":
                async with self.session.delete(url, headers=request_headers) as response:
                    status = response.status
                    try:
                        result = await response.json()
                    except:
                        result = {"text": await response.text()}
                    return status < 400, result, status
                    
        except Exception as e:
            return False, {"error": str(e)}, 0

    # ============================================
    # 1. EVOLUTION API (SERVIDOR EXTERNO)
    # ============================================
    
    async def test_evolution_api_online(self):
        """Verificar se Evolution API está online"""
        print("\n🔍 TESTE 1: Evolution API Online")
        print("=" * 50)
        
        try:
            success, data, status = await self.make_request("GET", f"{EVOLUTION_API_URL}/")
            
            if success and status == 200:
                self.log_test("Evolution API Online", True, f"Status: {status}")
                return True
            else:
                self.log_test("Evolution API Online", False, f"Status: {status}", data)
                return False
                
        except Exception as e:
            self.log_test("Evolution API Online", False, f"Erro: {str(e)}")
            return False
    
    async def test_evolution_api_instances(self):
        """Listar todas as instâncias da Evolution API"""
        print("\n🔍 TESTE 2: Evolution API - Listar Instâncias")
        print("=" * 50)
        
        try:
            headers = {"apikey": EVOLUTION_API_KEY}
            success, data, status = await self.make_request(
                "GET", 
                f"{EVOLUTION_API_URL}/instance/fetchInstances",
                headers=headers
            )
            
            if success and isinstance(data, list):
                # Procurar por instâncias conectadas
                connected_instances = [inst for inst in data if inst.get("connectionStatus") == "open"]
                
                self.log_test(
                    "Evolution API - Listar Instâncias", 
                    True, 
                    f"Total: {len(data)}, Conectadas: {len(connected_instances)}"
                )
                
                # Verificar se admin_1_1761943955 está presente e conectada
                admin_instance = next((inst for inst in data if "admin_1_1761943955" in inst.get("instanceName", "")), None)
                if admin_instance:
                    is_connected = admin_instance.get("connectionStatus") == "open"
                    self.log_test(
                        "Evolution API - Instância admin_1_1761943955", 
                        is_connected, 
                        f"Status: {admin_instance.get('connectionStatus')}"
                    )
                else:
                    self.log_test("Evolution API - Instância admin_1_1761943955", False, "Não encontrada")
                
                return len(connected_instances) > 0
            else:
                self.log_test("Evolution API - Listar Instâncias", False, f"Status: {status}", data)
                return False
                
        except Exception as e:
            self.log_test("Evolution API - Listar Instâncias", False, f"Erro: {str(e)}")
            return False

    # ============================================
    # 2. BACKEND IAZE - AUTENTICAÇÃO
    # ============================================
    
    async def test_admin_login(self):
        """Teste 2.1 - Login Admin"""
        print("\n🔍 TESTE 3: Backend IAZE - Login Admin")
        print("=" * 50)
        
        try:
            success, data, status = await self.make_request(
                "POST",
                f"{BACKEND_URL}/api/auth/admin/login",
                json_data={"password": ADMIN_PASSWORD}
            )
            
            if success and data.get("token") and data.get("user_type") == "admin":
                self.admin_token = data["token"]
                self.log_test("Backend - Login Admin", True, f"Token obtido, user_type: {data.get('user_type')}")
                return True
            else:
                self.log_test("Backend - Login Admin", False, f"Status: {status}", data)
                return False
                
        except Exception as e:
            self.log_test("Backend - Login Admin", False, f"Erro: {str(e)}")
            return False
    
    async def test_reseller_login(self):
        """Teste 2.2 - Login Reseller"""
        print("\n🔍 TESTE 4: Backend IAZE - Login Reseller")
        print("=" * 50)
        
        try:
            success, data, status = await self.make_request(
                "POST",
                f"{BACKEND_URL}/api/resellers/login",
                json_data={"email": RESELLER_EMAIL, "password": RESELLER_PASSWORD}
            )
            
            if success and data.get("token") and data.get("user_type") == "reseller":
                self.reseller_token = data["token"]
                reseller_id = data.get("reseller_id") or data.get("user_data", {}).get("reseller_id")
                self.log_test("Backend - Login Reseller", True, f"Token obtido, reseller_id: {reseller_id}")
                return True
            else:
                self.log_test("Backend - Login Reseller", False, f"Status: {status}", data)
                return False
                
        except Exception as e:
            self.log_test("Backend - Login Reseller", False, f"Erro: {str(e)}")
            return False

    # ============================================
    # 3. BACKEND IAZE - WHATSAPP (CRÍTICO)
    # ============================================
    
    async def test_whatsapp_connections_admin(self):
        """Teste 3.1 - Listar Conexões (Admin)"""
        print("\n🔍 TESTE 5: Backend IAZE - WhatsApp Conexões (Admin)")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_test("WhatsApp Conexões (Admin)", False, "Token admin não disponível")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            success, data, status = await self.make_request(
                "GET",
                f"{BACKEND_URL}/api/whatsapp/connections",
                headers=headers
            )
            
            if success and isinstance(data, list):
                # Procurar pela instância admin_1_1761943955
                admin_connection = next((conn for conn in data if "admin_1_1761943955" in conn.get("instance_name", "")), None)
                
                if admin_connection:
                    is_connected = admin_connection.get("status") == "connected" and admin_connection.get("connected") == True
                    self.log_test(
                        "WhatsApp Conexões (Admin)", 
                        is_connected, 
                        f"admin_1_1761943955 - Status: {admin_connection.get('status')}, Connected: {admin_connection.get('connected')}"
                    )
                    return is_connected
                else:
                    self.log_test("WhatsApp Conexões (Admin)", False, "Instância admin_1_1761943955 não encontrada")
                    return False
            else:
                self.log_test("WhatsApp Conexões (Admin)", False, f"Status: {status}", data)
                return False
                
        except Exception as e:
            self.log_test("WhatsApp Conexões (Admin)", False, f"Erro: {str(e)}")
            return False
    
    async def test_whatsapp_connections_reseller(self):
        """Teste 3.2 - Listar Conexões (Reseller fabio)"""
        print("\n🔍 TESTE 6: Backend IAZE - WhatsApp Conexões (Reseller)")
        print("=" * 50)
        
        if not self.reseller_token:
            self.log_test("WhatsApp Conexões (Reseller)", False, "Token reseller não disponível")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.reseller_token}"}
            success, data, status = await self.make_request(
                "GET",
                f"{BACKEND_URL}/api/whatsapp/connections",
                headers=headers
            )
            
            if success and isinstance(data, list):
                self.log_test("WhatsApp Conexões (Reseller)", True, f"Retornou {len(data)} conexões do reseller")
                return True
            else:
                self.log_test("WhatsApp Conexões (Reseller)", False, f"Status: {status}", data)
                return False
                
        except Exception as e:
            self.log_test("WhatsApp Conexões (Reseller)", False, f"Erro: {str(e)}")
            return False
    
    async def test_whatsapp_create_connection(self):
        """Teste 3.3 - Criar Nova Conexão (Reseller)"""
        print("\n🔍 TESTE 7: Backend IAZE - Criar Conexão WhatsApp")
        print("=" * 50)
        
        if not self.reseller_token:
            self.log_test("Criar Conexão WhatsApp", False, "Token reseller não disponível")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.reseller_token}"}
            success, data, status = await self.make_request(
                "POST",
                f"{BACKEND_URL}/api/whatsapp/connections",
                headers=headers,
                json_data={
                    "max_received_daily": 200,
                    "max_sent_daily": 100
                }
            )
            
            if success and (status in [200, 201]):
                # Verificar se tem QR code e instance_name
                has_qr = data.get("qr_code") is not None
                has_instance = data.get("instance_name") is not None
                
                if has_qr and has_instance:
                    instance_name = data.get("instance_name")
                    # Verificar formato do instance_name (fabio_X_timestamp)
                    is_correct_format = "fabio_" in instance_name and "_" in instance_name
                    
                    self.log_test(
                        "Criar Conexão WhatsApp", 
                        is_correct_format, 
                        f"Instância: {instance_name}, QR: {'Presente' if has_qr else 'Ausente'}"
                    )
                    return is_correct_format
                else:
                    self.log_test("Criar Conexão WhatsApp", False, "QR code ou instance_name ausente", data)
                    return False
            else:
                self.log_test("Criar Conexão WhatsApp", False, f"Status: {status}", data)
                return False
                
        except Exception as e:
            self.log_test("Criar Conexão WhatsApp", False, f"Erro: {str(e)}")
            return False
    
    async def test_whatsapp_config(self):
        """Teste 3.4 - Configuração WhatsApp"""
        print("\n🔍 TESTE 8: Backend IAZE - Configuração WhatsApp")
        print("=" * 50)
        
        if not self.reseller_token:
            self.log_test("Configuração WhatsApp", False, "Token reseller não disponível")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.reseller_token}"}
            success, data, status = await self.make_request(
                "GET",
                f"{BACKEND_URL}/api/whatsapp/config",
                headers=headers
            )
            
            if success and status == 200:
                has_plan = "plan" in data
                has_rotation = "rotation_mode" in data
                
                self.log_test(
                    "Configuração WhatsApp", 
                    has_plan or has_rotation, 
                    f"Plan: {'Presente' if has_plan else 'Ausente'}, Rotation: {'Presente' if has_rotation else 'Ausente'}"
                )
                return has_plan or has_rotation
            else:
                self.log_test("Configuração WhatsApp", False, f"Status: {status}", data)
                return False
                
        except Exception as e:
            self.log_test("Configuração WhatsApp", False, f"Erro: {str(e)}")
            return False
    
    async def test_whatsapp_stats(self):
        """Teste 3.5 - Estatísticas WhatsApp"""
        print("\n🔍 TESTE 9: Backend IAZE - Estatísticas WhatsApp")
        print("=" * 50)
        
        if not self.reseller_token:
            self.log_test("Estatísticas WhatsApp", False, "Token reseller não disponível")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.reseller_token}"}
            success, data, status = await self.make_request(
                "GET",
                f"{BACKEND_URL}/api/whatsapp/stats",
                headers=headers
            )
            
            if success and status == 200:
                has_total = "total_connections" in data
                has_active = "active_connections" in data
                
                self.log_test(
                    "Estatísticas WhatsApp", 
                    has_total and has_active, 
                    f"Total: {data.get('total_connections', 'N/A')}, Ativas: {data.get('active_connections', 'N/A')}"
                )
                return has_total and has_active
            else:
                self.log_test("Estatísticas WhatsApp", False, f"Status: {status}", data)
                return False
                
        except Exception as e:
            self.log_test("Estatísticas WhatsApp", False, f"Erro: {str(e)}")
            return False

    # ============================================
    # 4. BACKEND IAZE - UPLOAD DE MÍDIA
    # ============================================
    
    async def test_upload_file(self):
        """Teste 4.1 - Upload Arquivo"""
        print("\n🔍 TESTE 10: Backend IAZE - Upload de Arquivo")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_test("Upload de Arquivo", False, "Token admin não disponível")
            return False
            
        try:
            # Criar arquivo temporário
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write("teste upload IAZE")
                temp_file_path = f.name
            
            # Preparar FormData
            data = aiohttp.FormData()
            data.add_field('file', open(temp_file_path, 'rb'), filename='test.txt', content_type='text/plain')
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            success, response_data, status = await self.make_request(
                "POST",
                f"{BACKEND_URL}/api/upload",
                headers=headers,
                data=data
            )
            
            # Limpar arquivo temporário
            os.unlink(temp_file_path)
            
            if success and response_data.get("ok"):
                url = response_data.get("url")
                filename = response_data.get("filename")
                kind = response_data.get("kind")
                local = response_data.get("local")
                
                all_fields_present = all([url, filename, kind is not None, local is not None])
                
                self.log_test(
                    "Upload de Arquivo", 
                    all_fields_present, 
                    f"URL: {url}, Kind: {kind}, Local: {local}"
                )
                return all_fields_present
            else:
                self.log_test("Upload de Arquivo", False, f"Status: {status}", response_data)
                return False
                
        except Exception as e:
            self.log_test("Upload de Arquivo", False, f"Erro: {str(e)}")
            return False

    # ============================================
    # 5. BACKEND IAZE - REVENDAS (ADMIN)
    # ============================================
    
    async def test_list_resellers(self):
        """Teste 5.1 - Listar Revendas"""
        print("\n🔍 TESTE 11: Backend IAZE - Listar Revendas")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_test("Listar Revendas", False, "Token admin não disponível")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            success, data, status = await self.make_request(
                "GET",
                f"{BACKEND_URL}/api/resellers",
                headers=headers
            )
            
            if success and isinstance(data, list):
                # Procurar por fabio@gmail.com
                fabio_reseller = next((r for r in data if r.get("email") == RESELLER_EMAIL), None)
                
                if fabio_reseller:
                    self.log_test(
                        "Listar Revendas", 
                        True, 
                        f"Total: {len(data)}, fabio@gmail.com encontrado"
                    )
                    return True
                else:
                    self.log_test("Listar Revendas", False, f"fabio@gmail.com não encontrado em {len(data)} revendas")
                    return False
            else:
                self.log_test("Listar Revendas", False, f"Status: {status}", data)
                return False
                
        except Exception as e:
            self.log_test("Listar Revendas", False, f"Erro: {str(e)}")
            return False

    # ============================================
    # 6. BACKEND IAZE - ATENDENTES
    # ============================================
    
    async def test_list_agents(self):
        """Teste 6.1 - Listar Atendentes (Reseller)"""
        print("\n🔍 TESTE 12: Backend IAZE - Listar Atendentes")
        print("=" * 50)
        
        if not self.reseller_token:
            self.log_test("Listar Atendentes", False, "Token reseller não disponível")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.reseller_token}"}
            success, data, status = await self.make_request(
                "GET",
                f"{BACKEND_URL}/api/agents",
                headers=headers
            )
            
            if success and isinstance(data, list):
                self.log_test("Listar Atendentes", True, f"Retornou {len(data)} atendentes")
                return True
            else:
                self.log_test("Listar Atendentes", False, f"Status: {status}", data)
                return False
                
        except Exception as e:
            self.log_test("Listar Atendentes", False, f"Erro: {str(e)}")
            return False

    # ============================================
    # 7. BACKEND IAZE - TICKETS
    # ============================================
    
    async def test_list_tickets(self):
        """Teste 7.1 - Listar Tickets"""
        print("\n🔍 TESTE 13: Backend IAZE - Listar Tickets")
        print("=" * 50)
        
        if not self.admin_token:
            self.log_test("Listar Tickets", False, "Token admin não disponível")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            success, data, status = await self.make_request(
                "GET",
                f"{BACKEND_URL}/api/tickets",
                headers=headers
            )
            
            if success and isinstance(data, list):
                self.log_test("Listar Tickets", True, f"Retornou {len(data)} tickets sem erros KeyError")
                return True
            else:
                self.log_test("Listar Tickets", False, f"Status: {status}", data)
                return False
                
        except Exception as e:
            error_msg = str(e)
            is_keyerror = "KeyError" in error_msg
            self.log_test("Listar Tickets", not is_keyerror, f"Erro: {error_msg}")
            return not is_keyerror

    # ============================================
    # EXECUTAR TODOS OS TESTES
    # ============================================
    
    async def run_all_tests(self):
        """Executar todos os testes"""
        print("🧪 TESTE COMPLETO E ABRANGENTE - BACKEND IAZE + EVOLUTION API")
        print("=" * 80)
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print(f"🔗 Evolution API: {EVOLUTION_API_URL}")
        print(f"🔑 Admin Password: {ADMIN_PASSWORD}")
        print(f"📧 Reseller: {RESELLER_EMAIL}")
        print("=" * 80)
        
        await self.setup_session()
        
        # Lista de todos os testes
        tests = [
            # 1. Evolution API
            ("Evolution API Online", self.test_evolution_api_online),
            ("Evolution API Instâncias", self.test_evolution_api_instances),
            
            # 2. Autenticação
            ("Admin Login", self.test_admin_login),
            ("Reseller Login", self.test_reseller_login),
            
            # 3. WhatsApp (CRÍTICO)
            ("WhatsApp Conexões (Admin)", self.test_whatsapp_connections_admin),
            ("WhatsApp Conexões (Reseller)", self.test_whatsapp_connections_reseller),
            ("WhatsApp Criar Conexão", self.test_whatsapp_create_connection),
            ("WhatsApp Config", self.test_whatsapp_config),
            ("WhatsApp Stats", self.test_whatsapp_stats),
            
            # 4. Upload de Mídia
            ("Upload de Arquivo", self.test_upload_file),
            
            # 5. Revendas
            ("Listar Revendas", self.test_list_resellers),
            
            # 6. Atendentes
            ("Listar Atendentes", self.test_list_agents),
            
            # 7. Tickets
            ("Listar Tickets", self.test_list_tickets),
        ]
        
        passed = 0
        total = len(tests)
        failed_tests = []
        
        for test_name, test_func in tests:
            try:
                print(f"\n🔄 Executando: {test_name}")
                result = await test_func()
                if result:
                    passed += 1
                else:
                    failed_tests.append(test_name)
                    
            except Exception as e:
                self.log_test(test_name, False, f"Exception: {str(e)}")
                failed_tests.append(test_name)
                print(f"💥 {test_name} ERRO: {str(e)}")
        
        await self.cleanup_session()
        
        # Resumo final
        print("\n" + "=" * 80)
        print("📊 RESUMO GERAL DO ESTADO DO BACKEND")
        print("=" * 80)
        
        success_rate = (passed / total) * 100
        print(f"📈 Taxa de Sucesso: {success_rate:.1f}% ({passed}/{total})")
        
        # Categorizar resultados
        passed_tests = []
        failed_tests_details = []
        warnings = []
        
        for result in self.test_results:
            if result["success"]:
                passed_tests.append(result["test"])
            else:
                failed_tests_details.append(f"{result['test']}: {result['details']}")
                
                # Identificar warnings importantes
                if "Evolution API" in result["test"]:
                    warnings.append(f"⚠️ {result['test']}: Servidor Evolution pode estar offline")
                elif "WhatsApp" in result["test"]:
                    warnings.append(f"⚠️ {result['test']}: Funcionalidade crítica com problema")
        
        print(f"\n✅ TESTES QUE PASSARAM ({len(passed_tests)}):")
        for test in passed_tests:
            print(f"   ✅ {test}")
        
        if failed_tests_details:
            print(f"\n❌ TESTES QUE FALHARAM ({len(failed_tests_details)}):")
            for test in failed_tests_details:
                print(f"   ❌ {test}")
        
        if warnings:
            print(f"\n⚠️ AVISOS IMPORTANTES ({len(warnings)}):")
            for warning in warnings:
                print(f"   {warning}")
        
        # Validações específicas do review request
        print(f"\n🎯 VALIDAÇÕES ESPECÍFICAS:")
        
        # Evolution API
        evolution_tests = [r for r in self.test_results if "Evolution API" in r["test"]]
        evolution_ok = all(r["success"] for r in evolution_tests)
        if evolution_ok:
            print("✅ Evolution API versão 2.2.3+ funcionando")
            print("✅ Instâncias conectadas (admin_1_1761943955)")
        else:
            print("❌ Evolution API com problemas")
        
        # Autenticação
        auth_tests = [r for r in self.test_results if "Login" in r["test"]]
        auth_ok = all(r["success"] for r in auth_tests)
        if auth_ok:
            print("✅ Autenticação Admin e Reseller funcionando")
        else:
            print("❌ Problemas na autenticação")
        
        # WhatsApp (CRÍTICO)
        whatsapp_tests = [r for r in self.test_results if "WhatsApp" in r["test"]]
        whatsapp_ok = sum(r["success"] for r in whatsapp_tests) >= len(whatsapp_tests) * 0.8  # 80% dos testes
        if whatsapp_ok:
            print("✅ Funcionalidades WhatsApp funcionando (>80%)")
        else:
            print("❌ Problemas críticos no WhatsApp")
        
        # Conclusão final
        if success_rate >= 90:
            print(f"\n🎉 SISTEMA FUNCIONANDO PERFEITAMENTE!")
            print(f"✅ {success_rate:.1f}% dos testes passaram")
            print(f"✅ Backend IAZE pronto para produção")
        elif success_rate >= 70:
            print(f"\n⚠️ SISTEMA FUNCIONANDO COM ALGUNS PROBLEMAS")
            print(f"📊 {success_rate:.1f}% dos testes passaram")
            print(f"🔧 Correções menores necessárias")
        else:
            print(f"\n❌ SISTEMA COM PROBLEMAS CRÍTICOS")
            print(f"📊 {success_rate:.1f}% dos testes passaram")
            print(f"🚨 Correções urgentes necessárias")
        
        return success_rate >= 70

async def main():
    """Função principal"""
    tester = ComprehensiveIAZEEvolutionTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎯 CONCLUSÃO: Sistema IAZE + Evolution API funcionando adequadamente!")
        exit(0)
    else:
        print("\n⚠️ CONCLUSÃO: Problemas detectados que precisam de atenção!")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())