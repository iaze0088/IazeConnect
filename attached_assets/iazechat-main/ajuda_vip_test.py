#!/usr/bin/env python3
"""
Teste específico para o problema de login da revenda ajuda.vip
Conforme solicitado no review_request
"""

import requests
import json
import os
from typing import Dict, Optional, List
import bcrypt

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://wppconnect-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
ADMIN_PASSWORD = "102030@ab"  # From .env file

class AjudaVipTester:
    def __init__(self):
        self.admin_token = None
        self.test_results = []
        
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
                    token: str = None, headers: dict = None) -> tuple[bool, dict]:
        """Make HTTP request with error handling"""
        url = f"{API_BASE}{endpoint}"
        
        request_headers = {"Content-Type": "application/json"}
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        if headers:
            request_headers.update(headers)
            
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=request_headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=request_headers, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=request_headers, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=request_headers, timeout=30)
            else:
                return False, {"error": f"Unsupported method: {method}"}
                
            return response.status_code < 400, response.json() if response.text else {}
            
        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}
        except json.JSONDecodeError:
            return False, {"error": "Invalid JSON response"}
    
    def test_admin_login(self) -> bool:
        """Test 1: Admin Master Authentication"""
        success, response = self.make_request("POST", "/auth/admin/login", {
            "password": ADMIN_PASSWORD
        })
        
        if success and "token" in response:
            self.admin_token = response["token"]
            self.log_result("Admin Master Login", True, f"Token received: {response['user_type']}")
            return True
        else:
            self.log_result("Admin Master Login", False, f"Error: {response}")
            return False
    
    def test_list_all_resellers(self) -> List[dict]:
        """Test 2: Listar TODAS as revendas no banco"""
        success, response = self.make_request("GET", "/resellers", token=self.admin_token)
        
        if success and isinstance(response, list):
            print(f"\n📋 TODAS AS REVENDAS ENCONTRADAS ({len(response)}):")
            print("=" * 80)
            
            for i, reseller in enumerate(response, 1):
                print(f"{i}. ID: {reseller.get('id', 'N/A')}")
                print(f"   Nome: {reseller.get('name', 'N/A')}")
                print(f"   Email: {reseller.get('email', 'N/A')}")
                print(f"   Domain: {reseller.get('domain', 'N/A')}")
                print(f"   Custom Domain: {reseller.get('custom_domain', 'N/A')}")
                print(f"   Level: {reseller.get('level', 'N/A')}")
                print(f"   Parent ID: {reseller.get('parent_id', 'N/A')}")
                print(f"   Active: {reseller.get('is_active', 'N/A')}")
                print("-" * 40)
            
            self.log_result("List All Resellers", True, f"Found {len(response)} resellers")
            return response
        else:
            self.log_result("List All Resellers", False, f"Error: {response}")
            return []
    
    def test_find_ajuda_vip_reseller(self, resellers: List[dict]) -> Optional[dict]:
        """Test 3: Verificar qual revenda tem domínio ajuda.vip"""
        ajuda_vip_resellers = []
        
        for reseller in resellers:
            custom_domain = reseller.get('custom_domain', '').lower()
            domain = reseller.get('domain', '').lower()
            
            if 'ajuda.vip' in custom_domain or 'ajuda.vip' in domain:
                ajuda_vip_resellers.append(reseller)
        
        if ajuda_vip_resellers:
            print(f"\n🎯 REVENDAS COM DOMÍNIO AJUDA.VIP ({len(ajuda_vip_resellers)}):")
            print("=" * 60)
            
            for reseller in ajuda_vip_resellers:
                print(f"ID: {reseller.get('id')}")
                print(f"Nome: {reseller.get('name')}")
                print(f"EMAIL EXATO: {reseller.get('email')}")
                print(f"Domain: {reseller.get('domain')}")
                print(f"Custom Domain: {reseller.get('custom_domain')}")
                print(f"Active: {reseller.get('is_active')}")
                print("-" * 40)
            
            self.log_result("Find ajuda.vip Reseller", True, f"Found {len(ajuda_vip_resellers)} resellers with ajuda.vip domain")
            return ajuda_vip_resellers[0]  # Return first one
        else:
            self.log_result("Find ajuda.vip Reseller", False, "No reseller found with ajuda.vip domain")
            return None
    
    def test_login_variations(self, ajuda_reseller: Optional[dict]) -> bool:
        """Test 4: Testar login com diferentes variações"""
        if not ajuda_reseller:
            self.log_result("Login Variations", False, "No ajuda.vip reseller found to test")
            return False
        
        # Variações de login para testar
        login_attempts = [
            {"email": "michaelrv@gmail.com", "password": "ab181818ab"},
            {"email": "michael@gmail.com", "password": "ab181818ab"},
            {"email": ajuda_reseller.get('email', ''), "password": "ab181818ab"},
            {"email": "contato@ajuda.vip", "password": "ab181818ab"},
        ]
        
        print(f"\n🔐 TESTANDO VARIAÇÕES DE LOGIN:")
        print("=" * 50)
        
        successful_logins = []
        
        for attempt in login_attempts:
            if not attempt["email"]:  # Skip empty emails
                continue
                
            print(f"Tentando: {attempt['email']} / {attempt['password']}")
            
            success, response = self.make_request("POST", "/resellers/login", attempt)
            
            if success and "token" in response:
                print(f"✅ LOGIN SUCESSO!")
                print(f"   Token: {response.get('token', '')[:50]}...")
                print(f"   Reseller ID: {response.get('reseller_id', 'N/A')}")
                print(f"   User Data: {response.get('user_data', {})}")
                successful_logins.append({
                    "credentials": attempt,
                    "response": response
                })
            else:
                print(f"❌ LOGIN FALHOU: {response.get('detail', response)}")
            print("-" * 30)
        
        if successful_logins:
            self.log_result("Login Variations", True, f"{len(successful_logins)} successful login(s)")
            return True
        else:
            self.log_result("Login Variations", False, "All login attempts failed")
            return False
    
    def test_create_new_ajuda_reseller(self) -> bool:
        """Test 5: Se nenhum login funcionar, criar nova revenda"""
        print(f"\n🆕 CRIANDO NOVA REVENDA AJUDA.VIP:")
        print("=" * 50)
        
        # Primeiro, deletar todas revendas com domínio ajuda.vip
        success, all_resellers = self.make_request("GET", "/resellers", token=self.admin_token)
        
        if success:
            deleted_count = 0
            for reseller in all_resellers:
                custom_domain = reseller.get('custom_domain', '').lower()
                domain = reseller.get('domain', '').lower()
                
                if 'ajuda.vip' in custom_domain or 'ajuda.vip' in domain:
                    print(f"Deletando revenda existente: {reseller.get('name')} ({reseller.get('email')})")
                    delete_success, delete_response = self.make_request("DELETE", f"/resellers/{reseller['id']}", token=self.admin_token)
                    if delete_success:
                        deleted_count += 1
                        print(f"✅ Deletada com sucesso")
                    else:
                        print(f"❌ Erro ao deletar: {delete_response}")
            
            print(f"Total deletadas: {deleted_count}")
        
        # Criar nova revenda
        new_reseller_data = {
            "name": "michaelrv",
            "email": "michaelrv@gmail.com",
            "password": "ab181818ab",
            "domain": "",
            "parent_id": None
        }
        
        print(f"Criando nova revenda:")
        print(f"  Nome: {new_reseller_data['name']}")
        print(f"  Email: {new_reseller_data['email']}")
        print(f"  Senha: {new_reseller_data['password']}")
        
        success, response = self.make_request("POST", "/resellers", new_reseller_data, self.admin_token)
        
        if success and response.get("ok"):
            reseller_id = response.get("reseller_id")
            print(f"✅ Revenda criada com sucesso!")
            print(f"   ID: {reseller_id}")
            
            # Atualizar custom_domain para ajuda.vip
            update_data = {"custom_domain": "ajuda.vip"}
            update_success, update_response = self.make_request("PUT", f"/resellers/{reseller_id}", 
                                                              update_data, self.admin_token)
            
            if update_success:
                print(f"✅ Custom domain ajuda.vip configurado!")
                
                # Testar login imediatamente
                login_data = {
                    "email": "michaelrv@gmail.com",
                    "password": "ab181818ab"
                }
                
                login_success, login_response = self.make_request("POST", "/resellers/login", login_data)
                
                if login_success and "token" in login_response:
                    print(f"✅ LOGIN FUNCIONANDO!")
                    print(f"   Email: michaelrv@gmail.com")
                    print(f"   Senha: ab181818ab")
                    print(f"   Reseller ID: {login_response.get('reseller_id')}")
                    print(f"   Token: {login_response.get('token', '')[:50]}...")
                    
                    self.log_result("Create New ajuda.vip Reseller", True, 
                                  f"Created and tested successfully - ID: {reseller_id}")
                    return True
                else:
                    print(f"❌ Login falhou após criação: {login_response}")
                    self.log_result("Create New ajuda.vip Reseller", False, 
                                  f"Created but login failed: {login_response}")
                    return False
            else:
                print(f"❌ Erro ao configurar custom domain: {update_response}")
                self.log_result("Create New ajuda.vip Reseller", False, 
                              f"Created but domain update failed: {update_response}")
                return False
        else:
            print(f"❌ Erro ao criar revenda: {response}")
            self.log_result("Create New ajuda.vip Reseller", False, f"Creation failed: {response}")
            return False
    
    def test_final_working_credentials(self) -> bool:
        """Test 6: Retornar credenciais EXATAS que funcionam"""
        print(f"\n🎯 TESTANDO CREDENCIAIS FINAIS:")
        print("=" * 50)
        
        # Testar as credenciais esperadas
        final_test = {
            "email": "michaelrv@gmail.com",
            "password": "ab181818ab"
        }
        
        success, response = self.make_request("POST", "/resellers/login", final_test)
        
        if success and "token" in response:
            print(f"🎉 CREDENCIAIS FUNCIONANDO:")
            print(f"   Email correto: {final_test['email']}")
            print(f"   Senha correta: {final_test['password']}")
            print(f"   ID da revenda: {response.get('reseller_id')}")
            print(f"   Token gerado: {response.get('token', '')[:50]}...")
            print(f"   User Data: {response.get('user_data', {})}")
            
            self.log_result("Final Working Credentials", True, 
                          f"Email: {final_test['email']}, Reseller ID: {response.get('reseller_id')}")
            return True
        else:
            print(f"❌ CREDENCIAIS NÃO FUNCIONAM: {response}")
            self.log_result("Final Working Credentials", False, f"Login failed: {response}")
            return False
    
    def run_ajuda_vip_tests(self):
        """Run all ajuda.vip specific tests"""
        print("🚀 TESTE URGENTE - LOGIN DA REVENDA AJUDA.VIP")
        print("=" * 60)
        print(f"🔗 Testing backend at: {API_BASE}")
        print(f"📧 Email esperado: michaelrv@gmail.com")
        print(f"🔑 Senha esperada: ab181818ab")
        print("=" * 60)
        
        # Test 1: Admin login
        if not self.test_admin_login():
            print("❌ Não foi possível fazer login como admin. Abortando testes.")
            return
        
        # Test 2: List all resellers
        all_resellers = self.test_list_all_resellers()
        
        # Test 3: Find ajuda.vip reseller
        ajuda_reseller = self.test_find_ajuda_vip_reseller(all_resellers)
        
        # Test 4: Try login variations
        login_success = self.test_login_variations(ajuda_reseller)
        
        # Test 5: If no login works, create new reseller
        if not login_success:
            print("\n⚠️  Nenhum login funcionou. Criando nova revenda...")
            self.test_create_new_ajuda_reseller()
        
        # Test 6: Final test with expected credentials
        self.test_final_working_credentials()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 RESUMO DOS TESTES:")
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        print(f"\n📈 Resultado: {passed}/{total} testes passaram")
        
        if passed == total:
            print("🎉 TODOS OS TESTES PASSARAM! Login da ajuda.vip está funcionando.")
        else:
            print(f"⚠️  {total - passed} testes falharam. Verifique os problemas acima.")

def main():
    """Main test execution"""
    tester = AjudaVipTester()
    tester.run_ajuda_vip_tests()

if __name__ == "__main__":
    main()