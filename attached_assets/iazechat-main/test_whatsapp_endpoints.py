#!/usr/bin/env python3
"""
Teste simples dos endpoints WhatsApp
"""

import requests
import json

# Configuration
BACKEND_URL = "https://suporte.help/api"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "102030@ab"

def test_endpoints():
    print("🔐 Fazendo login admin...")
    
    # 1. Admin Login
    login_response = requests.post(f"{BACKEND_URL}/auth/admin/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    
    if login_response.status_code != 200:
        print(f"❌ Erro no login: {login_response.status_code}")
        return
    
    token = login_response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login realizado com sucesso")
    
    # 2. Listar conexões
    print("\n📱 Listando conexões WhatsApp...")
    connections_response = requests.get(f"{BACKEND_URL}/whatsapp/connections", headers=headers)
    
    if connections_response.status_code != 200:
        print(f"❌ Erro ao listar conexões: {connections_response.status_code}")
        return
    
    connections = connections_response.json()
    print(f"✅ Encontradas {len(connections)} conexões")
    
    if not connections:
        print("❌ Nenhuma conexão encontrada para testar")
        return
    
    connection_id = connections[0]["id"]
    print(f"🆔 Usando connection_id: {connection_id}")
    
    # 3. Testar refresh-qr
    print(f"\n🔄 Testando refresh-qr...")
    refresh_url = f"{BACKEND_URL}/whatsapp/connections/{connection_id}/refresh-qr"
    print(f"URL: {refresh_url}")
    
    refresh_response = requests.post(refresh_url, headers=headers)
    print(f"Status: {refresh_response.status_code}")
    print(f"Response: {refresh_response.text}")
    
    # 4. Testar restart-session
    print(f"\n🔄 Testando restart-session...")
    restart_url = f"{BACKEND_URL}/whatsapp/connections/{connection_id}/restart-session"
    print(f"URL: {restart_url}")
    
    restart_response = requests.post(restart_url, headers=headers)
    print(f"Status: {restart_response.status_code}")
    print(f"Response: {restart_response.text}")

if __name__ == "__main__":
    test_endpoints()