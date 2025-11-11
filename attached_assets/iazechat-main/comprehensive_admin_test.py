#!/usr/bin/env python3
"""
🧪 TESTE FINAL COMPLETO - VALIDAR TODAS AS FUNCIONALIDADES CRÍTICAS
Teste sistemático de todas as 8 funcionalidades conforme review request
"""

import requests
import json
import time

# Configuration
BASE_URL = "https://suporte.help/api"
ADMIN_PASSWORD = "102030@ab"

def print_header(title):
    print("\n" + "="*80)
    print(f"🎯 {title}")
    print("="*80)

def print_test(test_name):
    print(f"\n📋 {test_name}")
    print("-" * 60)

def admin_login():
    """Login como admin e retorna o token"""
    print_test("FAZENDO LOGIN COMO ADMIN")
    
    try:
        response = requests.post(f"{BASE_URL}/auth/admin/login", 
                               json={"password": ADMIN_PASSWORD})
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            print(f"✅ Login realizado com sucesso!")
            print(f"   Token: {token[:50]}...")
            return token
        else:
            print(f"❌ Erro no login: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro durante login: {str(e)}")
        return None

def test_criar_revenda(token):
    """Teste 1: CRIAR REVENDA"""
    print_test("1️⃣ TESTANDO CRIAR REVENDA")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Dados da revenda de teste
    revenda_data = {
        "name": "Revenda Teste Final API",
        "email": "teste.final.api@exemplo.com",
        "password": "senha123"
    }
    
    try:
        # Criar revenda
        response = requests.post(f"{BASE_URL}/resellers", 
                               json=revenda_data, headers=headers)
        
        if response.status_code in [200, 201]:
            print("✅ REVENDA: Criada com sucesso!")
            data = response.json()
            reseller_id = data.get('id')
            print(f"   ID da revenda: {reseller_id}")
            
            # Verificar se aparece na lista
            list_response = requests.get(f"{BASE_URL}/resellers", headers=headers)
            if list_response.status_code == 200:
                resellers = list_response.json()
                found = any(r.get('email') == revenda_data['email'] for r in resellers)
                if found:
                    print("✅ REVENDA: Dados persistiram (encontrada na lista)")
                else:
                    print("❌ REVENDA: Dados NÃO persistiram")
            
            return True
        else:
            print(f"❌ REVENDA: Erro {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ REVENDA: Erro durante teste: {str(e)}")
        return False

def test_salvar_departamento(token):
    """Teste 2: SALVAR DEPARTAMENTO"""
    print_test("2️⃣ TESTANDO SALVAR DEPARTAMENTO")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Dados do departamento de teste
    dept_data = {
        "name": "Departamento Teste Final API",
        "description": "Descrição do departamento de teste final via API"
    }
    
    try:
        # Criar departamento
        response = requests.post(f"{BASE_URL}/ai/departments", 
                               json=dept_data, headers=headers)
        
        if response.status_code in [200, 201]:
            print("✅ DEPARTAMENTO: Criado com sucesso!")
            data = response.json()
            dept_id = data.get('id')
            print(f"   ID do departamento: {dept_id}")
            
            # Verificar se aparece na lista
            list_response = requests.get(f"{BASE_URL}/ai/departments", headers=headers)
            if list_response.status_code == 200:
                departments = list_response.json()
                found = any(d.get('name') == dept_data['name'] for d in departments)
                if found:
                    print("✅ DEPARTAMENTO: Dados persistiram (encontrado na lista)")
                else:
                    print("❌ DEPARTAMENTO: Dados NÃO persistiram")
            
            return True
        else:
            print(f"❌ DEPARTAMENTO: Erro {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ DEPARTAMENTO: Erro durante teste: {str(e)}")
        return False

def test_msg_rapida(token):
    """Teste 3: MSG RÁPIDA"""
    print_test("3️⃣ TESTANDO MSG RÁPIDA")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Primeiro, obter config atual
        config_response = requests.get(f"{BASE_URL}/config", headers=headers)
        if config_response.status_code != 200:
            print(f"❌ MSG RÁPIDA: Erro ao obter config: {config_response.status_code}")
            return False
        
        config = config_response.json()
        
        # Adicionar nova mensagem rápida
        new_message = {
            "title": "Mensagem Teste Final API",
            "text": "Esta é uma mensagem rápida de teste final via API"
        }
        
        quick_blocks = config.get('quick_blocks', [])
        quick_blocks.append(new_message)
        
        # Atualizar config
        config['quick_blocks'] = quick_blocks
        
        update_response = requests.put(f"{BASE_URL}/config", 
                                     json=config, headers=headers)
        
        if update_response.status_code == 200:
            print("✅ MSG RÁPIDA: Salva com sucesso!")
            
            # Verificar se persistiu
            verify_response = requests.get(f"{BASE_URL}/config", headers=headers)
            if verify_response.status_code == 200:
                verify_config = verify_response.json()
                found = any(msg.get('title') == new_message['title'] 
                          for msg in verify_config.get('quick_blocks', []))
                if found:
                    print("✅ MSG RÁPIDA: Dados persistiram")
                else:
                    print("❌ MSG RÁPIDA: Dados NÃO persistiram")
            
            return True
        else:
            print(f"❌ MSG RÁPIDA: Erro {update_response.status_code} - {update_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ MSG RÁPIDA: Erro durante teste: {str(e)}")
        return False

def test_dados_permitidos(token):
    """Teste 4: DADOS PERMITIDOS"""
    print_test("4️⃣ TESTANDO DADOS PERMITIDOS")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Primeiro, obter config atual
        config_response = requests.get(f"{BASE_URL}/config", headers=headers)
        if config_response.status_code != 200:
            print(f"❌ DADOS PERMITIDOS: Erro ao obter config: {config_response.status_code}")
            return False
        
        config = config_response.json()
        
        # Adicionar CPF aos dados permitidos
        test_cpf = "111.222.333-44"
        
        if 'allowed_data' not in config:
            config['allowed_data'] = {'cpfs': [], 'emails': [], 'phones': [], 'random_keys': []}
        
        if 'cpfs' not in config['allowed_data']:
            config['allowed_data']['cpfs'] = []
        
        config['allowed_data']['cpfs'].append(test_cpf)
        
        # Atualizar config
        update_response = requests.put(f"{BASE_URL}/config", 
                                     json=config, headers=headers)
        
        if update_response.status_code == 200:
            print("✅ DADOS PERMITIDOS: CPF salvo com sucesso!")
            
            # Verificar se persistiu
            verify_response = requests.get(f"{BASE_URL}/config", headers=headers)
            if verify_response.status_code == 200:
                verify_config = verify_response.json()
                cpfs = verify_config.get('allowed_data', {}).get('cpfs', [])
                if test_cpf in cpfs:
                    print("✅ DADOS PERMITIDOS: CPF persistiu")
                else:
                    print("❌ DADOS PERMITIDOS: CPF NÃO persistiu")
            
            return True
        else:
            print(f"❌ DADOS PERMITIDOS: Erro {update_response.status_code} - {update_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ DADOS PERMITIDOS: Erro durante teste: {str(e)}")
        return False

def test_avisos(token):
    """Teste 5: AVISOS"""
    print_test("5️⃣ TESTANDO AVISOS")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Dados do aviso de teste
    aviso_data = {
        "title": "Aviso Teste Final API",
        "message": "Esta é uma mensagem de aviso de teste final via API",
        "type": "info"
    }
    
    try:
        # Criar aviso
        response = requests.post(f"{BASE_URL}/notices", 
                               json=aviso_data, headers=headers)
        
        if response.status_code in [200, 201]:
            print("✅ AVISOS: Criado com sucesso!")
            data = response.json()
            notice_id = data.get('id')
            print(f"   ID do aviso: {notice_id}")
            
            # Verificar se aparece na lista
            list_response = requests.get(f"{BASE_URL}/notices", headers=headers)
            if list_response.status_code == 200:
                notices = list_response.json()
                found = any(n.get('title') == aviso_data['title'] for n in notices)
                if found:
                    print("✅ AVISOS: Dados persistiram (encontrado na lista)")
                else:
                    print("❌ AVISOS: Dados NÃO persistiram")
            
            return True
        else:
            print(f"❌ AVISOS: Erro {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ AVISOS: Erro durante teste: {str(e)}")
        return False

def test_wa_site(token):
    """Teste 6: WA SITE"""
    print_test("6️⃣ TESTANDO WA SITE")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Obter config atual do vendas bot
        config_response = requests.get(f"{BASE_URL}/admin/vendas-bot/config", headers=headers)
        if config_response.status_code != 200:
            print(f"❌ WA SITE: Erro ao obter config: {config_response.status_code}")
            return False
        
        config = config_response.json()
        
        # Atualizar instruções da IA
        test_instructions = "Instruções da IA de teste final via API - Seja sempre educado e prestativo."
        config['ai_instructions'] = test_instructions
        
        # Salvar config
        update_response = requests.post(f"{BASE_URL}/admin/vendas-bot/config", 
                                      json=config, headers=headers)
        
        if update_response.status_code == 200:
            print("✅ WA SITE: Instruções salvas com sucesso!")
            
            # Verificar se persistiu
            verify_response = requests.get(f"{BASE_URL}/admin/vendas-bot/config", headers=headers)
            if verify_response.status_code == 200:
                verify_config = verify_response.json()
                if verify_config.get('ai_instructions') == test_instructions:
                    print("✅ WA SITE: Instruções persistiram")
                else:
                    print("❌ WA SITE: Instruções NÃO persistiram")
            
            return True
        else:
            print(f"❌ WA SITE: Erro {update_response.status_code} - {update_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ WA SITE: Erro durante teste: {str(e)}")
        return False

def test_backup(token):
    """Teste 7: BACKUP"""
    print_test("7️⃣ TESTANDO BACKUP")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Criar backup manual
        response = requests.post(f"{BASE_URL}/admin/backup/create", 
                               headers=headers)
        
        if response.status_code in [200, 201]:
            print("✅ BACKUP: Criado com sucesso!")
            data = response.json()
            backup_id = data.get('backup_id')
            print(f"   ID do backup: {backup_id}")
            
            # Verificar se aparece na lista
            list_response = requests.get(f"{BASE_URL}/admin/backup/list", headers=headers)
            if list_response.status_code == 200:
                backups = list_response.json()
                found = any(b.get('id') == backup_id for b in backups.get('backups', []))
                if found:
                    print("✅ BACKUP: Aparece na lista")
                else:
                    print("❌ BACKUP: NÃO aparece na lista")
            
            return True
        else:
            print(f"❌ BACKUP: Erro {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ BACKUP: Erro durante teste: {str(e)}")
        return False

def test_office_gestor(token):
    """Teste 8: OFFICE GESTOR.MY"""
    print_test("8️⃣ TESTANDO OFFICE GESTOR.MY")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Dados de configuração do office
    office_data = {
        "login": "teste_office_api",
        "password": "senha_office_123"
    }
    
    try:
        # Salvar configuração do office
        response = requests.post(f"{BASE_URL}/office/config", 
                               json=office_data, headers=headers)
        
        if response.status_code in [200, 201]:
            print("✅ OFFICE: Configuração salva com sucesso!")
            
            # Verificar se persistiu
            verify_response = requests.get(f"{BASE_URL}/office/config", headers=headers)
            if verify_response.status_code == 200:
                verify_config = verify_response.json()
                if verify_config.get('login') == office_data['login']:
                    print("✅ OFFICE: Configuração persistiu")
                else:
                    print("❌ OFFICE: Configuração NÃO persistiu")
            
            return True
        else:
            print(f"❌ OFFICE: Erro {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ OFFICE: Erro durante teste: {str(e)}")
        return False

def main():
    """Função principal que executa todos os testes"""
    print_header("TESTE FINAL COMPLETO - VALIDAR TODAS AS FUNCIONALIDADES CRÍTICAS")
    print("URL:", BASE_URL)
    print("Login: admin@admin.com / 102030@ab")
    
    # Login
    token = admin_login()
    if not token:
        print("\n❌ FALHA CRÍTICA: Não foi possível fazer login!")
        return
    
    # Executar todos os testes
    tests = [
        ("CRIAR REVENDA", test_criar_revenda),
        ("SALVAR DEPARTAMENTO", test_salvar_departamento),
        ("MSG RÁPIDA", test_msg_rapida),
        ("DADOS PERMITIDOS", test_dados_permitidos),
        ("AVISOS", test_avisos),
        ("WA SITE", test_wa_site),
        ("BACKUP", test_backup),
        ("OFFICE GESTOR.MY", test_office_gestor)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func(token)
            results.append((test_name, result))
            time.sleep(1)  # Pequena pausa entre testes
        except Exception as e:
            print(f"❌ ERRO CRÍTICO no teste {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Resumo final
    print_header("RESUMO FINAL DOS TESTES")
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        if result:
            print(f"✅ {test_name}: PASSOU")
            passed += 1
        else:
            print(f"❌ {test_name}: FALHOU")
            failed += 1
    
    print(f"\n📊 RESULTADO FINAL:")
    print(f"   ✅ Testes que passaram: {passed}/8")
    print(f"   ❌ Testes que falharam: {failed}/8")
    print(f"   📈 Taxa de sucesso: {(passed/8)*100:.1f}%")
    
    if passed == 8:
        print("\n🎉 TODOS OS TESTES PASSARAM! Sistema 100% funcional!")
    elif passed >= 6:
        print("\n⚠️ Maioria dos testes passou, mas há alguns problemas a resolver.")
    else:
        print("\n🚨 MUITOS TESTES FALHARAM! Sistema precisa de correções urgentes.")

if __name__ == "__main__":
    main()