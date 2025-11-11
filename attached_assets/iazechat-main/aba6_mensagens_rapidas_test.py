#!/usr/bin/env python3
"""
🧪 TESTE SISTEMÁTICO - ABA 6: MENSAGENS RÁPIDAS
Teste completo do sistema de mensagens rápidas (quick_blocks)

FUNCIONALIDADES A TESTAR:
1. Login Admin - POST /api/auth/admin/login
2. GET Config - Verificar campo quick_blocks
3. Adicionar Mensagem Rápida - via PUT /api/config
4. Editar Mensagem Rápida - via PUT /api/config
5. Remover Mensagem Rápida - via PUT /api/config
6. Verificar Persistência - GET /api/config

Admin: admin@admin.com / 102030@ab
Backend: https://wppconnect-fix.preview.emergentagent.com/api
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import uuid

# Configuração
BACKEND_URL = "https://wppconnect-fix.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "102030@ab"

class TestResult:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = []
    
    def add_result(self, test_name: str, success: bool, details: str):
        self.results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        if success:
            self.tests_passed += 1
        else:
            self.tests_failed += 1
    
    def print_summary(self):
        total = self.tests_passed + self.tests_failed
        success_rate = (self.tests_passed / total * 100) if total > 0 else 0
        
        print(f"\n{'='*80}")
        print(f"📊 RESULTADO FINAL: {self.tests_passed}/{total} TESTES PASSARAM ({success_rate:.1f}% SUCCESS RATE)")
        print(f"{'='*80}")
        
        for result in self.results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   {result['details']}")
        
        print(f"\n🎯 RESUMO:")
        print(f"✅ Sucessos: {self.tests_passed}")
        print(f"❌ Falhas: {self.tests_failed}")
        print(f"📈 Taxa de Sucesso: {success_rate:.1f}%")

async def test_admin_login(session: aiohttp.ClientSession, result: TestResult):
    """Teste 1: Login do Admin"""
    print(f"\n🔐 TESTE 1: Admin Login")
    
    try:
        login_data = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        async with session.post(f"{BACKEND_URL}/auth/admin/login", json=login_data) as response:
            if response.status == 200:
                data = await response.json()
                token = data.get("token")
                user_type = data.get("user_type")
                
                if token and user_type == "admin":
                    result.add_result("Admin Login", True, f"Login successful - Token: {token[:20]}...")
                    return token
                else:
                    result.add_result("Admin Login", False, f"Invalid response structure: {data}")
                    return None
            else:
                error_text = await response.text()
                result.add_result("Admin Login", False, f"HTTP {response.status}: {error_text}")
                return None
                
    except Exception as e:
        result.add_result("Admin Login", False, f"Exception: {str(e)}")
        return None

async def test_get_config_quick_blocks(session: aiohttp.ClientSession, token: str, result: TestResult):
    """Teste 2: GET Config - Verificar campo quick_blocks"""
    print(f"\n📋 TESTE 2: GET Config - Verificar quick_blocks")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        async with session.get(f"{BACKEND_URL}/config", headers=headers) as response:
            if response.status == 200:
                config = await response.json()
                quick_blocks = config.get("quick_blocks", [])
                
                result.add_result("GET Config - quick_blocks", True, 
                    f"Config retrieved successfully. Quick blocks count: {len(quick_blocks)}")
                return config
            else:
                error_text = await response.text()
                result.add_result("GET Config - quick_blocks", False, f"HTTP {response.status}: {error_text}")
                return None
                
    except Exception as e:
        result.add_result("GET Config - quick_blocks", False, f"Exception: {str(e)}")
        return None

async def test_add_quick_message(session: aiohttp.ClientSession, token: str, config: dict, result: TestResult):
    """Teste 3: Adicionar Mensagem Rápida"""
    print(f"\n➕ TESTE 3: Adicionar Mensagem Rápida")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Criar nova mensagem rápida
        new_message = {
            "name": "Bom dia! 🌅",
            "text": "Bom dia! Como posso ajudá-lo hoje? Estou aqui para resolver qualquer dúvida ou problema que você possa ter."
        }
        
        # Adicionar à lista existente
        current_quick_blocks = config.get("quick_blocks", [])
        updated_quick_blocks = current_quick_blocks + [new_message]
        
        # Atualizar config
        update_data = {**config, "quick_blocks": updated_quick_blocks}
        
        async with session.put(f"{BACKEND_URL}/config", json=update_data, headers=headers) as response:
            if response.status == 200:
                response_data = await response.json()
                
                result.add_result("Adicionar Mensagem Rápida", True, 
                    f"Mensagem adicionada: '{new_message['name']}'")
                return new_message["name"]  # Use name as identifier
            else:
                error_text = await response.text()
                result.add_result("Adicionar Mensagem Rápida", False, f"HTTP {response.status}: {error_text}")
                return None
                
    except Exception as e:
        result.add_result("Adicionar Mensagem Rápida", False, f"Exception: {str(e)}")
        return None

async def test_edit_quick_message(session: aiohttp.ClientSession, token: str, message_name: str, result: TestResult):
    """Teste 4: Editar Mensagem Rápida"""
    print(f"\n✏️ TESTE 4: Editar Mensagem Rápida")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Primeiro, buscar config atual
        async with session.get(f"{BACKEND_URL}/config", headers=headers) as response:
            if response.status != 200:
                result.add_result("Editar Mensagem Rápida", False, "Falha ao buscar config atual")
                return False
            
            config = await response.json()
            quick_blocks = config.get("quick_blocks", [])
            
            # Encontrar e editar a mensagem
            message_found = False
            for message in quick_blocks:
                if message.get("name") == message_name:
                    message["name"] = "Boa tarde! ☀️"
                    message["text"] = "Boa tarde! Espero que esteja tendo um ótimo dia. Como posso ajudá-lo?"
                    message_found = True
                    break
            
            if not message_found:
                result.add_result("Editar Mensagem Rápida", False, f"Mensagem '{message_name}' não encontrada")
                return False
            
            # Salvar config atualizada
            update_data = {**config, "quick_blocks": quick_blocks}
            
            async with session.put(f"{BACKEND_URL}/config", json=update_data, headers=headers) as response:
                if response.status == 200:
                    result.add_result("Editar Mensagem Rápida", True, 
                        f"Mensagem editada: 'Boa tarde! ☀️'")
                    return True
                else:
                    error_text = await response.text()
                    result.add_result("Editar Mensagem Rápida", False, f"HTTP {response.status}: {error_text}")
                    return False
                    
    except Exception as e:
        result.add_result("Editar Mensagem Rápida", False, f"Exception: {str(e)}")
        return False

async def test_remove_quick_message(session: aiohttp.ClientSession, token: str, message_name: str, result: TestResult):
    """Teste 5: Remover Mensagem Rápida"""
    print(f"\n🗑️ TESTE 5: Remover Mensagem Rápida")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Primeiro, buscar config atual
        async with session.get(f"{BACKEND_URL}/config", headers=headers) as response:
            if response.status != 200:
                result.add_result("Remover Mensagem Rápida", False, "Falha ao buscar config atual")
                return False
            
            config = await response.json()
            quick_blocks = config.get("quick_blocks", [])
            original_count = len(quick_blocks)
            
            # Remover a mensagem
            updated_quick_blocks = [msg for msg in quick_blocks if msg.get("name") != message_name]
            new_count = len(updated_quick_blocks)
            
            if original_count == new_count:
                result.add_result("Remover Mensagem Rápida", False, f"Mensagem '{message_name}' não encontrada para remoção")
                return False
            
            # Salvar config atualizada
            update_data = {**config, "quick_blocks": updated_quick_blocks}
            
            async with session.put(f"{BACKEND_URL}/config", json=update_data, headers=headers) as response:
                if response.status == 200:
                    result.add_result("Remover Mensagem Rápida", True, 
                        f"Mensagem removida '{message_name}'. Count: {original_count} → {new_count}")
                    return True
                else:
                    error_text = await response.text()
                    result.add_result("Remover Mensagem Rápida", False, f"HTTP {response.status}: {error_text}")
                    return False
                    
    except Exception as e:
        result.add_result("Remover Mensagem Rápida", False, f"Exception: {str(e)}")
        return False

async def test_verify_persistence(session: aiohttp.ClientSession, token: str, result: TestResult):
    """Teste 6: Verificar Persistência"""
    print(f"\n💾 TESTE 6: Verificar Persistência")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Adicionar uma mensagem de teste para verificar persistência
        test_message = {
            "name": "Teste Persistência 🔍",
            "text": "Esta é uma mensagem de teste para verificar se os dados são persistidos corretamente no banco de dados."
        }
        
        # Primeiro, buscar config atual
        async with session.get(f"{BACKEND_URL}/config", headers=headers) as response:
            if response.status != 200:
                result.add_result("Verificar Persistência", False, "Falha ao buscar config inicial")
                return False
            
            config = await response.json()
            quick_blocks = config.get("quick_blocks", [])
            
            # Adicionar mensagem de teste
            updated_quick_blocks = quick_blocks + [test_message]
            update_data = {**config, "quick_blocks": updated_quick_blocks}
            
            # Salvar
            async with session.put(f"{BACKEND_URL}/config", json=update_data, headers=headers) as response:
                if response.status != 200:
                    result.add_result("Verificar Persistência", False, "Falha ao salvar mensagem de teste")
                    return False
        
        # Aguardar um pouco
        await asyncio.sleep(1)
        
        # Buscar novamente para verificar persistência
        async with session.get(f"{BACKEND_URL}/config", headers=headers) as response:
            if response.status == 200:
                config_after = await response.json()
                quick_blocks_after = config_after.get("quick_blocks", [])
                
                # Verificar se a mensagem de teste ainda está lá
                test_message_found = any(msg.get("name") == test_message["name"] for msg in quick_blocks_after)
                
                if test_message_found:
                    result.add_result("Verificar Persistência", True, 
                        f"Dados persistidos corretamente. Total de mensagens: {len(quick_blocks_after)}")
                    
                    # Limpar mensagem de teste
                    clean_quick_blocks = [msg for msg in quick_blocks_after if msg.get("name") != test_message["name"]]
                    clean_data = {**config_after, "quick_blocks": clean_quick_blocks}
                    await session.put(f"{BACKEND_URL}/config", json=clean_data, headers=headers)
                    
                    return True
                else:
                    result.add_result("Verificar Persistência", False, "Mensagem de teste não encontrada após reload")
                    return False
            else:
                error_text = await response.text()
                result.add_result("Verificar Persistência", False, f"HTTP {response.status}: {error_text}")
                return False
                
    except Exception as e:
        result.add_result("Verificar Persistência", False, f"Exception: {str(e)}")
        return False

async def main():
    """Executa todos os testes da ABA 6: MENSAGENS RÁPIDAS"""
    print(f"🧪 TESTE SISTEMÁTICO - ABA 6: MENSAGENS RÁPIDAS")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Admin: {ADMIN_EMAIL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"{'='*80}")
    
    result = TestResult()
    
    # Configurar sessão HTTP
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        
        # Teste 1: Login Admin
        token = await test_admin_login(session, result)
        if not token:
            print("❌ Não foi possível fazer login. Abortando testes.")
            result.print_summary()
            return
        
        # Teste 2: GET Config - Verificar quick_blocks
        config = await test_get_config_quick_blocks(session, token, result)
        if not config:
            print("❌ Não foi possível buscar config. Abortando testes.")
            result.print_summary()
            return
        
        # Teste 3: Adicionar Mensagem Rápida
        message_name = await test_add_quick_message(session, token, config, result)
        
        # Teste 4: Editar Mensagem Rápida (se adição foi bem-sucedida)
        if message_name:
            edit_success = await test_edit_quick_message(session, token, message_name, result)
            
            # Teste 5: Remover Mensagem Rápida (usar nome editado se edição foi bem-sucedida)
            remove_name = "Boa tarde! ☀️" if edit_success else message_name
            await test_remove_quick_message(session, token, remove_name, result)
        else:
            result.add_result("Editar Mensagem Rápida", False, "Pulado - falha na adição")
            result.add_result("Remover Mensagem Rápida", False, "Pulado - falha na adição")
        
        # Teste 6: Verificar Persistência
        await test_verify_persistence(session, token, result)
    
    # Imprimir resumo final
    result.print_summary()
    
    # Determinar se todos os testes passaram
    if result.tests_failed == 0:
        print(f"\n🎉 TODOS OS TESTES PASSARAM - ABA 6 (MENSAGENS RÁPIDAS) 100% FUNCIONAL!")
        print(f"✅ Pode avançar para ABA 7 (DADOS PERMITIDOS) conforme plano sistemático do usuário")
    else:
        print(f"\n❌ {result.tests_failed} TESTE(S) FALHARAM - ABA 6 (MENSAGENS RÁPIDAS) PRECISA DE CORREÇÕES")
        print(f"🔧 Verifique os erros acima antes de avançar para próxima ABA")

if __name__ == "__main__":
    asyncio.run(main())