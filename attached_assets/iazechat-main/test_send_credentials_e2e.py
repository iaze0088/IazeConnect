"""
Teste E2E: Enviar mensagens com usuário/senha via API
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

async def test_send_credentials():
    backend_url = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
    
    print("=" * 80)
    print("TESTE E2E: Enviar credenciais via API")
    print("=" * 80)
    
    # Casos de teste
    test_messages = [
        ("usuario: teste123 senha: abc123", "Formato simples minúsculo"),
        ("Usuario: teste123 Senha: abc123", "Formato capitalizado"),
        ("Usuário: teste123 Senha: abc123", "Com acento"),
        ("USUARIO: teste123 SENHA: abc123", "Tudo maiúsculo"),
        ("esse aqui é seu usuario e senha segue\nUsuario: teste123\nSenha: abc123", "Com texto antes e quebras de linha"),
        ("Olá! Suas credenciais:\n\nUsuario: teste123\nSenha: abc123\n\nQualquer dúvida me avise!", "Com saudação e texto"),
        ("user: teste123 password: abc123", "Inglês"),
    ]
    
    print("\n🔑 LOGIN COMO AGENTE:")
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Login como agente
        login_response = await client.post(
            f"{backend_url}/api/auth/login",
            json={"email": "fabio@teste.com", "password": "fabio123"}
        )
        
        if login_response.status_code != 200:
            print(f"   ❌ Erro no login: {login_response.status_code}")
            print(f"   Response: {login_response.text}")
            return
        
        login_data = login_response.json()
        token = login_data.get("token")
        agent_id = login_data.get("user", {}).get("id")
        
        print(f"   ✅ Login bem-sucedido!")
        print(f"   Agent ID: {agent_id}")
        print(f"   Token: {token[:30]}...")
        
        # Buscar um ticket qualquer para enviar mensagens
        print("\n📋 BUSCANDO TICKETS:")
        tickets_response = await client.get(
            f"{backend_url}/api/tickets",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if tickets_response.status_code != 200:
            print(f"   ❌ Erro ao buscar tickets: {tickets_response.status_code}")
            return
        
        tickets_data = tickets_response.json()
        tickets = tickets_data.get("tickets", [])
        
        if not tickets:
            print(f"   ⚠️ Nenhum ticket encontrado. Criando ticket de teste...")
            # Criar ticket de teste
            # TODO: Implementar criação de ticket de teste se necessário
            print(f"   ⚠️ Pule este teste ou crie um ticket manualmente")
            return
        
        ticket_id = tickets[0].get("id")
        print(f"   ✅ Ticket encontrado: {ticket_id}")
        
        # Testar envio de cada mensagem
        print(f"\n🧪 TESTANDO ENVIO DE MENSAGENS:\n")
        
        passed = 0
        failed = 0
        
        for text, description in test_messages:
            print(f"   Testando: {description}")
            print(f"   Texto: {text[:60]}...")
            
            response = await client.post(
                f"{backend_url}/api/messages",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "ticket_id": ticket_id,
                    "text": text,
                    "from_type": "agent",
                    "from_id": agent_id,
                    "kind": "text"
                }
            )
            
            if response.status_code == 200:
                print(f"   ✅ SUCESSO - Mensagem enviada!\n")
                passed += 1
            else:
                print(f"   ❌ FALHOU - Status: {response.status_code}")
                print(f"   Resposta: {response.text}\n")
                failed += 1
        
        print("=" * 80)
        print(f"RESULTADO: {passed} passaram, {failed} falharam de {len(test_messages)} testes")
        print("=" * 80)
        
        if failed == 0:
            print("\n🎉 TODOS OS TESTES PASSARAM! Credenciais podem ser enviadas em qualquer formato!")
        else:
            print(f"\n⚠️ {failed} TESTES FALHARAM. Verifique os logs acima.")

asyncio.run(test_send_credentials())
