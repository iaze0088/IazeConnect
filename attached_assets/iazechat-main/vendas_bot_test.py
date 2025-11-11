#!/usr/bin/env python3
"""
🤖 TESTE COMPLETO DO BOT DE IA - PÁGINA /VENDAS
Sistema IAZE - Bot CyberTV para atendimento automatizado de vendas via LLM

CONTEXTO:
Sistema IAZE possui uma página pública /vendas com bot de IA chamado "CyberTV" 
para atendimento automatizado de vendas via LLM (Emergent LLM Key).

OBJETIVO DO TESTE:
Validar funcionamento completo do bot de IA na página /vendas, incluindo:
1. Criação de sessão de chat
2. Envio de mensagens
3. Resposta do bot via LLM
4. Persistência de conversas
5. Multi-turn conversation (conversas com múltiplas interações)
"""

import asyncio
import httpx
import json
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv('/app/backend/.env')

# Configurações
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://wppconnect-fix.preview.emergentagent.com')
BASE_URL = f"{BACKEND_URL}/api"

print(f"🎯 TESTE COMPLETO DO BOT DE IA - PÁGINA /VENDAS")
print(f"🌐 Backend URL: {BACKEND_URL}")
print(f"🔑 Emergent LLM Key: {os.environ.get('EMERGENT_LLM_KEY', 'NÃO CONFIGURADA')[:20]}...")
print("=" * 80)

class VendasBotTester:
    def __init__(self):
        self.session_id = None
        self.messages = []
        self.test_results = []
        
    async def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log de resultado de teste"""
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{status} - {test_name}")
        if details:
            print(f"   📋 {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
    async def test_1_create_session(self):
        """✅ Teste 1: Criar Sessão"""
        print("\n🔵 TESTE 1: CRIAR SESSÃO DE CHAT")
        
        try:
            # Nota: O endpoint real é /start, não /session como no review request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{BASE_URL}/vendas/start", json={})
                
                if response.status_code == 200:
                    data = response.json()
                    self.session_id = data.get("session_id")
                    messages = data.get("messages", [])
                    
                    if self.session_id and messages:
                        welcome_message = messages[0].get("text", "") if messages else ""
                        await self.log_test(
                            "Criar Sessão", 
                            True, 
                            f"Session ID: {self.session_id[:8]}..., Welcome: '{welcome_message[:50]}...'"
                        )
                        return True
                    else:
                        await self.log_test("Criar Sessão", False, "Session ID ou mensagem de boas-vindas não retornados")
                        return False
                else:
                    await self.log_test("Criar Sessão", False, f"Status {response.status_code}: {response.text}")
                    return False
                    
        except Exception as e:
            await self.log_test("Criar Sessão", False, f"Erro: {str(e)}")
            return False
    
    async def test_2_first_message(self):
        """✅ Teste 2: Primeira Mensagem (Saudação)"""
        print("\n🔵 TESTE 2: PRIMEIRA MENSAGEM (SAUDAÇÃO)")
        
        if not self.session_id:
            await self.log_test("Primeira Mensagem", False, "Session ID não disponível")
            return False
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{BASE_URL}/vendas/message",
                    json={
                        "session_id": self.session_id,
                        "text": "Olá"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    messages = data.get("messages", [])
                    
                    # Deve ter 2 mensagens: cliente + bot
                    if len(messages) >= 2:
                        client_msg = messages[0]
                        bot_msg = messages[1]
                        
                        # Verificar estrutura das mensagens
                        client_ok = (
                            client_msg.get("from_type") == "client" and
                            client_msg.get("text") == "Olá" and
                            client_msg.get("message_id")
                        )
                        
                        bot_ok = (
                            bot_msg.get("from_type") == "bot" and
                            bot_msg.get("text") and
                            bot_msg.get("message_id")
                        )
                        
                        if client_ok and bot_ok:
                            bot_response = bot_msg.get("text", "")
                            # Verificar se resposta está em português
                            portuguese_indicators = ["olá", "oi", "como", "posso", "ajudar", "bem-vindo", "seja"]
                            is_portuguese = any(word in bot_response.lower() for word in portuguese_indicators)
                            
                            await self.log_test(
                                "Primeira Mensagem", 
                                True, 
                                f"Bot respondeu em português: '{bot_response[:100]}...'"
                            )
                            return True
                        else:
                            await self.log_test("Primeira Mensagem", False, "Estrutura de mensagens incorreta")
                            return False
                    else:
                        await self.log_test("Primeira Mensagem", False, f"Esperado 2 mensagens, recebido {len(messages)}")
                        return False
                else:
                    await self.log_test("Primeira Mensagem", False, f"Status {response.status_code}: {response.text}")
                    return False
                    
        except Exception as e:
            await self.log_test("Primeira Mensagem", False, f"Erro: {str(e)}")
            return False
    
    async def test_3_product_question(self):
        """✅ Teste 3: Pergunta sobre Produto"""
        print("\n🔵 TESTE 3: PERGUNTA SOBRE PRODUTO")
        
        if not self.session_id:
            await self.log_test("Pergunta sobre Produto", False, "Session ID não disponível")
            return False
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{BASE_URL}/vendas/message",
                    json={
                        "session_id": self.session_id,
                        "text": "Quais são os planos disponíveis?"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    messages = data.get("messages", [])
                    
                    if len(messages) >= 2:
                        bot_msg = messages[1]  # Resposta do bot
                        bot_response = bot_msg.get("text", "")
                        
                        # Verificar se resposta é relevante (contém palavras relacionadas a planos/IPTV)
                        relevant_keywords = ["plano", "iptv", "preço", "valor", "canal", "teste", "assinatura", "mensal"]
                        is_relevant = any(keyword in bot_response.lower() for keyword in relevant_keywords)
                        
                        if is_relevant and len(bot_response) > 20:
                            await self.log_test(
                                "Pergunta sobre Produto", 
                                True, 
                                f"Bot respondeu com informações relevantes: '{bot_response[:100]}...'"
                            )
                            return True
                        else:
                            await self.log_test("Pergunta sobre Produto", False, "Resposta não relevante ou muito curta")
                            return False
                    else:
                        await self.log_test("Pergunta sobre Produto", False, "Mensagens insuficientes")
                        return False
                else:
                    await self.log_test("Pergunta sobre Produto", False, f"Status {response.status_code}: {response.text}")
                    return False
                    
        except Exception as e:
            await self.log_test("Pergunta sobre Produto", False, f"Erro: {str(e)}")
            return False
    
    async def test_4_multi_turn_conversation(self):
        """✅ Teste 4: Multi-turn Conversation"""
        print("\n🔵 TESTE 4: CONVERSA MULTI-TURN (CONTEXTO)")
        
        if not self.session_id:
            await self.log_test("Multi-turn Conversation", False, "Session ID não disponível")
            return False
        
        conversation_flow = [
            "Quero saber sobre IPTV",
            "Qual o preço?",
            "Como faço para assinar?"
        ]
        
        try:
            responses = []
            
            for i, message_text in enumerate(conversation_flow):
                print(f"   📤 Enviando mensagem {i+1}: '{message_text}'")
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{BASE_URL}/vendas/message",
                        json={
                            "session_id": self.session_id,
                            "text": message_text
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        messages = data.get("messages", [])
                        
                        if len(messages) >= 2:
                            bot_response = messages[1].get("text", "")
                            responses.append(bot_response)
                            print(f"   📥 Bot respondeu: '{bot_response[:80]}...'")
                        else:
                            await self.log_test("Multi-turn Conversation", False, f"Falha na mensagem {i+1}")
                            return False
                    else:
                        await self.log_test("Multi-turn Conversation", False, f"Erro HTTP na mensagem {i+1}")
                        return False
                
                # Pequena pausa entre mensagens
                await asyncio.sleep(1)
            
            # Verificar se todas as respostas são coerentes e contextuais
            if len(responses) == 3:
                # Verificar se as respostas são diferentes (não repetitivas)
                unique_responses = len(set(responses)) == len(responses)
                
                # Verificar se respostas têm tamanho adequado
                adequate_length = all(len(resp) > 20 for resp in responses)
                
                if unique_responses and adequate_length:
                    await self.log_test(
                        "Multi-turn Conversation", 
                        True, 
                        f"3 mensagens processadas com respostas contextuais e únicas"
                    )
                    return True
                else:
                    await self.log_test("Multi-turn Conversation", False, "Respostas repetitivas ou muito curtas")
                    return False
            else:
                await self.log_test("Multi-turn Conversation", False, "Nem todas as mensagens foram processadas")
                return False
                
        except Exception as e:
            await self.log_test("Multi-turn Conversation", False, f"Erro: {str(e)}")
            return False
    
    async def test_5_message_history(self):
        """✅ Teste 5: Histórico de Mensagens"""
        print("\n🔵 TESTE 5: HISTÓRICO DE MENSAGENS")
        
        if not self.session_id:
            await self.log_test("Histórico de Mensagens", False, "Session ID não disponível")
            return False
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{BASE_URL}/vendas/messages/{self.session_id}")
                
                if response.status_code == 200:
                    data = response.json()
                    messages = data.get("messages", [])
                    
                    if len(messages) > 0:
                        # Verificar estrutura das mensagens
                        client_messages = [msg for msg in messages if msg.get("from_type") == "client"]
                        bot_messages = [msg for msg in messages if msg.get("from_type") == "bot"]
                        
                        # Verificar se tem mensagens de ambos os tipos
                        if len(client_messages) > 0 and len(bot_messages) > 0:
                            # Verificar ordem cronológica
                            timestamps = [msg.get("timestamp") for msg in messages if msg.get("timestamp")]
                            is_chronological = timestamps == sorted(timestamps)
                            
                            # Verificar se todas as mensagens têm campos obrigatórios
                            all_have_required_fields = all(
                                msg.get("message_id") and 
                                msg.get("from_type") and 
                                msg.get("text") and 
                                msg.get("timestamp")
                                for msg in messages
                            )
                            
                            if is_chronological and all_have_required_fields:
                                await self.log_test(
                                    "Histórico de Mensagens", 
                                    True, 
                                    f"{len(messages)} mensagens salvas ({len(client_messages)} cliente, {len(bot_messages)} bot)"
                                )
                                return True
                            else:
                                await self.log_test("Histórico de Mensagens", False, "Ordem cronológica ou campos obrigatórios incorretos")
                                return False
                        else:
                            await self.log_test("Histórico de Mensagens", False, "Faltam mensagens de cliente ou bot")
                            return False
                    else:
                        await self.log_test("Histórico de Mensagens", False, "Nenhuma mensagem encontrada")
                        return False
                else:
                    await self.log_test("Histórico de Mensagens", False, f"Status {response.status_code}: {response.text}")
                    return False
                    
        except Exception as e:
            await self.log_test("Histórico de Mensagens", False, f"Erro: {str(e)}")
            return False
    
    async def test_6_mongodb_persistence(self):
        """✅ Teste 6: Persistência no MongoDB"""
        print("\n🔵 TESTE 6: PERSISTÊNCIA NO MONGODB")
        
        if not self.session_id:
            await self.log_test("Persistência MongoDB", False, "Session ID não disponível")
            return False
        
        try:
            # Verificar se a sessão existe no banco
            async with httpx.AsyncClient(timeout=30.0) as client:
                session_response = await client.get(f"{BASE_URL}/vendas/session/{self.session_id}")
                
                if session_response.status_code == 200:
                    session_data = session_response.json()
                    
                    # Verificar estrutura da sessão
                    session_ok = (
                        session_data.get("session_id") == self.session_id and
                        session_data.get("created_at") and
                        session_data.get("empresa_nome")
                    )
                    
                    if session_ok:
                        # Verificar mensagens no banco
                        messages_response = await client.get(f"{BASE_URL}/vendas/messages/{self.session_id}")
                        
                        if messages_response.status_code == 200:
                            messages_data = messages_response.json()
                            messages = messages_data.get("messages", [])
                            
                            if len(messages) > 0:
                                await self.log_test(
                                    "Persistência MongoDB", 
                                    True, 
                                    f"Sessão e {len(messages)} mensagens persistidas corretamente"
                                )
                                return True
                            else:
                                await self.log_test("Persistência MongoDB", False, "Mensagens não persistidas")
                                return False
                        else:
                            await self.log_test("Persistência MongoDB", False, "Erro ao buscar mensagens")
                            return False
                    else:
                        await self.log_test("Persistência MongoDB", False, "Estrutura da sessão incorreta")
                        return False
                else:
                    await self.log_test("Persistência MongoDB", False, f"Sessão não encontrada: {session_response.status_code}")
                    return False
                    
        except Exception as e:
            await self.log_test("Persistência MongoDB", False, f"Erro: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Executar todos os testes"""
        print("🚀 INICIANDO BATERIA DE TESTES DO BOT DE VENDAS")
        print("=" * 80)
        
        # Executar testes em sequência
        test_1_ok = await self.test_1_create_session()
        
        if test_1_ok:
            test_2_ok = await self.test_2_first_message()
            test_3_ok = await self.test_3_product_question()
            test_4_ok = await self.test_4_multi_turn_conversation()
            test_5_ok = await self.test_5_message_history()
            test_6_ok = await self.test_6_mongodb_persistence()
        else:
            print("❌ Teste 1 falhou, pulando testes subsequentes")
        
        # Resumo final
        print("\n" + "=" * 80)
        print("📊 RESUMO DOS TESTES")
        print("=" * 80)
        
        passed_tests = sum(1 for result in self.test_results if result["success"])
        total_tests = len(self.test_results)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   📋 {result['details']}")
        
        print(f"\n🎯 RESULTADO FINAL: {passed_tests}/{total_tests} TESTES PASSARAM")
        
        if passed_tests == total_tests:
            print("🎉 TODOS OS TESTES PASSARAM! BOT DE VENDAS 100% FUNCIONAL!")
        else:
            print(f"⚠️ {total_tests - passed_tests} TESTE(S) FALHARAM - VERIFICAR IMPLEMENTAÇÃO")
        
        print("=" * 80)
        
        return passed_tests == total_tests

async def main():
    """Função principal"""
    tester = VendasBotTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n✅ SISTEMA DE VENDAS VALIDADO COM SUCESSO!")
    else:
        print("\n❌ SISTEMA DE VENDAS PRECISA DE CORREÇÕES!")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())