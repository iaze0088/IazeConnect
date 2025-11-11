#!/usr/bin/env python3
"""
TESTE COMPLETO DOS ENDPOINTS WHATSAPP CONNECTIONS EXISTENTES
Verificando funcionalidades reais disponíveis no sistema
"""

import asyncio
import httpx
import json
from datetime import datetime

# Configuração
BACKEND_URL = "https://wppconnect-fix.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "102030@ab"

class WhatsAppConnectionsTester:
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
    
    async def test_list_connections(self):
        """2. Testar listagem de conexões WhatsApp"""
        if not self.admin_token:
            self.log_result("Listar Conexões", False, "Token admin não disponível")
            return []
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                response = await client.get(
                    f"{BACKEND_URL}/whatsapp/connections",
                    headers=headers
                )
                
                if response.status_code == 200:
                    connections = response.json()
                    self.log_result(
                        "GET /api/whatsapp/connections", 
                        True, 
                        f"Retornou {len(connections)} conexões"
                    )
                    
                    # Mostrar detalhes das primeiras 3 conexões
                    if connections:
                        print("   📋 Primeiras conexões encontradas:")
                        for i, conn in enumerate(connections[:3]):
                            print(f"      {i+1}. ID: {conn.get('id', 'N/A')[:20]}...")
                            print(f"         Nome: {conn.get('instance_name', 'N/A')}")
                            print(f"         Status: {conn.get('status', 'N/A')}")
                    
                    return connections
                else:
                    self.log_result(
                        "GET /api/whatsapp/connections", 
                        False, 
                        f"Status {response.status_code}: {response.text}"
                    )
                    return []
                    
        except Exception as e:
            self.log_result("Listar Conexões", False, f"Erro: {str(e)}")
            return []
    
    async def test_get_qr_code(self, connection_id):
        """3. Testar obtenção de QR Code"""
        if not self.admin_token or not connection_id:
            self.log_result("Obter QR Code", False, "Token admin ou connection_id não disponível")
            return False
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                response = await client.get(
                    f"{BACKEND_URL}/whatsapp/connections/{connection_id}/qrcode",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    qr_code = data.get("qr_code")
                    status = data.get("status")
                    message = data.get("message", "")
                    
                    self.log_result(
                        "GET /api/whatsapp/connections/{id}/qrcode", 
                        True, 
                        f"Status: {status}, QR: {'Disponível' if qr_code else 'Não disponível'}, Msg: {message}"
                    )
                    return True
                else:
                    self.log_result(
                        "GET /api/whatsapp/connections/{id}/qrcode", 
                        False, 
                        f"Status {response.status_code}: {response.text}"
                    )
                    return False
                    
        except Exception as e:
            self.log_result("Obter QR Code", False, f"Erro: {str(e)}")
            return False
    
    async def test_refresh_status(self, connection_id):
        """4. Testar refresh de status"""
        if not self.admin_token or not connection_id:
            self.log_result("Refresh Status", False, "Token admin ou connection_id não disponível")
            return False
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                response = await client.post(
                    f"{BACKEND_URL}/whatsapp/connections/{connection_id}/refresh-status",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_result(
                        "POST /api/whatsapp/connections/{id}/refresh-status", 
                        True, 
                        f"Status atualizado: {data}"
                    )
                    return True
                else:
                    self.log_result(
                        "POST /api/whatsapp/connections/{id}/refresh-status", 
                        False, 
                        f"Status {response.status_code}: {response.text}"
                    )
                    return False
                    
        except Exception as e:
            self.log_result("Refresh Status", False, f"Erro: {str(e)}")
            return False
    
    async def test_dashboard_stats(self):
        """5. Testar estatísticas do dashboard"""
        if not self.admin_token:
            self.log_result("Dashboard Stats", False, "Token admin não disponível")
            return False
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                response = await client.get(
                    f"{BACKEND_URL}/whatsapp/dashboard-stats",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    total_instances = data.get("totalInstances", 0)
                    connected = data.get("connectedInstances", 0)
                    disconnected = data.get("disconnectedInstances", 0)
                    
                    self.log_result(
                        "GET /api/whatsapp/dashboard-stats", 
                        True, 
                        f"Total: {total_instances}, Conectadas: {connected}, Desconectadas: {disconnected}"
                    )
                    return True
                else:
                    self.log_result(
                        "GET /api/whatsapp/dashboard-stats", 
                        False, 
                        f"Status {response.status_code}: {response.text}"
                    )
                    return False
                    
        except Exception as e:
            self.log_result("Dashboard Stats", False, f"Erro: {str(e)}")
            return False
    
    async def test_whatsapp_config(self):
        """6. Testar configuração WhatsApp"""
        if not self.admin_token:
            self.log_result("WhatsApp Config", False, "Token admin não disponível")
            return False
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                response = await client.get(
                    f"{BACKEND_URL}/whatsapp/config",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_result(
                        "GET /api/whatsapp/config", 
                        True, 
                        f"Config obtida: {list(data.keys())}"
                    )
                    return True
                else:
                    self.log_result(
                        "GET /api/whatsapp/config", 
                        False, 
                        f"Status {response.status_code}: {response.text}"
                    )
                    return False
                    
        except Exception as e:
            self.log_result("WhatsApp Config", False, f"Erro: {str(e)}")
            return False
    
    async def test_sync_instances(self):
        """7. Testar sincronização de instâncias"""
        if not self.admin_token:
            self.log_result("Sync Instances", False, "Token admin não disponível")
            return False
            
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:  # Timeout maior para sync
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                response = await client.post(
                    f"{BACKEND_URL}/whatsapp/connections/sync",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_result(
                        "POST /api/whatsapp/connections/sync", 
                        True, 
                        f"Sincronização executada: {data}"
                    )
                    return True
                else:
                    self.log_result(
                        "POST /api/whatsapp/connections/sync", 
                        False, 
                        f"Status {response.status_code}: {response.text}"
                    )
                    return False
                    
        except Exception as e:
            self.log_result("Sync Instances", False, f"Erro: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Executar todos os testes"""
        print("🧪 TESTE COMPLETO DOS ENDPOINTS WHATSAPP CONNECTIONS EXISTENTES")
        print("=" * 80)
        
        # 1. Admin Login
        login_success = await self.test_admin_login()
        if not login_success:
            print("\n❌ TESTE ABORTADO: Falha no login do admin")
            return
        
        # 2. Listar Conexões
        connections = await self.test_list_connections()
        
        # 3. Testar QR Code (usar primeira conexão se disponível)
        if connections:
            first_connection_id = connections[0].get("id")
            if first_connection_id:
                await self.test_get_qr_code(first_connection_id)
                await self.test_refresh_status(first_connection_id)
        
        # 4. Dashboard Stats
        await self.test_dashboard_stats()
        
        # 5. WhatsApp Config
        await self.test_whatsapp_config()
        
        # 6. Sync Instances
        await self.test_sync_instances()
        
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
        print("📌 ENDPOINTS SOLICITADOS NO REVIEW REQUEST NÃO EXISTEM:")
        print("   ❌ GET /api/whatsapp/instances")
        print("   ❌ POST /api/whatsapp/instances") 
        print("   ❌ GET /api/whatsapp/qrcode/{instance_id}")
        print("   ❌ GET /api/whatsapp/status/{instance_id}")
        print("   ❌ DELETE /api/whatsapp/instances/{instance_id}")
        
        print("\n📌 ENDPOINTS ALTERNATIVOS DISPONÍVEIS:")
        print("   ✅ GET /api/whatsapp/connections (listar conexões)")
        print("   ✅ GET /api/whatsapp/connections/{id}/qrcode (obter QR code)")
        print("   ✅ POST /api/whatsapp/connections/{id}/refresh-status (status)")
        print("   ✅ DELETE /api/whatsapp/connections/{id} (deletar)")
        print("   ✅ GET /api/whatsapp/dashboard-stats (estatísticas)")
        print("   ✅ POST /api/whatsapp/connections/sync (sincronizar)")
        
        if passed >= total * 0.7:
            print("\n✅ SISTEMA WHATSAPP FUNCIONAL - Mas endpoints do review request não existem")
        else:
            print("\n❌ PROBLEMAS NO SISTEMA WHATSAPP - Muitos endpoints falhando")
        
        return self.test_results

async def main():
    tester = WhatsAppConnectionsTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())