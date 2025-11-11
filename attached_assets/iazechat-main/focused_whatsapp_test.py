#!/usr/bin/env python3
"""
TESTE FOCADO: Endpoint WhatsApp Send Message
Problema: "Erro ao enviar mensagem" no painel do atendente
"""

import requests
import json
import os

# Configurações
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://wppconnect-fix.preview.emergentagent.com')

def test_whatsapp_send_message():
    print("🚀 TESTE FOCADO: Endpoint WhatsApp Send Message")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    
    # 1. Login como agente
    print("\n1️⃣ Fazendo login como agente...")
    login_response = requests.post(
        f"{BACKEND_URL}/api/auth/agent/login",
        json={"login": "fabio123", "password": "fabio123"},
        timeout=30
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login falhou: {login_response.status_code} - {login_response.text}")
        return False
    
    token = login_response.json().get("token")
    print(f"✅ Login bem-sucedido! Token: {token[:30]}...")
    
    # 2. Testar endpoint de envio
    print("\n2️⃣ Testando endpoint de envio de mensagem...")
    
    test_data = {
        "instance_name": "nome-da-instancia",
        "number": "5551993513841",
        "text": "Teste de mensagem"
    }
    
    print(f"📋 Dados: {json.dumps(test_data, indent=2)}")
    
    send_response = requests.post(
        f"{BACKEND_URL}/api/whatsapp/send-message",
        json=test_data,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30
    )
    
    print(f"\n📊 Status: {send_response.status_code}")
    print(f"📄 Response: {send_response.text}")
    
    if send_response.status_code == 500:
        print("❌ ERRO 500 - Problema no servidor")
        return False
    elif send_response.status_code == 200:
        response_data = send_response.json()
        success = response_data.get("success", False)
        if success:
            print("✅ Mensagem enviada com sucesso!")
            return True
        else:
            error = response_data.get("error", "Erro desconhecido")
            print(f"❌ Erro na API: {error}")
            return False
    else:
        print(f"❌ Status inesperado: {send_response.status_code}")
        return False

if __name__ == "__main__":
    success = test_whatsapp_send_message()
    exit(0 if success else 1)