#!/usr/bin/env python3
"""
🔍 DEBUG: Encontrar agente correto para acessar ticket do Fabio Silva

PROBLEMA IDENTIFICADO:
- Ticket "Fabio Silva" existe no banco
- Departamento: 7b9b7fdd-dc08-4cda-833f-e0a27c5b67c0
- Reseller: 7ca75660-22d8-448b-8413-c745130baca5
- Credenciais fabio123/102030ab não funcionam

OBJETIVO:
- Encontrar agente que tem acesso ao departamento correto
- Testar login com credenciais corretas
- Verificar se consegue ver o ticket
"""

import requests
import json
import os

BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://wppconnect-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# IDs encontrados no teste anterior
FABIO_TICKET_DEPARTMENT = "7b9b7fdd-dc08-4cda-833f-e0a27c5b67c0"
FABIO_TICKET_RESELLER = "7ca75660-22d8-448b-8413-c745130baca5"

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

def debug_agents_and_departments():
    print("🔍 DEBUG: Encontrando agente correto para ticket do Fabio Silva")
    print("=" * 70)
    
    # 1. Login como admin
    print("1️⃣ Fazendo login como admin...")
    success, admin_response = make_request("POST", "/auth/admin/login", {"password": "102030@ab"})
    
    if not success:
        print(f"❌ Erro no login admin: {admin_response}")
        return
    
    admin_token = admin_response["token"]
    print("✅ Login admin OK")
    
    # 2. Buscar todos os agentes
    print("\n2️⃣ Buscando todos os agentes...")
    success, agents = make_request("GET", "/agents", token=admin_token)
    
    if not success:
        print(f"❌ Erro ao buscar agentes: {agents}")
        return
    
    print(f"✅ Encontrados {len(agents)} agentes")
    
    # 3. Buscar todos os departamentos
    print("\n3️⃣ Buscando todos os departamentos...")
    success, departments = make_request("GET", "/ai/departments", token=admin_token)
    
    if not success:
        print(f"❌ Erro ao buscar departamentos: {departments}")
        return
    
    print(f"✅ Encontrados {len(departments)} departamentos")
    
    # 4. Encontrar departamento do ticket Fabio Silva
    print(f"\n4️⃣ Procurando departamento do ticket Fabio Silva: {FABIO_TICKET_DEPARTMENT}")
    fabio_department = None
    for dept in departments:
        if dept.get('id') == FABIO_TICKET_DEPARTMENT:
            fabio_department = dept
            break
    
    if fabio_department:
        print(f"✅ Departamento encontrado:")
        print(f"   ID: {fabio_department.get('id')}")
        print(f"   Nome: {fabio_department.get('name')}")
        print(f"   Reseller: {fabio_department.get('reseller_id')}")
        print(f"   Agent IDs: {fabio_department.get('agent_ids', [])}")
    else:
        print(f"❌ Departamento não encontrado!")
        return
    
    # 5. Encontrar agentes que têm acesso a este departamento
    print(f"\n5️⃣ Procurando agentes com acesso ao departamento...")
    
    # Agentes da mesma revenda
    reseller_agents = [a for a in agents if a.get('reseller_id') == FABIO_TICKET_RESELLER]
    print(f"   Agentes da revenda {FABIO_TICKET_RESELLER}: {len(reseller_agents)}")
    
    for agent in reseller_agents:
        print(f"\n   👤 Agente: {agent.get('name', 'N/A')}")
        print(f"      ID: {agent.get('id')}")
        print(f"      Login: {agent.get('login')}")
        print(f"      Reseller: {agent.get('reseller_id')}")
        print(f"      Departamentos: {agent.get('department_ids', [])}")
        
        # Verificar se tem acesso ao departamento
        agent_depts = agent.get('department_ids', [])
        dept_agent_ids = fabio_department.get('agent_ids', [])
        
        has_access = False
        if len(agent_depts) == 0:
            print(f"      🔓 Sem departamentos específicos (acesso a todos)")
            has_access = True
        elif FABIO_TICKET_DEPARTMENT in agent_depts:
            print(f"      ✅ TEM acesso ao departamento (via department_ids)")
            has_access = True
        elif len(dept_agent_ids) == 0:
            print(f"      🔓 Departamento sem agentes específicos (todos têm acesso)")
            has_access = True
        elif agent.get('id') in dept_agent_ids:
            print(f"      ✅ TEM acesso ao departamento (via agent_ids)")
            has_access = True
        else:
            print(f"      ❌ NÃO tem acesso ao departamento")
        
        if has_access:
            print(f"      🎯 ESTE AGENTE PODE VER O TICKET!")
    
    # 6. Testar login com agentes conhecidos
    print(f"\n6️⃣ Testando logins conhecidos...")
    
    known_agents = [
        {"login": "fabio123", "password": "102030ab"},
        {"login": "fabioteste", "password": "123"},
        {"login": "fabio", "password": "123"},
        {"login": "fabio", "password": "102030ab"},
    ]
    
    for cred in known_agents:
        print(f"\n   🔑 Testando: {cred['login']} / {cred['password']}")
        success, response = make_request("POST", "/auth/agent/login", cred)
        
        if success and "token" in response:
            token = response["token"]
            user_data = response.get("user_data", {})
            reseller_id = response.get("reseller_id")
            
            print(f"   ✅ LOGIN OK!")
            print(f"      Agent ID: {user_data.get('id')}")
            print(f"      Nome: {user_data.get('name')}")
            print(f"      Reseller: {reseller_id}")
            
            # Testar se consegue ver tickets
            success, tickets = make_request("GET", "/tickets", token=token)
            if success:
                fabio_found = False
                for ticket in tickets:
                    if "fabio silva" in ticket.get('client_name', '').lower():
                        fabio_found = True
                        break
                
                print(f"      📊 Vê {len(tickets)} tickets")
                if fabio_found:
                    print(f"      🎯 CONSEGUE VER O TICKET DO FABIO SILVA!")
                else:
                    print(f"      ❌ Não consegue ver o ticket do Fabio Silva")
            else:
                print(f"      ❌ Erro ao buscar tickets: {tickets}")
        else:
            print(f"   ❌ Login falhou: {response}")

if __name__ == "__main__":
    debug_agents_and_departments()