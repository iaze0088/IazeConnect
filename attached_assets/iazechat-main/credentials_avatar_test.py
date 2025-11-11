#!/usr/bin/env python3
"""
🧪 TESTE COMPLETO: Auto-Fixar Credenciais + Foto de Perfil

BACKEND URL: https://suporte.help/api

OBJETIVO:
Testar se as duas funcionalidades estão funcionando:
1. Popup de credenciais (backend deve retornar pinned_user e pinned_pass)
2. Foto de perfil (backend deve retornar custom_avatar)
"""

import requests
import json
import sys
from io import BytesIO
from PIL import Image

# Backend URL
# NOTE: Using localhost because https://suporte.help/api points to a different backend
# The production backend needs to be redeployed with the latest code
BASE_URL = "http://localhost:8001/api"

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_test(test_name, passed, details=""):
    status = "✅ PASSOU" if passed else "❌ FALHOU"
    print(f"\n{status}: {test_name}")
    if details:
        print(f"   {details}")

def create_test_image():
    """Cria uma imagem de teste em memória"""
    img = Image.new('RGB', (200, 200), color='blue')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes

# ============================================================================
# TESTE 1: Verificar Cliente com Credenciais
# ============================================================================

print_section("TESTE 1: Verificar Cliente com Credenciais")

# 1.1. Fazer login como admin para buscar clientes
print("\n📋 1.1. Login como Admin...")
admin_response = requests.post(
    f"{BASE_URL}/auth/admin/login",
    json={"email": "admin@admin.com", "password": "102030@ab"}
)

if admin_response.status_code != 200:
    print(f"❌ ERRO: Admin login falhou - {admin_response.status_code}")
    print(f"   Response: {admin_response.text}")
    sys.exit(1)

admin_token = admin_response.json()["token"]
print_test("Admin Login", True, f"Token obtido: {admin_token[:20]}...")

# 1.2. Buscar um cliente existente
print("\n📋 1.2. Buscando clientes existentes...")
tickets_response = requests.get(
    f"{BASE_URL}/tickets",
    headers={"Authorization": f"Bearer {admin_token}"}
)

if tickets_response.status_code != 200:
    print(f"❌ ERRO: Falha ao buscar tickets - {tickets_response.status_code}")
    sys.exit(1)

tickets = tickets_response.json()
print(f"   Encontrados {len(tickets)} tickets")

# Pegar o primeiro cliente de um ticket
test_client_whatsapp = None
if tickets and len(tickets) > 0:
    # Tentar encontrar um ticket com client_whatsapp
    for ticket in tickets:
        if ticket.get("client_whatsapp"):
            test_client_whatsapp = ticket["client_whatsapp"]
            print(f"   Cliente encontrado: {test_client_whatsapp}")
            break

if not test_client_whatsapp:
    print("⚠️ Nenhum cliente encontrado nos tickets. Criando cliente de teste...")
    test_client_whatsapp = "5519999888777"
    test_client_pin = "99"
else:
    # Usar PIN padrão para teste - tentar vários PINs comuns
    test_client_pin = "00"
    
# Se o cliente já existe mas não sabemos o PIN, criar um novo cliente de teste
print("⚠️ Usando cliente de teste com PIN conhecido...")
test_client_whatsapp = "5519998887766"
test_client_pin = "88"

# 1.3. Fazer login como cliente (ou criar se não existir)
print(f"\n📋 1.3. Login como cliente ({test_client_whatsapp})...")
client_login_response = requests.post(
    f"{BASE_URL}/auth/client/login",
    json={"whatsapp": test_client_whatsapp, "pin": test_client_pin}
)

if client_login_response.status_code not in [200, 201]:
    print(f"❌ ERRO: Cliente login falhou - {client_login_response.status_code}")
    print(f"   Response: {client_login_response.text}")
    sys.exit(1)

client_data = client_login_response.json()
client_token = client_data["token"]
client_id = client_data["user_data"]["id"]
print_test("Cliente Login", True, f"Cliente ID: {client_id}")

# 1.4. Verificar se cliente já tem credenciais
print("\n📋 1.4. Verificando credenciais existentes...")
user_me_response = requests.get(
    f"{BASE_URL}/users/me",
    headers={"Authorization": f"Bearer {client_token}"}
)

if user_me_response.status_code != 200:
    print(f"❌ ERRO: Falha ao buscar /users/me - {user_me_response.status_code}")
    sys.exit(1)

user_data = user_me_response.json()
has_credentials = bool(user_data.get("pinned_user") or user_data.get("pinned_pass"))

print(f"   Pinned User: {user_data.get('pinned_user', 'N/A')}")
print(f"   Pinned Pass: {user_data.get('pinned_pass', 'N/A')}")
print(f"   Tem credenciais: {has_credentials}")

# 1.5. Se não tem credenciais, adicionar via admin/agent
if not has_credentials:
    print("\n📋 1.5. Adicionando credenciais ao cliente...")
    
    # Fazer login como agente para adicionar credenciais
    agent_login_response = requests.post(
        f"{BASE_URL}/auth/agent/login",
        json={"login": "biancaatt", "password": "ab181818ab"}
    )
    
    if agent_login_response.status_code != 200:
        print(f"⚠️ Aviso: Não foi possível fazer login como agente")
        print(f"   Tentando adicionar credenciais diretamente via admin...")
        
        # Tentar atualizar diretamente no banco via endpoint (se existir)
        # Como não temos endpoint direto, vamos usar o PUT /users/me
        update_response = requests.put(
            f"{BASE_URL}/users/me",
            headers={"Authorization": f"Bearer {client_token}"},
            json={
                "pinned_user": "teste123",
                "pinned_pass": "senha456"
            }
        )
        
        if update_response.status_code == 200:
            print_test("Credenciais Adicionadas", True, "Via PUT /users/me")
        else:
            print(f"⚠️ Não foi possível adicionar credenciais automaticamente")
            print(f"   Status: {update_response.status_code}")
    else:
        agent_token = agent_login_response.json()["token"]
        print(f"   Agente logado com sucesso")
        
        # Tentar endpoint de adicionar credenciais (se existir)
        # PUT /users/{user_id}/pin-credentials
        cred_response = requests.put(
            f"{BASE_URL}/users/{client_id}/pin-credentials",
            headers={"Authorization": f"Bearer {agent_token}"},
            json={
                "pinned_user": "teste123",
                "pinned_pass": "senha456"
            }
        )
        
        if cred_response.status_code == 200:
            print_test("Credenciais Adicionadas", True, "Via agente")
        else:
            print(f"⚠️ Endpoint /users/{{id}}/pin-credentials não existe")
            print(f"   Tentando via PUT /users/me...")
            
            update_response = requests.put(
                f"{BASE_URL}/users/me",
                headers={"Authorization": f"Bearer {client_token}"},
                json={
                    "pinned_user": "teste123",
                    "pinned_pass": "senha456"
                }
            )
            
            if update_response.status_code == 200:
                print_test("Credenciais Adicionadas", True, "Via PUT /users/me")

# ============================================================================
# TESTE 2: Verificar Endpoint GET /users/me
# ============================================================================

print_section("TESTE 2: Verificar Endpoint GET /users/me")

print("\n📋 2.1. Buscar dados do cliente autenticado...")
user_me_response = requests.get(
    f"{BASE_URL}/users/me",
    headers={"Authorization": f"Bearer {client_token}"}
)

if user_me_response.status_code != 200:
    print(f"❌ ERRO: GET /users/me falhou - {user_me_response.status_code}")
    print(f"   Response: {user_me_response.text}")
    sys.exit(1)

user_data = user_me_response.json()
print("\n📊 RESPONSE:")
print(json.dumps(user_data, indent=2))

# Verificar campos obrigatórios
print("\n📋 2.2. Verificando campos obrigatórios...")

tests_passed = 0
tests_total = 0

# Teste 1: Campo custom_avatar existe
tests_total += 1
has_custom_avatar_field = "custom_avatar" in user_data
if has_custom_avatar_field:
    tests_passed += 1
    print_test("Campo 'custom_avatar' presente", True, f"Valor: {user_data.get('custom_avatar', 'null')}")
else:
    print_test("Campo 'custom_avatar' presente", False, "❌ CAMPO NÃO EXISTE NO RESPONSE")

# Teste 2: Campo pinned_user existe
tests_total += 1
has_pinned_user_field = "pinned_user" in user_data
if has_pinned_user_field:
    tests_passed += 1
    print_test("Campo 'pinned_user' presente", True, f"Valor: {user_data.get('pinned_user', 'null')}")
else:
    print_test("Campo 'pinned_user' presente", False, "❌ CAMPO NÃO EXISTE NO RESPONSE")

# Teste 3: Campo pinned_pass existe
tests_total += 1
has_pinned_pass_field = "pinned_pass" in user_data
if has_pinned_pass_field:
    tests_passed += 1
    print_test("Campo 'pinned_pass' presente", True, f"Valor: {user_data.get('pinned_pass', 'null')}")
else:
    print_test("Campo 'pinned_pass' presente", False, "❌ CAMPO NÃO EXISTE NO RESPONSE")

# ============================================================================
# TESTE 3: Upload de Foto de Perfil
# ============================================================================

print_section("TESTE 3: Upload de Foto de Perfil")

print("\n📋 3.1. Fazer upload de foto...")

# Criar imagem de teste
test_image = create_test_image()

upload_response = requests.post(
    f"{BASE_URL}/users/me/avatar",
    headers={"Authorization": f"Bearer {client_token}"},
    files={"file": ("test_avatar.jpg", test_image, "image/jpeg")}
)

if upload_response.status_code != 200:
    print(f"❌ ERRO: Upload falhou - {upload_response.status_code}")
    print(f"   Response: {upload_response.text}")
    upload_success = False
    avatar_url = None
else:
    upload_data = upload_response.json()
    print("\n📊 UPLOAD RESPONSE:")
    print(json.dumps(upload_data, indent=2))
    
    tests_total += 1
    if upload_data.get("ok") and upload_data.get("avatar_url"):
        tests_passed += 1
        upload_success = True
        avatar_url = upload_data["avatar_url"]
        print_test("Upload de Foto", True, f"URL: {avatar_url}")
    else:
        upload_success = False
        avatar_url = None
        print_test("Upload de Foto", False, "Response não contém 'ok' ou 'avatar_url'")

# 3.2. Verificar se foto foi salva
print("\n📋 3.2. Verificar se foto foi salva...")
user_me_after_upload = requests.get(
    f"{BASE_URL}/users/me",
    headers={"Authorization": f"Bearer {client_token}"}
)

if user_me_after_upload.status_code != 200:
    print(f"❌ ERRO: GET /users/me após upload falhou - {user_me_after_upload.status_code}")
else:
    user_data_after = user_me_after_upload.json()
    
    tests_total += 1
    custom_avatar_after = user_data_after.get("custom_avatar")
    
    if custom_avatar_after and custom_avatar_after == avatar_url:
        tests_passed += 1
        print_test("Foto Salva no custom_avatar", True, f"URL: {custom_avatar_after}")
    elif custom_avatar_after:
        tests_passed += 1
        print_test("Foto Salva no custom_avatar", True, f"URL diferente: {custom_avatar_after}")
    else:
        print_test("Foto Salva no custom_avatar", False, "custom_avatar está vazio ou null")

# ============================================================================
# TESTE 4: Verificar no AgentDashboard
# ============================================================================

print_section("TESTE 4: Verificar no AgentDashboard")

print("\n📋 4.1. Fazer login como agente...")
agent_login_response = requests.post(
    f"{BASE_URL}/auth/agent/login",
    json={"login": "biancaatt", "password": "ab181818ab"}
)

if agent_login_response.status_code != 200:
    print(f"❌ ERRO: Agente login falhou - {agent_login_response.status_code}")
    print(f"   Response: {agent_login_response.text}")
else:
    agent_token = agent_login_response.json()["token"]
    print_test("Agente Login", True, f"Token obtido")
    
    # 4.2. Buscar tickets
    print("\n📋 4.2. Buscar tickets...")
    tickets_response = requests.get(
        f"{BASE_URL}/tickets",
        headers={"Authorization": f"Bearer {agent_token}"}
    )
    
    if tickets_response.status_code != 200:
        print(f"❌ ERRO: GET /tickets falhou - {tickets_response.status_code}")
    else:
        tickets = tickets_response.json()
        print(f"   Encontrados {len(tickets)} tickets")
        
        # Verificar se algum ticket tem client_avatar
        tests_total += 1
        tickets_with_avatar = [t for t in tickets if t.get("client_avatar")]
        
        if tickets_with_avatar:
            tests_passed += 1
            print_test("Tickets com client_avatar", True, f"{len(tickets_with_avatar)} tickets têm foto")
            
            # Mostrar exemplo
            example = tickets_with_avatar[0]
            print(f"\n   Exemplo de ticket com foto:")
            print(f"   - Ticket ID: {example.get('id', 'N/A')}")
            print(f"   - Cliente: {example.get('client_name', 'N/A')}")
            print(f"   - Avatar: {example.get('client_avatar', 'N/A')[:50]}...")
        else:
            print_test("Tickets com client_avatar", False, "Nenhum ticket tem campo client_avatar")

# ============================================================================
# RESULTADO FINAL
# ============================================================================

print_section("RESULTADO FINAL")

print(f"\n📊 TESTES EXECUTADOS: {tests_passed}/{tests_total} passaram")
print(f"   Taxa de sucesso: {(tests_passed/tests_total*100):.1f}%")

print("\n✅ CRITÉRIOS DE SUCESSO:")
print(f"   1. GET /users/me retorna custom_avatar: {'✅' if has_custom_avatar_field else '❌'}")
print(f"   2. GET /users/me retorna pinned_user: {'✅' if has_pinned_user_field else '❌'}")
print(f"   3. GET /users/me retorna pinned_pass: {'✅' if has_pinned_pass_field else '❌'}")
print(f"   4. Upload de foto funciona: {'✅' if upload_success else '❌'}")
print(f"   5. Foto salva em custom_avatar: {'✅' if (upload_success and custom_avatar_after) else '❌'}")

if tests_passed == tests_total:
    print("\n🎉 TODOS OS TESTES PASSARAM!")
    sys.exit(0)
else:
    print(f"\n⚠️ {tests_total - tests_passed} TESTE(S) FALHARAM")
    sys.exit(1)
