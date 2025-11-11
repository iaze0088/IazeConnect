#!/usr/bin/env python3
"""
ABA 13 - WHATSAPP (GESTÃO DE INSTÂNCIAS) - TESTE SISTEMÁTICO
Testando funcionalidades de gestão de instâncias WhatsApp conforme review request
"""

import asyncio
import httpx
import json
from datetime import datetime

# Configuração
BACKEND_URL = "https://wppconnect-fix.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "102030@ab"

class WhatsAppInstanceTester:
    def __init__(self):
        self.admin_token = None
        self.test_results = []
        
    def log_result(self, test_name, success, details):
        """Log resultado do teste"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    async def test_admin_login(self):
        """1. Testar login do admin"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{BACKEND_URL}/auth/admin/login",
                    json={
                        "email": ADMIN_EMAIL,
                        "password": ADMIN_PASSWORD
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.admin_token = data.get("token")
                    self.log_result(
                        "Admin Login", 
                        True, 
                        f"Token obtido: {self.admin_token[:20]}..."
                    )
                    return True
                else:
                    self.log_result(
                        "Admin Login", 
                        False, 
                        f"Status {response.status_code}: {response.text}"
                    )
                    return False
                    
        except Exception as e:
            self.log_result("Admin Login", False, f"Erro: {str(e)}")
            return False
    
    async def test_list_instances(self):
        """2. Testar listagem de instâncias WhatsApp"""
        if not self.admin_token:
            self.log_result("Listar Instâncias", False, "Token admin não disponível")
            return False
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                # Testar endpoint solicitado no review request
                response = await client.get(
                    f"{BACKEND_URL}/whatsapp/instances",
                    headers=headers
                )
                
                if response.status_code == 200:
                    instances = response.json()
                    self.log_result(
                        "GET /api/whatsapp/instances", 
                        True, 
                        f"Retornou {len(instances)} instâncias"
                    )
                    return True
                elif response.status_code == 404:
                    # Endpoint não existe, vamos testar o que existe (connections)
                    self.log_result(
                        "GET /api/whatsapp/instances", 
                        False, 
                        "Endpoint não encontrado (404) - testando alternativas..."
                    )
                    
                    # Testar endpoint alternativo (connections)
                    response = await client.get(
                        f"{BACKEND_URL}/whatsapp/connections",
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        connections = response.json()
                        self.log_result(
                            "GET /api/whatsapp/connections (alternativo)", 
                            True, 
                            f"Retornou {len(connections)} conexões WhatsApp"
                        )
                        return True
                    else:
                        self.log_result(
                            "GET /api/whatsapp/connections", 
                            False, 
                            f"Status {response.status_code}: {response.text}"
                        )
                        return False
                else:
                    self.log_result(
                        "GET /api/whatsapp/instances", 
                        False, 
                        f"Status {response.status_code}: {response.text}"
                    )
                    return False
                    
        except Exception as e:
            self.log_result("Listar Instâncias", False, f"Erro: {str(e)}")
            return False
    
    async def test_create_instance(self):
        """3. Testar criação de nova instância"""
        if not self.admin_token:
            self.log_result("Criar Instância", False, "Token admin não disponível")
            return False
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                # Dados da instância conforme review request
                instance_data = {
                    "name": "Instância Teste",
                    "number": "+5511999999999"
                }
                
                # Testar endpoint solicitado
                response = await client.post(
                    f"{BACKEND_URL}/whatsapp/instances",
                    headers=headers,
                    json=instance_data
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    self.log_result(
                        "POST /api/whatsapp/instances", 
                        True, 
                        f"Instância criada: {data}"
                    )
                    return data
                elif response.status_code == 404:
                    # Endpoint não existe, testar alternativo
                    self.log_result(
                        "POST /api/whatsapp/instances", 
                        False, 
                        "Endpoint não encontrado (404) - testando alternativas..."
                    )
                    
                    # Testar endpoint alternativo (connections)
                    connection_data = {
                        "instance_name": "instancia-teste",
                        "phone_number": "+5511999999999",
                        "description": "Instância Teste"
                    }
                    
                    response = await client.post(
                        f"{BACKEND_URL}/whatsapp/connections",
                        headers=headers,
                        json=connection_data
                    )
                    
                    if response.status_code in [200, 201]:
                        data = response.json()
                        self.log_result(
                            "POST /api/whatsapp/connections (alternativo)", 
                            True, 
                            f"Conexão criada: {data}"
                        )
                        return data
                    else:
                        self.log_result(
                            "POST /api/whatsapp/connections", 
                            False, 
                            f"Status {response.status_code}: {response.text}"
                        )
                        return False
                else:
                    self.log_result(
                        "POST /api/whatsapp/instances", 
                        False, 
                        f"Status {response.status_code}: {response.text}"
                    )
                    return False
                    
        except Exception as e:
            self.log_result("Criar Instância", False, f"Erro: {str(e)}")
            return False
    
    async def test_get_qr_code(self, instance_id):
        """4. Testar obtenção de QR Code"""
        if not self.admin_token or not instance_id:
            self.log_result("Obter QR Code", False, "Token admin ou instance_id não disponível")
            return False
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                # Testar endpoint solicitado
                response = await client.get(
                    f"{BACKEND_URL}/whatsapp/qrcode/{instance_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_result(
                        "GET /api/whatsapp/qrcode/{instance_id}", 
                        True, 
                        f"QR Code obtido: {len(str(data))} chars"
                    )
                    return True
                elif response.status_code == 404:
                    # Testar endpoint alternativo
                    self.log_result(
                        "GET /api/whatsapp/qrcode/{instance_id}", 
                        False, 
                        "Endpoint não encontrado (404) - testando alternativas..."
                    )
                    
                    response = await client.get(
                        f"{BACKEND_URL}/whatsapp/connections/{instance_id}/qrcode",
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        self.log_result(
                            "GET /api/whatsapp/connections/{id}/qrcode (alternativo)", 
                            True, 
                            f"QR Code obtido: {data}"
                        )
                        return True
                    else:
                        self.log_result(
                            "GET /api/whatsapp/connections/{id}/qrcode", 
                            False, 
                            f"Status {response.status_code}: {response.text}"
                        )
                        return False
                else:
                    self.log_result(
                        "GET /api/whatsapp/qrcode/{instance_id}", 
                        False, 
                        f"Status {response.status_code}: {response.text}"
                    )
                    return False
                    
        except Exception as e:
            self.log_result("Obter QR Code", False, f"Erro: {str(e)}")
            return False
    
    async def test_get_status(self, instance_id):
        """5. Testar obtenção de status da instância"""
        if not self.admin_token or not instance_id:
            self.log_result("Obter Status", False, "Token admin ou instance_id não disponível")
            return False
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                # Testar endpoint solicitado
                response = await client.get(
                    f"{BACKEND_URL}/whatsapp/status/{instance_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_result(
                        "GET /api/whatsapp/status/{instance_id}", 
                        True, 
                        f"Status obtido: {data}"
                    )
                    return True
                elif response.status_code == 404:
                    # Testar endpoints alternativos
                    self.log_result(
                        "GET /api/whatsapp/status/{instance_id}", 
                        False, 
                        "Endpoint não encontrado (404) - testando alternativas..."
                    )
                    
                    # Testar refresh-status
                    response = await client.post(
                        f"{BACKEND_URL}/whatsapp/connections/{instance_id}/refresh-status",
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        self.log_result(
                            "POST /api/whatsapp/connections/{id}/refresh-status (alternativo)", 
                            True, 
                            f"Status obtido: {data}"
                        )
                        return True
                    else:
                        self.log_result(
                            "POST /api/whatsapp/connections/{id}/refresh-status", 
                            False, 
                            f"Status {response.status_code}: {response.text}"
                        )
                        return False
                else:
                    self.log_result(
                        "GET /api/whatsapp/status/{instance_id}", 
                        False, 
                        f"Status {response.status_code}: {response.text}"
                    )
                    return False
                    
        except Exception as e:
            self.log_result("Obter Status", False, f"Erro: {str(e)}")
            return False
    
    async def test_delete_instance(self, instance_id):
        """6. Testar deleção de instância"""
        if not self.admin_token or not instance_id:
            self.log_result("Deletar Instância", False, "Token admin ou instance_id não disponível")
            return False
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                # Testar endpoint solicitado
                response = await client.delete(
                    f"{BACKEND_URL}/whatsapp/instances/{instance_id}",
                    headers=headers
                )
                
                if response.status_code in [200, 204]:
                    self.log_result(
                        "DELETE /api/whatsapp/instances/{instance_id}", 
                        True, 
                        "Instância deletada com sucesso"
                    )
                    return True
                elif response.status_code == 404:
                    # Testar endpoint alternativo
                    self.log_result(
                        "DELETE /api/whatsapp/instances/{instance_id}", 
                        False, 
                        "Endpoint não encontrado (404) - testando alternativas..."
                    )
                    
                    response = await client.delete(
                        f"{BACKEND_URL}/whatsapp/connections/{instance_id}",
                        headers=headers
                    )
                    
                    if response.status_code in [200, 204]:
                        self.log_result(
                            "DELETE /api/whatsapp/connections/{id} (alternativo)", 
                            True, 
                            "Conexão deletada com sucesso"
                        )
                        return True
                    else:
                        self.log_result(
                            "DELETE /api/whatsapp/connections/{id}", 
                            False, 
                            f"Status {response.status_code}: {response.text}"
                        )
                        return False
                else:
                    self.log_result(
                        "DELETE /api/whatsapp/instances/{instance_id}", 
                        False, 
                        f"Status {response.status_code}: {response.text}"
                    )
                    return False
                    
        except Exception as e:
            self.log_result("Deletar Instância", False, f"Erro: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Executar todos os testes"""
        print("🧪 INICIANDO TESTE SISTEMÁTICO - ABA 13: WHATSAPP (GESTÃO DE INSTÂNCIAS)")
        print("=" * 80)
        
        # 1. Admin Login
        login_success = await self.test_admin_login()
        if not login_success:
            print("\n❌ TESTE ABORTADO: Falha no login do admin")
            return
        
        # 2. Listar Instâncias
        await self.test_list_instances()
        
        # 3. Criar Nova Instância
        instance_data = await self.test_create_instance()
        instance_id = None
        if instance_data and isinstance(instance_data, dict):
            instance_id = instance_data.get("id") or instance_data.get("connection_id")
        
        # 4. Obter QR Code (se instância foi criada)
        if instance_id:
            await self.test_get_qr_code(instance_id)
            
            # 5. Obter Status da Instância
            await self.test_get_status(instance_id)
            
            # 6. Deletar Instância
            await self.test_delete_instance(instance_id)
        else:
            self.log_result("Obter QR Code", False, "Instância não foi criada")
            self.log_result("Obter Status", False, "Instância não foi criada")
            self.log_result("Deletar Instância", False, "Instância não foi criada")
        
        # Resumo final
        print("\n" + "=" * 80)
        print("📊 RESUMO DOS TESTES")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"✅ Testes Passaram: {passed}/{total}")
        print(f"❌ Testes Falharam: {total - passed}/{total}")
        print(f"📈 Taxa de Sucesso: {(passed/total)*100:.1f}%")
        
        print("\n📋 DETALHES DOS TESTES:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   {result['details']}")
        
        # Análise final
        print("\n🎯 ANÁLISE FINAL:")
        if passed == total:
            print("✅ TODOS OS TESTES PASSARAM - ABA 13 (WHATSAPP) 100% FUNCIONAL!")
        elif passed >= total * 0.8:
            print("⚠️ MAIORIA DOS TESTES PASSOU - Algumas funcionalidades precisam de ajustes")
        else:
            print("❌ MUITOS TESTES FALHARAM - Sistema precisa de correções significativas")
        
        return self.test_results

async def main():
    tester = WhatsAppInstanceTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())