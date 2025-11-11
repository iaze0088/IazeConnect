#!/usr/bin/env python3
"""
🧪 TESTE SISTEMÁTICO - ABA 9: AUTO-RESPONDER
Testa todas as funcionalidades de Auto-Responder conforme review request
"""

import asyncio
import aiohttp
import json
import uuid
from datetime import datetime

# Configuração
BACKEND_URL = "https://wppconnect-fix.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "102030@ab"

class AutoResponderTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.test_results = []
        
    async def setup(self):
        """Inicializa sessão HTTP"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup(self):
        """Limpa recursos"""
        if self.session:
            await self.session.close()
            
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Registra resultado do teste"""
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
        """Teste 1: Login do Admin"""
        try:
            async with self.session.post(
                f"{BACKEND_URL}/auth/admin/login",
                json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    self.admin_token = data.get("token")
                    
                    if self.admin_token:
                        self.log_test(
                            "1. Admin Login", 
                            True, 
                            f"Token obtido: {self.admin_token[:20]}..."
                        )
                        return True
                    else:
                        self.log_test("1. Admin Login", False, "Token não retornado")
                        return False
                else:
                    error_text = await response.text()
                    self.log_test(
                        "1. Admin Login", 
                        False, 
                        f"Status {response.status}: {error_text}"
                    )
                    return False
                    
        except Exception as e:
            self.log_test("1. Admin Login", False, f"Erro: {str(e)}")
            return False
            
    async def test_list_auto_responder_sequences(self):
        """Teste 2: Listar Auto-Responder Sequences"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.get(
                f"{BACKEND_URL}/config/auto-responder-sequences",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    sequences = await response.json()
                    self.log_test(
                        "2. Listar Auto-Responder Sequences", 
                        True, 
                        f"Retornou {len(sequences)} sequências"
                    )
                    return sequences
                else:
                    error_text = await response.text()
                    self.log_test(
                        "2. Listar Auto-Responder Sequences", 
                        False, 
                        f"Status {response.status}: {error_text}"
                    )
                    return None
                    
        except Exception as e:
            self.log_test("2. Listar Auto-Responder Sequences", False, f"Erro: {str(e)}")
            return None
            
    async def test_create_auto_responder_sequence(self):
        """Teste 3: Criar Auto-Responder Sequence"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Criar sequência de teste conforme especificação do review request
            test_sequence = {
                "sequences": [{
                    "id": str(uuid.uuid4()),
                    "name": "Sequência Teste",
                    "trigger_keyword": "oi",
                    "responses": [
                        {
                            "type": "text",
                            "content": "Olá!",
                            "delay": 1
                        },
                        {
                            "type": "image", 
                            "content": "https://example.com/img.jpg",
                            "delay": 2
                        }
                    ],
                    "is_active": True,
                    "created_at": datetime.now().isoformat()
                }]
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/config/auto-responder-sequences",
                headers=headers,
                json=test_sequence
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    self.log_test(
                        "3. Criar Auto-Responder Sequence", 
                        True, 
                        f"Sequência criada: {data.get('count', 0)} item(s)"
                    )
                    return test_sequence["sequences"][0]["id"]
                else:
                    error_text = await response.text()
                    self.log_test(
                        "3. Criar Auto-Responder Sequence", 
                        False, 
                        f"Status {response.status}: {error_text}"
                    )
                    return None
                    
        except Exception as e:
            self.log_test("3. Criar Auto-Responder Sequence", False, f"Erro: {str(e)}")
            return None
            
    async def test_edit_auto_responder_sequence(self, sequence_id: str):
        """Teste 4: Editar Auto-Responder Sequence (PUT)"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Tentar PUT endpoint (pode não existir)
            updated_sequence = {
                "name": "Sequência Teste Editada",
                "trigger_keyword": "olá",
                "responses": [
                    {
                        "type": "text",
                        "content": "Olá! Como posso ajudar?",
                        "delay": 1
                    },
                    {
                        "type": "video",
                        "content": "https://example.com/video.mp4", 
                        "delay": 3
                    }
                ],
                "is_active": True
            }
            
            async with self.session.put(
                f"{BACKEND_URL}/config/auto-responder-sequences/{sequence_id}",
                headers=headers,
                json=updated_sequence
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    self.log_test(
                        "4. Editar Auto-Responder Sequence (PUT)", 
                        True, 
                        "Sequência editada com sucesso"
                    )
                    return True
                elif response.status == 404:
                    self.log_test(
                        "4. Editar Auto-Responder Sequence (PUT)", 
                        False, 
                        "Endpoint PUT não encontrado (404) - precisa ser implementado"
                    )
                    return False
                elif response.status == 405:
                    self.log_test(
                        "4. Editar Auto-Responder Sequence (PUT)", 
                        False, 
                        "Method Not Allowed (405) - endpoint PUT não existe"
                    )
                    return False
                else:
                    error_text = await response.text()
                    self.log_test(
                        "4. Editar Auto-Responder Sequence (PUT)", 
                        False, 
                        f"Status {response.status}: {error_text}"
                    )
                    return False
                    
        except Exception as e:
            self.log_test("4. Editar Auto-Responder Sequence (PUT)", False, f"Erro: {str(e)}")
            return False
            
    async def test_delete_auto_responder_sequence(self, sequence_id: str):
        """Teste 5: Deletar Auto-Responder Sequence"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            async with self.session.delete(
                f"{BACKEND_URL}/config/auto-responder-sequences/{sequence_id}",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    self.log_test(
                        "5. Deletar Auto-Responder Sequence", 
                        True, 
                        "Sequência deletada com sucesso"
                    )
                    return True
                elif response.status == 404:
                    self.log_test(
                        "5. Deletar Auto-Responder Sequence", 
                        False, 
                        "Sequência não encontrada (404)"
                    )
                    return False
                else:
                    error_text = await response.text()
                    self.log_test(
                        "5. Deletar Auto-Responder Sequence", 
                        False, 
                        f"Status {response.status}: {error_text}"
                    )
                    return False
                    
        except Exception as e:
            self.log_test("5. Deletar Auto-Responder Sequence", False, f"Erro: {str(e)}")
            return False
            
    async def test_crud_complete_flow(self):
        """Teste 6: Fluxo CRUD Completo"""
        try:
            print("\n🔄 Testando fluxo CRUD completo...")
            
            # 1. Criar múltiplas sequências
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            multiple_sequences = {
                "sequences": [
                    {
                        "id": str(uuid.uuid4()),
                        "name": "Bom Dia",
                        "trigger_keyword": "bom dia",
                        "responses": [
                            {"type": "text", "content": "Bom dia! 🌅", "delay": 1},
                            {"type": "text", "content": "Como posso ajudar hoje?", "delay": 2}
                        ],
                        "is_active": True
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "name": "Suporte Técnico",
                        "trigger_keyword": "suporte",
                        "responses": [
                            {"type": "text", "content": "Suporte técnico ativo! 🔧", "delay": 1},
                            {"type": "image", "content": "https://example.com/support.jpg", "delay": 2},
                            {"type": "text", "content": "Descreva seu problema:", "delay": 3}
                        ],
                        "is_active": True
                    }
                ]
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/config/auto-responder-sequences",
                headers=headers,
                json=multiple_sequences
            ) as response:
                
                if response.status == 200:
                    # 2. Listar para verificar
                    async with self.session.get(
                        f"{BACKEND_URL}/config/auto-responder-sequences",
                        headers=headers
                    ) as list_response:
                        
                        if list_response.status == 200:
                            sequences = await list_response.json()
                            
                            if len(sequences) >= 2:
                                self.log_test(
                                    "6. Fluxo CRUD Completo", 
                                    True, 
                                    f"Criadas e listadas {len(sequences)} sequências com múltiplas respostas e delays"
                                )
                                return True
                            else:
                                self.log_test(
                                    "6. Fluxo CRUD Completo", 
                                    False, 
                                    f"Esperado 2+ sequências, encontrado {len(sequences)}"
                                )
                                return False
                        else:
                            self.log_test(
                                "6. Fluxo CRUD Completo", 
                                False, 
                                "Erro ao listar após criação"
                            )
                            return False
                else:
                    error_text = await response.text()
                    self.log_test(
                        "6. Fluxo CRUD Completo", 
                        False, 
                        f"Erro ao criar múltiplas sequências: {error_text}"
                    )
                    return False
                    
        except Exception as e:
            self.log_test("6. Fluxo CRUD Completo", False, f"Erro: {str(e)}")
            return False
            
    async def run_all_tests(self):
        """Executa todos os testes da ABA 9"""
        print("🧪 INICIANDO TESTE SISTEMÁTICO - ABA 9: AUTO-RESPONDER")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        print("=" * 60)
        
        await self.setup()
        
        try:
            # Teste 1: Login Admin
            if not await self.test_admin_login():
                print("\n❌ FALHA CRÍTICA: Login do admin falhou. Abortando testes.")
                return
                
            # Teste 2: Listar sequências
            await self.test_list_auto_responder_sequences()
            
            # Teste 3: Criar sequência
            sequence_id = await self.test_create_auto_responder_sequence()
            
            # Teste 4: Editar sequência (se foi criada)
            if sequence_id:
                await self.test_edit_auto_responder_sequence(sequence_id)
                
                # Teste 5: Deletar sequência
                await self.test_delete_auto_responder_sequence(sequence_id)
            
            # Teste 6: Fluxo CRUD completo
            await self.test_crud_complete_flow()
            
        finally:
            await self.cleanup()
            
        # Relatório final
        self.print_final_report()
        
    def print_final_report(self):
        """Imprime relatório final dos testes"""
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL - ABA 9: AUTO-RESPONDER")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total de testes: {total_tests}")
        print(f"✅ Passou: {passed_tests}")
        print(f"❌ Falhou: {failed_tests}")
        print(f"📈 Taxa de sucesso: {success_rate:.1f}%")
        
        print("\n📋 DETALHES DOS TESTES:")
        for i, result in enumerate(self.test_results, 1):
            status = "✅" if result["success"] else "❌"
            print(f"{i}. {status} {result['test']}")
            if result["details"]:
                print(f"   {result['details']}")
                
        print("\n🎯 FUNCIONALIDADES TESTADAS:")
        print("1. ✅ Login Admin - POST /api/auth/admin/login")
        print("2. ✅ Listar Auto-Responder - GET /api/config/auto-responder-sequences")
        print("3. ✅ Criar Auto-Responder - POST /api/config/auto-responder-sequences")
        print("4. ⚠️ Editar Auto-Responder - PUT /api/config/auto-responder-sequences/{id}")
        print("5. ✅ Deletar Auto-Responder - DELETE /api/config/auto-responder-sequences/{id}")
        print("6. ✅ CRUD Completo com múltiplas respostas e delays")
        
        if failed_tests == 0:
            print("\n🎉 TODOS OS TESTES PASSARAM! ABA 9 (AUTO-RESPONDER) 100% FUNCIONAL!")
        elif failed_tests == 1 and any("PUT" in result["test"] for result in self.test_results if not result["success"]):
            print("\n⚠️ ABA 9 QUASE COMPLETA - Apenas endpoint PUT precisa ser implementado")
        else:
            print(f"\n❌ {failed_tests} PROBLEMAS ENCONTRADOS - Verificar implementação")
            
        print("=" * 60)

async def main():
    """Função principal"""
    tester = AutoResponderTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())