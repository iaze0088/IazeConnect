#!/usr/bin/env python3
"""
🧪 TESTE COMPLETO E SISTEMÁTICO - TODAS AS 16 ABAS DO ADMIN DASHBOARD (CORRIGIDO)

OBJETIVO: Testar TODAS as abas do Admin Dashboard com endpoints corretos
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

class AdminDashboardTesterCorrected:
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
        
    async def test_get_endpoint(self, endpoint, description, base_url=None):
        """Testa endpoint GET"""
        try:
            url = f"{base_url or BACKEND_URL}{endpoint}"
            async with self.session.get(url, headers=self.get_headers()) as response:
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
            
    async def test_post_endpoint(self, endpoint, data, description, base_url=None):
        """Testa endpoint POST"""
        try:
            url = f"{base_url or BACKEND_URL}{endpoint}"
            async with self.session.post(url, json=data, headers=self.get_headers()) as response:
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

    async def test_aba_16_backup_corrected(self):
        """ABA 16: BACKUP (ENDPOINTS CORRETOS)"""
        print("\n" + "="*80)
        print("🧪 ABA 16: BACKUP (ENDPOINTS CORRETOS)")
        print("="*80)
        
        results = {
            "get_backups": False,
            "post_create_backup": False,
            "get_backup_config": False,
            "post_backup_config": False
        }
        
        # Base URL sem /api para backup routes
        backup_base_url = "https://wppconnect-fix.preview.emergentagent.com"
        
        # 1. GET /admin/backup/list
        backups = await self.test_get_endpoint("/admin/backup/list", "Listar backups existentes", backup_base_url)
        if backups is not None:
            results["get_backups"] = True
            
        # 2. GET /admin/backup/config
        backup_config = await self.test_get_endpoint("/admin/backup/config", "Obter configuração de backup", backup_base_url)
        if backup_config is not None:
            results["get_backup_config"] = True
            
        # 3. POST /admin/backup/config
        config_data = {
            "auto_backup_enabled": True
        }
        
        updated_config = await self.test_post_endpoint("/admin/backup/config", config_data, "Atualizar configuração de backup", backup_base_url)
        if updated_config:
            results["post_backup_config"] = True
            
        # 4. POST /admin/backup/create
        created_backup = await self.test_post_endpoint("/admin/backup/create", {}, "Criar novo backup", backup_base_url)
        if created_backup:
            results["post_create_backup"] = True
            print(f"    📋 Backup criado: {created_backup.get('backup_id', 'N/A')}")
            
        self.test_results["aba_16_backup"] = results
        success_rate = sum(results.values()) / len(results) * 100
        status = "✅ FUNCIONAL" if success_rate >= 80 else "⚠️ PARCIAL" if success_rate >= 50 else "❌ COM ERROS"
        print(f"\n📊 ABA 16 - Status: {status} ({success_rate:.1f}% dos testes passaram)")

    async def test_aba_15_wa_site_corrected(self):
        """ABA 15: WA SITE (ENDPOINTS CORRETOS)"""
        print("\n" + "="*80)
        print("🧪 ABA 15: WA SITE (ENDPOINTS CORRETOS)")
        print("="*80)
        
        results = {
            "get_vendas_bot_config": False,
            "post_vendas_bot_config": False,
            "get_vendas_buttons": False,
            "post_vendas_button": False
        }
        
        # 1. GET /api/admin/vendas-bot/config
        bot_config = await self.test_get_endpoint("/admin/vendas-bot/config", "Obter configuração do bot WA Site")
        if bot_config is not None:
            results["get_vendas_bot_config"] = True
            
        # 2. POST /api/admin/vendas-bot/config (com campos corretos)
        bot_config_data = {
            "name": "Bot Vendas Teste",
            "instructions": "Você é um assistente de vendas especializado em IPTV. Seja sempre educado e prestativo.",
            "initial_message": "Olá! Como posso ajudá-lo hoje?",
            "steps": [
                {
                    "step": 1,
                    "message": "Qual tipo de dispositivo você possui?",
                    "options": ["Smart TV", "Android", "iOS"]
                }
            ],
            "is_active": True
        }
        
        created_bot_config = await self.test_post_endpoint("/admin/vendas-bot/config", bot_config_data, "Criar configuração do bot")
        if created_bot_config:
            results["post_vendas_bot_config"] = True
            
        # 3. Testar endpoints de botões (podem estar em rotas diferentes)
        # Base URL sem /api para vendas buttons
        buttons_base_url = "https://wppconnect-fix.preview.emergentagent.com"
        
        buttons = await self.test_get_endpoint("/vendas-buttons/buttons", "Listar botões interativos", buttons_base_url)
        if buttons is not None:
            results["get_vendas_buttons"] = True
        else:
            # Tentar com /api
            buttons = await self.test_get_endpoint("/vendas-buttons/buttons", "Listar botões interativos (com /api)")
            if buttons is not None:
                results["get_vendas_buttons"] = True
            
        # 4. POST botão
        button_data = {
            "title": "Teste Grátis",
            "description": "Experimente nosso serviço por 24 horas grátis",
            "action": "redirect",
            "value": "https://example.com/teste-gratis",
            "is_active": True
        }
        
        created_button = await self.test_post_endpoint("/vendas-buttons/buttons", button_data, "Criar botão interativo", buttons_base_url)
        if created_button:
            results["post_vendas_button"] = True
        else:
            # Tentar com /api
            created_button = await self.test_post_endpoint("/vendas-buttons/buttons", button_data, "Criar botão (com /api)")
            if created_button:
                results["post_vendas_button"] = True
                
        self.test_results["aba_15_wa_site"] = results
        success_rate = sum(results.values()) / len(results) * 100
        status = "✅ FUNCIONAL" if success_rate >= 80 else "⚠️ PARCIAL" if success_rate >= 50 else "❌ COM ERROS"
        print(f"\n📊 ABA 15 - Status: {status} ({success_rate:.1f}% dos testes passaram)")

    async def test_aba_4_atendentes_corrected(self):
        """ABA 4: ATENDENTES (CAMPOS CORRETOS)"""
        print("\n" + "="*80)
        print("🧪 ABA 4: ATENDENTES (CAMPOS CORRETOS)")
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
            
        # 2. POST /api/agents (com campo 'login' em vez de 'username')
        agent_data = {
            "name": "Atendente Teste Sistemático",
            "login": f"teste-sistematico-{int(time.time())}",  # Campo correto
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
                "login": agent_data["login"],  # Manter mesmo login
                "department_ids": []
            }
            updated_agent = await self.test_put_endpoint(f"/agents/{agent_id}", update_data, "Atualizar atendente")
            if updated_agent:
                results["put_agent"] = True
                
        # 4. Testar login do atendente
        try:
            async with self.session.post(f"{BACKEND_URL}/auth/agent/login", json={
                "login": agent_data["login"],
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

    async def test_aba_3_revendas_corrected(self):
        """ABA 3: REVENDAS (CAMPOS CORRETOS)"""
        print("\n" + "="*80)
        print("🧪 ABA 3: REVENDAS (CAMPOS CORRETOS)")
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
            
        # 2. POST /api/resellers (verificar campos obrigatórios)
        reseller_data = {
            "name": "Revenda Teste Sistemático",
            "email": f"teste-sistematico-{int(time.time())}@example.com",
            "password": "teste123"
            # Removido custom_domain que pode não ser obrigatório
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
                "email": reseller_data["email"]  # Manter mesmo email
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

    async def run_corrected_tests(self):
        """Executa testes corrigidos das abas com problemas"""
        print("🚀 INICIANDO TESTES CORRIGIDOS - ABAS COM PROBLEMAS IDENTIFICADOS")
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
                
            # Executar testes corrigidos das abas com problemas
            await self.test_aba_3_revendas_corrected()
            await self.test_aba_4_atendentes_corrected()
            await self.test_aba_15_wa_site_corrected()
            await self.test_aba_16_backup_corrected()
            
        finally:
            await self.cleanup()
            
        # Relatório final
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "="*100)
        print("📊 RELATÓRIO FINAL - TESTES CORRIGIDOS")
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
        overall_status = "✅ CORRIGIDO" if overall_success >= 80 else "⚠️ PARCIALMENTE CORRIGIDO" if overall_success >= 50 else "❌ AINDA COM PROBLEMAS"
        
        print("="*100)
        print(f"🎯 RESULTADO GERAL: {overall_status}")
        print(f"📈 Taxa de Sucesso: {overall_success:.1f}% ({passed_tests}/{total_tests} testes)")
        print(f"⏱️ Tempo Total: {duration:.1f} segundos")
        print("="*100)

async def main():
    """Função principal"""
    tester = AdminDashboardTesterCorrected()
    await tester.run_corrected_tests()

if __name__ == "__main__":
    asyncio.run(main())