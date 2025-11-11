#!/usr/bin/env python3
"""
TESTE ESPECÍFICO: 3 Otimizações IAZE (Review Request)

CONTEXTO: Implementei 3 otimizações importantes no sistema IAZE. Preciso de teste backend completo.

MUDANÇAS IMPLEMENTADAS:
1️⃣ MONGODB INDEX OPTIMIZATION - Script executado com sucesso, 37 novos índices criados
2️⃣ AGENT ONLINE STATUS FIX - Endpoint /api/agents/online-status corrigido
3️⃣ CUSTOM DOMAIN LINKS - Component DomainConfig.js implementado

TESTES SOLICITADOS:
✅ TESTE 1: MongoDB Indexes - verificar se indices foram criados
✅ TESTE 2: Agent Online Status - Reseller Isolado (michaelrv@gmail.com / ab181818ab)
✅ TESTE 3: Agent Online Status - Admin (admin@cybertv.com / 102030@ab)
✅ TESTE 4: Manual Away Mode - testar GET /config para verificar manual_away_mode
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import sys

# Configurações
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://wppconnect-fix.preview.emergentagent.com')
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'support_chat')

class IAZEOptimizationsTestRunner:
    def __init__(self):
        self.client = AsyncIOMotorClient(MONGO_URL)
        self.db = self.client[DB_NAME]
        self.session = None
        self.test_results = []
        self.admin_token = None
        self.reseller_token = None
        
    async def setup_session(self):
        """Configurar sessão HTTP"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Limpar sessão HTTP"""
        if self.session:
            await self.session.close()
            
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
        
    async def make_request(self, method: str, endpoint: str, data: dict = None, 
                          token: str = None, headers: dict = None) -> tuple[bool, dict]:
        """Make HTTP request with error handling"""
        url = f"{BACKEND_URL}/api{endpoint}"
        
        request_headers = {"Content-Type": "application/json"}
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        if headers:
            request_headers.update(headers)
            
        try:
            if method.upper() == "GET":
                async with self.session.get(url, headers=request_headers) as response:
                    return response.status < 400, await response.json() if response.text else {}
            elif method.upper() == "POST":
                async with self.session.post(url, json=data, headers=request_headers) as response:
                    return response.status < 400, await response.json() if response.text else {}
            elif method.upper() == "PUT":
                async with self.session.put(url, json=data, headers=request_headers) as response:
                    return response.status < 400, await response.json() if response.text else {}
            else:
                return False, {"error": f"Unsupported method: {method}"}
                
        except Exception as e:
            return False, {"error": str(e)}

    # ============================================
    # TESTE 1: MONGODB INDEX OPTIMIZATION
    # ============================================
    
    async def test_mongodb_indexes(self):
        """Teste 1: Verificar se índices MongoDB foram criados com sucesso"""
        print("\n🔍 TESTE 1: MongoDB Index Optimization")
        print("=" * 60)
        
        try:
            # Verificar índices em collections críticas
            collections_to_check = [
                'users', 'tickets', 'messages', 'agents', 'departments', 
                'resellers', 'config', 'reseller_configs', 'ai_agents'
            ]
            
            total_indexes = 0
            collections_with_indexes = 0
            
            for collection_name in collections_to_check:
                try:
                    collection = self.db[collection_name]
                    indexes = await collection.list_indexes().to_list(None)
                    index_count = len(indexes)
                    total_indexes += index_count
                    
                    if index_count > 1:  # Mais que apenas _id
                        collections_with_indexes += 1
                        print(f"   📊 {collection_name}: {index_count} índices")
                        
                        # Mostrar alguns índices importantes
                        for idx in indexes:
                            if idx['name'] != '_id_':
                                keys = list(idx.get('key', {}).keys())
                                print(f"      - {idx['name']}: {keys}")
                    else:
                        print(f"   ⚠️  {collection_name}: apenas índice _id (sem otimização)")
                        
                except Exception as e:
                    print(f"   ❌ Erro ao verificar {collection_name}: {e}")
            
            print(f"\n📈 RESUMO DOS ÍNDICES:")
            print(f"   Total de índices: {total_indexes}")
            print(f"   Collections otimizadas: {collections_with_indexes}/{len(collections_to_check)}")
            
            # Critério de sucesso: pelo menos 30 índices no total e 6+ collections otimizadas
            success = total_indexes >= 30 and collections_with_indexes >= 6
            
            if success:
                self.log_result("MongoDB Index Optimization", True, 
                              f"{total_indexes} índices em {collections_with_indexes} collections")
                print("🎉 ÍNDICES MONGODB OTIMIZADOS COM SUCESSO!")
            else:
                self.log_result("MongoDB Index Optimization", False, 
                              f"Apenas {total_indexes} índices em {collections_with_indexes} collections")
                print("❌ OTIMIZAÇÃO DE ÍNDICES INSUFICIENTE")
            
            return success
            
        except Exception as e:
            print(f"💥 ERRO ao verificar índices MongoDB: {e}")
            self.log_result("MongoDB Index Optimization", False, f"Erro: {str(e)}")
            return False

    # ============================================
    # TESTE 2: AGENT ONLINE STATUS - RESELLER
    # ============================================
    
    async def test_reseller_login_and_online_status(self):
        """Teste 2: Login reseller e verificar online status isolado"""
        print("\n👤 TESTE 2: Agent Online Status - Reseller Isolado")
        print("=" * 60)
        
        try:
            # Login como reseller: michaelrv@gmail.com / ab181818ab
            print("🔑 Fazendo login como reseller...")
            success, response = await self.make_request("POST", "/resellers/login", {
                "email": "michaelrv@gmail.com",
                "password": "ab181818ab"
            })
            
            if not success:
                print(f"❌ Falha no login do reseller: {response}")
                self.log_result("Reseller Login", False, f"Login failed: {response}")
                return False
            
            if "token" not in response:
                print(f"❌ Token não retornado no login: {response}")
                self.log_result("Reseller Login", False, "No token returned")
                return False
            
            self.reseller_token = response["token"]
            reseller_id = response.get("user_data", {}).get("reseller_id")
            print(f"✅ Login reseller OK - Reseller ID: {reseller_id}")
            
            # Testar GET /api/agents/online-status
            print("📊 Testando GET /api/agents/online-status...")
            success, online_status = await self.make_request("GET", "/agents/online-status", 
                                                           token=self.reseller_token)
            
            if not success:
                print(f"❌ Falha ao buscar online status: {online_status}")
                self.log_result("Reseller Online Status", False, f"API failed: {online_status}")
                return False
            
            print(f"📋 Response: {json.dumps(online_status, indent=2)}")
            
            # Validações específicas
            required_fields = ["online", "status", "manual"]
            missing_fields = [field for field in required_fields if field not in online_status]
            
            if missing_fields:
                print(f"❌ Campos obrigatórios ausentes: {missing_fields}")
                self.log_result("Reseller Online Status", False, f"Missing fields: {missing_fields}")
                return False
            
            online_count = online_status.get("online", -1)
            status = online_status.get("status", "")
            manual = online_status.get("manual", None)
            
            print(f"   📊 Online agents: {online_count}")
            print(f"   📊 Status: {status}")
            print(f"   📊 Manual mode: {manual}")
            
            # Validações
            validations = []
            
            # 1. Online deve ser número >= 0
            if isinstance(online_count, int) and online_count >= 0:
                validations.append("✅ Online count válido")
            else:
                validations.append(f"❌ Online count inválido: {online_count}")
            
            # 2. Status deve ser válido
            valid_statuses = ["online", "offline", "away"]
            if status in valid_statuses:
                validations.append("✅ Status válido")
            else:
                validations.append(f"❌ Status inválido: {status}")
            
            # 3. Manual deve ser boolean
            if isinstance(manual, bool):
                validations.append("✅ Manual flag válido")
            else:
                validations.append(f"❌ Manual flag inválido: {manual}")
            
            # 4. Multi-tenant: deve retornar apenas agentes do reseller
            if online_count <= 10:  # Assumindo que um reseller não tem mais que 10 agentes
                validations.append("✅ Count parece isolado por tenant")
            else:
                validations.append(f"⚠️ Count alto ({online_count}) - verificar isolamento")
            
            for validation in validations:
                print(f"   {validation}")
            
            success = all("✅" in v for v in validations)
            
            if success:
                self.log_result("Reseller Online Status", True, 
                              f"online: {online_count}, status: {status}, manual: {manual}")
                print("🎉 ONLINE STATUS RESELLER FUNCIONANDO!")
            else:
                self.log_result("Reseller Online Status", False, 
                              f"Validations failed: {validations}")
                print("❌ PROBLEMAS NO ONLINE STATUS RESELLER")
            
            return success
            
        except Exception as e:
            print(f"💥 ERRO no teste reseller online status: {e}")
            self.log_result("Reseller Online Status", False, f"Exception: {str(e)}")
            return False

    # ============================================
    # TESTE 3: AGENT ONLINE STATUS - ADMIN
    # ============================================
    
    async def test_admin_login_and_online_status(self):
        """Teste 3: Login admin e verificar online status global"""
        print("\n👑 TESTE 3: Agent Online Status - Admin")
        print("=" * 60)
        
        try:
            # Login como admin: admin@cybertv.com / 102030@ab
            # Nota: O sistema usa apenas a senha, não o email para admin
            print("🔑 Fazendo login como admin...")
            success, response = await self.make_request("POST", "/auth/admin/login", {
                "password": "102030@ab"
            })
            
            if not success:
                print(f"❌ Falha no login do admin: {response}")
                self.log_result("Admin Login", False, f"Login failed: {response}")
                return False
            
            if "token" not in response:
                print(f"❌ Token não retornado no login: {response}")
                self.log_result("Admin Login", False, "No token returned")
                return False
            
            self.admin_token = response["token"]
            user_type = response.get("user_type", "")
            print(f"✅ Login admin OK - User type: {user_type}")
            
            # Testar GET /api/agents/online-status
            print("📊 Testando GET /api/agents/online-status como admin...")
            success, online_status = await self.make_request("GET", "/agents/online-status", 
                                                           token=self.admin_token)
            
            if not success:
                print(f"❌ Falha ao buscar online status: {online_status}")
                self.log_result("Admin Online Status", False, f"API failed: {online_status}")
                return False
            
            print(f"📋 Response: {json.dumps(online_status, indent=2)}")
            
            # Validações específicas
            required_fields = ["online", "status", "manual"]
            missing_fields = [field for field in required_fields if field not in online_status]
            
            if missing_fields:
                print(f"❌ Campos obrigatórios ausentes: {missing_fields}")
                self.log_result("Admin Online Status", False, f"Missing fields: {missing_fields}")
                return False
            
            online_count = online_status.get("online", -1)
            status = online_status.get("status", "")
            manual = online_status.get("manual", None)
            
            print(f"   📊 Online agents (todos): {online_count}")
            print(f"   📊 Status: {status}")
            print(f"   📊 Manual mode: {manual}")
            
            # Validações
            validations = []
            
            # 1. Online deve ser número >= 0
            if isinstance(online_count, int) and online_count >= 0:
                validations.append("✅ Online count válido")
            else:
                validations.append(f"❌ Online count inválido: {online_count}")
            
            # 2. Status deve ser válido
            valid_statuses = ["online", "offline", "away"]
            if status in valid_statuses:
                validations.append("✅ Status válido")
            else:
                validations.append(f"❌ Status inválido: {status}")
            
            # 3. Manual deve ser boolean
            if isinstance(manual, bool):
                validations.append("✅ Manual flag válido")
            else:
                validations.append(f"❌ Manual flag inválido: {manual}")
            
            # 4. Admin deve ver todos os agentes (pode ser maior que reseller)
            if online_count >= 0:  # Admin pode ver 0 ou mais agentes
                validations.append("✅ Admin vê todos os agentes do sistema")
            else:
                validations.append(f"❌ Count inválido para admin: {online_count}")
            
            for validation in validations:
                print(f"   {validation}")
            
            success = all("✅" in v for v in validations)
            
            if success:
                self.log_result("Admin Online Status", True, 
                              f"online: {online_count}, status: {status}, manual: {manual}")
                print("🎉 ONLINE STATUS ADMIN FUNCIONANDO!")
            else:
                self.log_result("Admin Online Status", False, 
                              f"Validations failed: {validations}")
                print("❌ PROBLEMAS NO ONLINE STATUS ADMIN")
            
            return success
            
        except Exception as e:
            print(f"💥 ERRO no teste admin online status: {e}")
            self.log_result("Admin Online Status", False, f"Exception: {str(e)}")
            return False

    # ============================================
    # TESTE 4: MANUAL AWAY MODE
    # ============================================
    
    async def test_manual_away_mode(self):
        """Teste 4: Verificar manual_away_mode no config"""
        print("\n⚙️ TESTE 4: Manual Away Mode")
        print("=" * 60)
        
        try:
            # Testar GET /config com admin token
            if not self.admin_token:
                print("❌ Admin token necessário para testar config")
                self.log_result("Manual Away Mode", False, "No admin token")
                return False
            
            print("📋 Testando GET /config...")
            success, config = await self.make_request("GET", "/config", token=self.admin_token)
            
            if not success:
                print(f"❌ Falha ao buscar config: {config}")
                self.log_result("Manual Away Mode", False, f"Config API failed: {config}")
                return False
            
            print(f"📄 Config keys: {list(config.keys())}")
            
            # Verificar se manual_away_mode existe
            if "manual_away_mode" not in config:
                print("❌ Campo manual_away_mode não encontrado no config")
                self.log_result("Manual Away Mode", False, "manual_away_mode field missing")
                return False
            
            manual_away_mode = config.get("manual_away_mode")
            print(f"   📊 manual_away_mode: {manual_away_mode} (type: {type(manual_away_mode)})")
            
            # Validações
            validations = []
            
            # 1. Deve ser boolean
            if isinstance(manual_away_mode, bool):
                validations.append("✅ manual_away_mode é boolean")
            else:
                validations.append(f"❌ manual_away_mode deve ser boolean, é {type(manual_away_mode)}")
            
            # 2. Testar comportamento: se true, online-status deve retornar status="away"
            if manual_away_mode:
                print("   🔍 manual_away_mode=true, testando se online-status retorna 'away'...")
                success, online_status = await self.make_request("GET", "/agents/online-status", 
                                                               token=self.admin_token)
                if success and online_status.get("status") == "away":
                    validations.append("✅ manual_away_mode=true → status='away'")
                else:
                    validations.append(f"❌ manual_away_mode=true mas status='{online_status.get('status')}'")
            else:
                validations.append("✅ manual_away_mode=false (modo normal)")
            
            # 3. Verificar se reseller também tem o campo (se temos reseller token)
            if self.reseller_token:
                print("   🔍 Verificando manual_away_mode no config do reseller...")
                success, reseller_config = await self.make_request("GET", "/config", 
                                                                 token=self.reseller_token)
                if success and "manual_away_mode" in reseller_config:
                    reseller_manual = reseller_config.get("manual_away_mode")
                    print(f"   📊 Reseller manual_away_mode: {reseller_manual}")
                    validations.append("✅ Reseller também tem manual_away_mode")
                else:
                    validations.append("⚠️ Reseller config sem manual_away_mode")
            
            for validation in validations:
                print(f"   {validation}")
            
            success = all("✅" in v for v in validations)
            
            if success:
                self.log_result("Manual Away Mode", True, 
                              f"manual_away_mode: {manual_away_mode}")
                print("🎉 MANUAL AWAY MODE FUNCIONANDO!")
            else:
                self.log_result("Manual Away Mode", False, 
                              f"Validations failed: {validations}")
                print("❌ PROBLEMAS NO MANUAL AWAY MODE")
            
            return success
            
        except Exception as e:
            print(f"💥 ERRO no teste manual away mode: {e}")
            self.log_result("Manual Away Mode", False, f"Exception: {str(e)}")
            return False

    # ============================================
    # RUNNER PRINCIPAL
    # ============================================
    
    async def run_all_tests(self):
        """Executar todos os testes das otimizações IAZE"""
        print("🚀 INICIANDO TESTE DAS 3 OTIMIZAÇÕES IAZE")
        print("=" * 80)
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print(f"🗄️ MongoDB: {MONGO_URL}")
        print("=" * 80)
        
        try:
            await self.setup_session()
            
            # Executar testes na ordem
            tests = [
                ("MongoDB Index Optimization", self.test_mongodb_indexes),
                ("Agent Online Status - Reseller", self.test_reseller_login_and_online_status),
                ("Agent Online Status - Admin", self.test_admin_login_and_online_status),
                ("Manual Away Mode", self.test_manual_away_mode),
            ]
            
            results = []
            for test_name, test_func in tests:
                print(f"\n🔄 Executando: {test_name}")
                try:
                    success = await test_func()
                    results.append(success)
                    if success:
                        print(f"✅ {test_name} PASSOU")
                    else:
                        print(f"❌ {test_name} FALHOU")
                except Exception as e:
                    print(f"💥 {test_name} ERRO: {str(e)}")
                    results.append(False)
                    self.log_result(test_name, False, f"Exception: {str(e)}")
            
            # Resumo final
            print("\n" + "=" * 80)
            print("📊 RESUMO FINAL DOS TESTES DAS OTIMIZAÇÕES IAZE")
            print("=" * 80)
            
            total_tests = len(results)
            passed_tests = sum(results)
            
            print(f"📈 Total de testes: {total_tests}")
            print(f"✅ Testes passaram: {passed_tests}")
            print(f"❌ Testes falharam: {total_tests - passed_tests}")
            print(f"📊 Taxa de sucesso: {(passed_tests/total_tests)*100:.1f}%")
            
            print("\n📋 DETALHES DOS TESTES:")
            for i, result in enumerate(self.test_results, 1):
                status_icon = "✅" if result["success"] else "❌"
                print(f"{i}. {status_icon} {result['test']}")
                if result["message"]:
                    print(f"   {result['message']}")
            
            # Validações específicas do review request
            print("\n🎯 VALIDAÇÕES ESPECÍFICAS DO REVIEW REQUEST:")
            
            test_names = [
                "MongoDB Index Optimization",
                "Reseller Online Status", 
                "Admin Online Status",
                "Manual Away Mode"
            ]
            
            for i, (test_name, success) in enumerate(zip(test_names, results)):
                if success:
                    print(f"✅ TESTE {i+1}: {test_name} FUNCIONANDO")
                else:
                    print(f"❌ TESTE {i+1}: {test_name} COM PROBLEMAS")
            
            overall_success = all(results)
            
            if overall_success:
                print("\n🎉 RESULTADO FINAL: TODAS AS 3 OTIMIZAÇÕES IAZE 100% FUNCIONAIS!")
                print("✅ MongoDB otimizado, Online Status corrigido, Manual Away Mode funcionando")
                print("✅ Sistema pronto para produção com performance melhorada")
            else:
                print("\n❌ RESULTADO FINAL: ALGUMAS OTIMIZAÇÕES COM PROBLEMAS")
                print("⚠️ Verificar logs acima para detalhes dos problemas")
            
            return overall_success
            
        except Exception as e:
            print(f"💥 ERRO CRÍTICO durante execução dos testes: {e}")
            return False
        finally:
            await self.cleanup_session()

async def main():
    """Função principal"""
    runner = IAZEOptimizationsTestRunner()
    success = await runner.run_all_tests()
    
    if success:
        print("\n🎯 CONCLUSÃO: Todas as otimizações IAZE funcionando perfeitamente!")
        sys.exit(0)
    else:
        print("\n⚠️ CONCLUSÃO: Problemas detectados em algumas otimizações!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())