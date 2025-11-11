#!/usr/bin/env python3
"""
TESTE SIMPLES: Verificar conectividade e login admin
"""

import requests
import json
import os
import time

# Usar URL local para teste
BACKEND_URL = "http://localhost:8001"
ADMIN_PASSWORD = "102030@ab"

def test_health():
    """Testar health check"""
    try:
        print(f"🔍 Testando health check: {BACKEND_URL}/api/health")
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro no health check: {e}")
        return False

def test_admin_login():
    """Testar login admin"""
    try:
        print(f"\n🔐 Testando admin login: {BACKEND_URL}/api/auth/admin/login")
        response = requests.post(
            f"{BACKEND_URL}/api/auth/admin/login",
            json={"password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if "token" in data:
                print(f"✅ Login successful! Token: {data['token'][:50]}...")
                return True, data["token"]
            else:
                print(f"❌ No token in response: {data}")
                return False, None
        else:
            print(f"❌ Login failed with status {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ Erro no login: {e}")
        return False, None

def test_config_get(token):
    """Testar buscar config"""
    try:
        print(f"\n⚙️ Testando GET config: {BACKEND_URL}/api/config")
        response = requests.get(
            f"{BACKEND_URL}/api/config",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Config retrieved! Keys: {list(data.keys())[:10]}")
            return True
        else:
            print(f"❌ Config failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao buscar config: {e}")
        return False

def main():
    print("🚀 TESTE SIMPLES DO BACKEND")
    print("=" * 50)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Admin Password: {ADMIN_PASSWORD}")
    print("=" * 50)
    
    # Teste 1: Health check
    if not test_health():
        print("❌ Health check falhou - backend pode estar inacessível")
        return False
    
    # Teste 2: Admin login
    success, token = test_admin_login()
    if not success:
        print("❌ Admin login falhou")
        return False
    
    # Teste 3: Config get
    if not test_config_get(token):
        print("❌ Config get falhou")
        return False
    
    print("\n🎉 TODOS OS TESTES BÁSICOS PASSARAM!")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)