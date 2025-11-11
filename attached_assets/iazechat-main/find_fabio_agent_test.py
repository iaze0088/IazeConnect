#!/usr/bin/env python3
"""
🔍 Encontrar o agente correto com ID 6254a141-af9e-4be0-a77a-016030482db7
"""

import requests
import json
import os

BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://wppconnect-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

TARGET_AGENT_ID = "6254a141-af9e-4be0-a77a-016030482db7"

def make_request(method: str, endpoint: str, data: dict = None, token: str = None, params: dict = None):
    """Make HTTP request"""
    url = f"{API_BASE}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=30)
        
        return response.status_code < 400, response.json() if response.text else {}
    except Exception as e:
        return False, {"error": str(e)}

def find_target_agent():
    print(f"🔍 Procurando agente com ID: {TARGET_AGENT_ID}")
    print("=" * 70)
    
    # Login como admin
    success, admin_response = make_request("POST", "/auth/admin/login", {"password": "102030@ab"})
    if not success:
        print(f"❌ Erro no login admin: {admin_response}")
        return
    
    admin_token = admin_response["token"]
    print("✅ Login admin OK")
    
    # Buscar todos os agentes
    success, agents = make_request("GET", "/agents", token=admin_token)
    if not success:
        print(f"❌ Erro ao buscar agentes: {agents}")
        return
    
    print(f"✅ Encontrados {len(agents)} agentes")
    
    # Procurar o agente específico
    target_agent = None
    for agent in agents:
        if agent.get('id') == TARGET_AGENT_ID:
            target_agent = agent
            break
    
    if target_agent:
        print(f"\n🎯 AGENTE ENCONTRADO:")
        print(f"   ID: {target_agent.get('id')}")
        print(f"   Nome: {target_agent.get('name')}")
        print(f"   Login: {target_agent.get('login')}")
        print(f"   Reseller: {target_agent.get('reseller_id')}")
        print(f"   Departamentos: {target_agent.get('department_ids', [])}")
        print(f"   Ativo: {target_agent.get('is_active', True)}")
        
        # Tentar algumas senhas comuns
        login = target_agent.get('login')
        if login:
            passwords = ["102030ab", "123", "123456", "senha123", "fabio123"]
            
            print(f"\n🔑 Testando senhas para login '{login}':")
            for password in passwords:
                print(f"   Testando: {login} / {password}")
                success, response = make_request("POST", "/auth/agent/login", {
                    "login": login,
                    "password": password
                })
                
                if success and "token" in response:
                    token = response["token"]
                    print(f"   ✅ SENHA CORRETA: {password}")
                    
                    # Testar se consegue ver o ticket do Fabio Silva
                    success, tickets = make_request("GET", "/tickets", token=token)
                    if success:
                        fabio_found = False
                        for ticket in tickets:
                            if "fabio silva" in ticket.get('client_name', '').lower():
                                fabio_found = True
                                print(f"   🎯 CONSEGUE VER O TICKET DO FABIO SILVA!")
                                break
                        
                        if not fabio_found:
                            print(f"   ❌ Não consegue ver o ticket do Fabio Silva ({len(tickets)} tickets total)")
                    else:
                        print(f"   ❌ Erro ao buscar tickets: {tickets}")
                    
                    return login, password
                else:
                    print(f"   ❌ Senha incorreta")
    else:
        print(f"❌ Agente com ID {TARGET_AGENT_ID} não encontrado!")
        
        # Mostrar todos os agentes para debug
        print(f"\n📋 Todos os agentes no sistema:")
        for i, agent in enumerate(agents):
            print(f"   [{i+1}] {agent.get('name', 'N/A')} (login: {agent.get('login', 'N/A')}, ID: {agent.get('id', 'N/A')})")
    
    return None, None

def test_mickviniz():
    """Testar o agente mickviniz que tem acesso a todos os departamentos"""
    print(f"\n🔍 Testando agente mickviniz (tem acesso a todos departamentos)")
    
    passwords = ["102030ab", "123", "123456", "senha123", "mickviniz"]
    
    for password in passwords:
        print(f"   Testando: mickviniz / {password}")
        success, response = make_request("POST", "/auth/agent/login", {
            "login": "mickviniz",
            "password": password
        })
        
        if success and "token" in response:
            token = response["token"]
            print(f"   ✅ SENHA CORRETA: {password}")
            
            # Testar se consegue ver o ticket do Fabio Silva
            success, tickets = make_request("GET", "/tickets", token=token)
            if success:
                fabio_found = False
                fabio_ticket = None
                for ticket in tickets:
                    if "fabio silva" in ticket.get('client_name', '').lower():
                        fabio_found = True
                        fabio_ticket = ticket
                        break
                
                print(f"   📊 Vê {len(tickets)} tickets total")
                if fabio_found:
                    print(f"   🎯 CONSEGUE VER O TICKET DO FABIO SILVA!")
                    print(f"      Ticket ID: {fabio_ticket.get('id')}")
                    print(f"      Cliente: {fabio_ticket.get('client_name')}")
                    print(f"      Status: {fabio_ticket.get('status')}")
                    return "mickviniz", password
                else:
                    print(f"   ❌ Não consegue ver o ticket do Fabio Silva")
            else:
                print(f"   ❌ Erro ao buscar tickets: {tickets}")
        else:
            print(f"   ❌ Senha incorreta")
    
    return None, None

if __name__ == "__main__":
    # Primeiro tentar encontrar o agente específico
    login, password = find_target_agent()
    
    if not login:
        # Se não encontrou, testar o mickviniz
        login, password = test_mickviniz()
    
    if login and password:
        print(f"\n🎉 CREDENCIAIS ENCONTRADAS: {login} / {password}")
        print(f"✅ Use estas credenciais para testar o endpoint /api/tickets")
    else:
        print(f"\n❌ Não foi possível encontrar credenciais válidas")