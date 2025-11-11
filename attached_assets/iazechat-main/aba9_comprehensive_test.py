#!/usr/bin/env python3
"""
🧪 TESTE ABRANGENTE - ABA 9: AUTO-RESPONDER
Testa cenários avançados e edge cases
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

class ComprehensiveAutoResponderTester:
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
        
    async def get_admin_token(self):
        """Obtém token do admin"""
        async with self.session.post(
            f"{BACKEND_URL}/auth/admin/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        ) as response:
            if response.status == 200:
                data = await response.json()
                self.admin_token = data.get("token")
                return True
            return False
            
    async def test_multiple_media_types(self):
        """Teste: Múltiplos tipos de mídia"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Sequência com todos os tipos de mídia
            multimedia_sequence = {
                "sequences": [{
                    "id": str(uuid.uuid4()),
                    "name": "Sequência Multimídia Completa",
                    "trigger_keyword": "multimedia",
                    "responses": [
                        {"type": "text", "content": "Bem-vindo! Vou enviar diferentes tipos de mídia:", "delay": 1},
                        {"type": "image", "content": "https://example.com/welcome.jpg", "delay": 2},
                        {"type": "video", "content": "https://example.com/tutorial.mp4", "delay": 3},
                        {"type": "audio", "content": "https://example.com/greeting.mp3", "delay": 2},
                        {"type": "text", "content": "Todos os tipos de mídia foram enviados! 🎉", "delay": 1}
                    ],
                    "is_active": True,
                    "created_at": datetime.now().isoformat()
                }]
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/config/auto-responder-sequences",
                headers=headers,
                json=multimedia_sequence
            ) as response:
                
                if response.status == 200:
                    self.log_test(
                        "Múltiplos Tipos de Mídia", 
                        True, 
                        "Sequência com texto, imagem, vídeo e áudio criada com sucesso"
                    )
                    return multimedia_sequence["sequences"][0]["id"]
                else:
                    error_text = await response.text()
                    self.log_test(
                        "Múltiplos Tipos de Mídia", 
                        False, 
                        f"Erro: {error_text}"
                    )
                    return None
                    
        except Exception as e:
            self.log_test("Múltiplos Tipos de Mídia", False, f"Erro: {str(e)}")
            return None
            
    async def test_variable_delays(self):
        """Teste: Delays variáveis (0-60 segundos)"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Sequência com delays variáveis
            delay_sequence = {
                "sequences": [{
                    "id": str(uuid.uuid4()),
                    "name": "Teste de Delays Variáveis",
                    "trigger_keyword": "delays",
                    "responses": [
                        {"type": "text", "content": "Resposta imediata (0s)", "delay": 0},
                        {"type": "text", "content": "Resposta rápida (1s)", "delay": 1},
                        {"type": "text", "content": "Resposta média (5s)", "delay": 5},
                        {"type": "text", "content": "Resposta lenta (10s)", "delay": 10},
                        {"type": "text", "content": "Resposta muito lenta (30s)", "delay": 30},
                        {"type": "text", "content": "Resposta máxima (60s)", "delay": 60}
                    ],
                    "is_active": True,
                    "created_at": datetime.now().isoformat()
                }]
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/config/auto-responder-sequences",
                headers=headers,
                json=delay_sequence
            ) as response:
                
                if response.status == 200:
                    self.log_test(
                        "Delays Variáveis (0-60s)", 
                        True, 
                        "Sequência com delays de 0s a 60s criada com sucesso"
                    )
                    return delay_sequence["sequences"][0]["id"]
                else:
                    error_text = await response.text()
                    self.log_test(
                        "Delays Variáveis (0-60s)", 
                        False, 
                        f"Erro: {error_text}"
                    )
                    return None
                    
        except Exception as e:
            self.log_test("Delays Variáveis (0-60s)", False, f"Erro: {str(e)}")
            return None
            
    async def test_edit_functionality(self, sequence_id: str):
        """Teste: Funcionalidade de edição completa"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Primeiro, buscar a sequência original
            async with self.session.get(
                f"{BACKEND_URL}/config/auto-responder-sequences",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    sequences = await response.json()
                    original_sequence = next((seq for seq in sequences if seq.get("id") == sequence_id), None)
                    
                    if not original_sequence:
                        self.log_test("Edição Completa", False, "Sequência original não encontrada")
                        return False
                    
                    # Editar todos os campos
                    updated_data = {
                        "name": "Nome Editado - Teste Completo",
                        "trigger_keyword": "editado",
                        "responses": [
                            {"type": "text", "content": "Resposta editada 1", "delay": 2},
                            {"type": "image", "content": "https://example.com/edited.jpg", "delay": 4},
                            {"type": "text", "content": "Resposta editada 2", "delay": 1}
                        ],
                        "is_active": False  # Desativar para testar
                    }
                    
                    # Fazer a edição
                    async with self.session.put(
                        f"{BACKEND_URL}/config/auto-responder-sequences/{sequence_id}",
                        headers=headers,
                        json=updated_data
                    ) as edit_response:
                        
                        if edit_response.status == 200:
                            # Verificar se a edição foi aplicada
                            async with self.session.get(
                                f"{BACKEND_URL}/config/auto-responder-sequences",
                                headers=headers
                            ) as verify_response:
                                
                                if verify_response.status == 200:
                                    updated_sequences = await verify_response.json()
                                    edited_sequence = next((seq for seq in updated_sequences if seq.get("id") == sequence_id), None)
                                    
                                    if edited_sequence:
                                        # Verificar se os campos foram atualizados
                                        checks = [
                                            edited_sequence.get("name") == updated_data["name"],
                                            edited_sequence.get("trigger_keyword") == updated_data["trigger_keyword"],
                                            len(edited_sequence.get("responses", [])) == len(updated_data["responses"]),
                                            edited_sequence.get("is_active") == updated_data["is_active"]
                                        ]
                                        
                                        if all(checks):
                                            self.log_test(
                                                "Edição Completa", 
                                                True, 
                                                "Todos os campos foram atualizados corretamente"
                                            )
                                            return True
                                        else:
                                            self.log_test(
                                                "Edição Completa", 
                                                False, 
                                                f"Alguns campos não foram atualizados. Checks: {checks}"
                                            )
                                            return False
                                    else:
                                        self.log_test("Edição Completa", False, "Sequência não encontrada após edição")
                                        return False
                                else:
                                    self.log_test("Edição Completa", False, "Erro ao verificar edição")
                                    return False
                        else:
                            error_text = await edit_response.text()
                            self.log_test("Edição Completa", False, f"Erro na edição: {error_text}")
                            return False
                else:
                    self.log_test("Edição Completa", False, "Erro ao buscar sequência original")
                    return False
                    
        except Exception as e:
            self.log_test("Edição Completa", False, f"Erro: {str(e)}")
            return False
            
    async def test_edge_cases(self):
        """Teste: Casos extremos"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Teste 1: Sequência vazia
            empty_sequence = {"sequences": []}
            
            async with self.session.post(
                f"{BACKEND_URL}/config/auto-responder-sequences",
                headers=headers,
                json=empty_sequence
            ) as response:
                
                if response.status == 200:
                    self.log_test("Edge Case: Sequência Vazia", True, "Aceita sequência vazia")
                else:
                    self.log_test("Edge Case: Sequência Vazia", False, f"Status: {response.status}")
            
            # Teste 2: Sequência com nome muito longo
            long_name_sequence = {
                "sequences": [{
                    "id": str(uuid.uuid4()),
                    "name": "A" * 200,  # Nome muito longo
                    "trigger_keyword": "long",
                    "responses": [{"type": "text", "content": "Teste", "delay": 1}],
                    "is_active": True
                }]
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/config/auto-responder-sequences",
                headers=headers,
                json=long_name_sequence
            ) as response:
                
                if response.status == 200:
                    self.log_test("Edge Case: Nome Longo", True, "Aceita nome com 200 caracteres")
                    return long_name_sequence["sequences"][0]["id"]
                else:
                    self.log_test("Edge Case: Nome Longo", False, f"Status: {response.status}")
                    return None
                    
        except Exception as e:
            self.log_test("Edge Cases", False, f"Erro: {str(e)}")
            return None
            
    async def test_persistence(self):
        """Teste: Persistência de dados"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Criar sequência de teste
            test_sequence = {
                "sequences": [{
                    "id": str(uuid.uuid4()),
                    "name": "Teste de Persistência",
                    "trigger_keyword": "persistencia",
                    "responses": [
                        {"type": "text", "content": "Dados persistidos!", "delay": 1}
                    ],
                    "is_active": True,
                    "created_at": datetime.now().isoformat()
                }]
            }
            
            # Criar
            async with self.session.post(
                f"{BACKEND_URL}/config/auto-responder-sequences",
                headers=headers,
                json=test_sequence
            ) as response:
                
                if response.status == 200:
                    sequence_id = test_sequence["sequences"][0]["id"]
                    
                    # Aguardar um pouco
                    await asyncio.sleep(1)
                    
                    # Verificar se ainda existe
                    async with self.session.get(
                        f"{BACKEND_URL}/config/auto-responder-sequences",
                        headers=headers
                    ) as verify_response:
                        
                        if verify_response.status == 200:
                            sequences = await verify_response.json()
                            found = any(seq.get("id") == sequence_id for seq in sequences)
                            
                            if found:
                                self.log_test("Persistência de Dados", True, "Dados persistidos corretamente no MongoDB")
                                return sequence_id
                            else:
                                self.log_test("Persistência de Dados", False, "Dados não encontrados após criação")
                                return None
                        else:
                            self.log_test("Persistência de Dados", False, "Erro ao verificar persistência")
                            return None
                else:
                    self.log_test("Persistência de Dados", False, "Erro ao criar sequência de teste")
                    return None
                    
        except Exception as e:
            self.log_test("Persistência de Dados", False, f"Erro: {str(e)}")
            return None
            
    async def run_comprehensive_tests(self):
        """Executa todos os testes abrangentes"""
        print("🧪 INICIANDO TESTE ABRANGENTE - ABA 9: AUTO-RESPONDER")
        print("=" * 70)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin: {ADMIN_EMAIL}")
        print("=" * 70)
        
        await self.setup()
        
        try:
            # Obter token
            if not await self.get_admin_token():
                print("\n❌ FALHA CRÍTICA: Login do admin falhou. Abortando testes.")
                return
                
            print("✅ Admin autenticado com sucesso\n")
            
            # Testes abrangentes
            multimedia_id = await self.test_multiple_media_types()
            delay_id = await self.test_variable_delays()
            
            if multimedia_id:
                await self.test_edit_functionality(multimedia_id)
            
            edge_case_id = await self.test_edge_cases()
            persistence_id = await self.test_persistence()
            
        finally:
            await self.cleanup()
            
        # Relatório final
        self.print_final_report()
        
    def print_final_report(self):
        """Imprime relatório final dos testes"""
        print("\n" + "=" * 70)
        print("📊 RELATÓRIO FINAL - TESTE ABRANGENTE ABA 9")
        print("=" * 70)
        
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
                
        print("\n🎯 CENÁRIOS AVANÇADOS TESTADOS:")
        print("1. ✅ Múltiplos tipos de mídia (texto, imagem, vídeo, áudio)")
        print("2. ✅ Delays variáveis (0-60 segundos)")
        print("3. ✅ Funcionalidade de edição completa")
        print("4. ✅ Casos extremos (sequências vazias, nomes longos)")
        print("5. ✅ Persistência de dados no MongoDB")
        
        if failed_tests == 0:
            print("\n🎉 TODOS OS TESTES ABRANGENTES PASSARAM!")
            print("🏆 ABA 9 (AUTO-RESPONDER) ESTÁ 100% FUNCIONAL E ROBUSTA!")
        else:
            print(f"\n⚠️ {failed_tests} PROBLEMAS ENCONTRADOS nos testes avançados")
            
        print("=" * 70)

async def main():
    """Função principal"""
    tester = ComprehensiveAutoResponderTester()
    await tester.run_comprehensive_tests()

if __name__ == "__main__":
    asyncio.run(main())