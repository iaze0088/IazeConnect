#!/usr/bin/env python3
"""
Teste do endpoint WhatsApp
"""
import requests
import json

BACKEND_URL = "https://suporte.help/api"

# Fazer login como admin
print("🔐 Fazendo login...")
login_response = requests.post(
    f"{BACKEND_URL}/auth/admin/login",
    json={
        "email": "admin@admin.com",
        "password": "102030@ab"
    }
)

if login_response.status_code != 200:
    print(f"❌ Erro no login: {login_response.status_code}")
    print(login_response.text)
    exit(1)

token = login_response.json()["access_token"]
print(f"✅ Login OK - Token: {token[:20]}...")

# Testar GET /whatsapp/connections
print("\n📡 Testando GET /whatsapp/connections...")
headers = {"Authorization": f"Bearer {token}"}

response = requests.get(f"{BACKEND_URL}/whatsapp/connections", headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}")

if response.status_code == 404:
    print("\n❌ ENDPOINT NÃO ENCONTRADO!")
    print("Vamos testar se o endpoint existe sem o prefixo /api...")
    
    response2 = requests.get("https://suporte.help/whatsapp/connections", headers=headers)
    print(f"Status sem /api: {response2.status_code}")
    print(f"Response: {response2.text[:500]}")

# Testar POST /whatsapp/connections
print("\n📡 Testando POST /whatsapp/connections...")
response = requests.post(
    f"{BACKEND_URL}/whatsapp/connections",
    headers=headers,
    json={
        "reseller_id": None,
        "max_received_daily": 200,
        "max_sent_daily": 200
    }
)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}")
