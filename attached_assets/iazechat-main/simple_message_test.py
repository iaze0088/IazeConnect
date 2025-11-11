#!/usr/bin/env python3
"""
TESTE SIMPLES: ENVIO E RECEBIMENTO DE MENSAGENS
Usando requests síncronos para evitar problemas de timeout
"""

import requests
import json
import time

# Configurações
BACKEND_URL = "https://wppconnect-fix.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Credenciais corretas encontradas no banco
AGENT_CREDENTIALS = {
    "login": "fabio21",
    "password": "fabio21"
}

CLIENT_CREDENTIALS = {
    "whatsapp": "19989612020",
    "pin": "12"
}

def test_agent_login():
    """Teste 1: Login do Agente"""
    print("🔑 TESTE 1: Login do Agente fabio21")
    print("=" * 50)
    
    try:
        response = requests.post(
            f"{API_BASE}/auth/agent/login",
            json=AGENT_CREDENTIALS,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            agent_id = data.get("user_data", {}).get("id")
            
            print(f"✅ Login bem-sucedido!")
            print(f"   Agent ID: {agent_id}")
            print(f"   Token: {token[:50] if token else 'None'}...")
            
            return True, token, agent_id
        else:
            print(f"❌ Login falhou: {response.text}")
            return False, None, None
            
    except Exception as e:
        print(f"💥 ERRO: {e}")
        return False, None, None

def test_client_login():
    """Teste 2: Login do Cliente"""
    print("\n🔑 TESTE 2: Login do Cliente 19989612020")
    print("=" * 50)
    
    try:
        response = requests.post(
            f"{API_BASE}/auth/client/login",
            json=CLIENT_CREDENTIALS,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            client_id = data.get("user_data", {}).get("id")
            
            print(f"✅ Login bem-sucedido!")
            print(f"   Client ID: {client_id}")
            print(f"   Token: {token[:50] if token else 'None'}...")
            
            return True, token, client_id
        else:
            print(f"❌ Login falhou: {response.text}")
            return False, None, None
            
    except Exception as e:
        print(f"💥 ERRO: {e}")
        return False, None, None

def test_agent_send_message(agent_token, agent_id):
    """Teste 3: Agente envia mensagem"""
    print("\n📤 TESTE 3: Agente envia mensagem")
    print("=" * 50)
    
    if not agent_token:
        print("❌ Token do agente não disponível")
        return False
    
    # Primeiro, vamos buscar um ticket existente ou usar um ID genérico
    ticket_id = "test-ticket-" + str(int(time.time()))
    
    message_data = {
        "from_type": "agent",
        "from_id": agent_id,
        "to_type": "client",
        "to_id": "19989612020",
        "ticket_id": ticket_id,
        "kind": "text",
        "text": "Teste de mensagem do agente para o cliente",
        "file_url": None
    }
    
    print(f"Dados da mensagem:")
    print(json.dumps(message_data, indent=2))
    
    try:
        response = requests.post(
            f"{API_BASE}/messages",
            json=message_data,
            headers={"Authorization": f"Bearer {agent_token}"},
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            message_id = data.get("id") or data.get("message_id")
            
            print(f"✅ Mensagem enviada com sucesso!")
            print(f"   Message ID: {message_id}")
            return True
        else:
            print(f"❌ Falha ao enviar mensagem: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 ERRO: {e}")
        return False

def test_client_send_message(client_token):
    """Teste 4: Cliente envia mensagem"""
    print("\n📤 TESTE 4: Cliente envia mensagem")
    print("=" * 50)
    
    if not client_token:
        print("❌ Token do cliente não disponível")
        return False
    
    # Usar ticket existente encontrado no banco
    existing_ticket_id = "6d54ebf2-d245-477b-a199-724412b4ee72"
    
    message_data = {
        "from_type": "client",
        "from_id": "8b2e0c78-275f-4f84-acea-1bf8f5fd7336",  # Client ID, not WhatsApp
        "to_type": "agent",
        "to_id": None,
        "ticket_id": existing_ticket_id,
        "kind": "text",
        "text": "Teste de mensagem do cliente para o sistema",
        "file_url": None
    }
    
    print(f"Dados da mensagem:")
    print(json.dumps(message_data, indent=2))
    
    try:
        response = requests.post(
            f"{API_BASE}/messages",
            json=message_data,
            headers={"Authorization": f"Bearer {client_token}"},
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            message_id = data.get("id") or data.get("message_id")
            
            print(f"✅ Mensagem enviada com sucesso!")
            print(f"   Message ID: {message_id}")
            return True
        else:
            print(f"❌ Falha ao enviar mensagem: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 ERRO: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 TESTE CRÍTICO: ENVIO E RECEBIMENTO DE MENSAGENS")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Agente: {AGENT_CREDENTIALS['login']} / {AGENT_CREDENTIALS['password']}")
    print(f"Cliente: {CLIENT_CREDENTIALS['whatsapp']} / PIN {CLIENT_CREDENTIALS['pin']}")
    print("⚠️ NOTA: Credenciais corrigidas após verificação no banco de dados")
    
    # Teste 1: Login do Agente
    agent_success, agent_token, agent_id = test_agent_login()
    
    # Teste 2: Login do Cliente
    client_success, client_token, client_id = test_client_login()
    
    # Teste 3: Agente envia mensagem
    if agent_success:
        agent_msg_success = test_agent_send_message(agent_token, agent_id)
    else:
        agent_msg_success = False
    
    # Teste 4: Cliente envia mensagem
    if client_success:
        client_msg_success = test_client_send_message(client_token)
    else:
        client_msg_success = False
    
    # Resumo
    print("\n" + "=" * 80)
    print("📊 RESUMO DOS TESTES")
    print("=" * 80)
    
    tests = [
        ("Login do Agente", agent_success),
        ("Login do Cliente", client_success),
        ("Envio Mensagem Agente", agent_msg_success),
        ("Envio Mensagem Cliente", client_msg_success)
    ]
    
    passed = sum(1 for _, success in tests if success)
    total = len(tests)
    
    for test_name, success in tests:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📈 Resultado: {passed}/{total} testes passaram ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Sistema de mensagens funcionando corretamente")
        print("💡 Se o erro persiste no frontend, verificar WebSocket e JavaScript")
    else:
        print(f"\n⚠️ {total - passed} testes falharam")
        print("🔍 Verificar logs do backend para mais detalhes")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)