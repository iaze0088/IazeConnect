#!/usr/bin/env python3
"""
🧪 TESTE DE PERSISTÊNCIA - /vendas Modo de Operação

OBJETIVO: Testar se o modo de operação do /vendas está sendo salvo persistentemente no MongoDB.

BACKEND URL: https://suporte.help/api

CREDENCIAIS ADMIN:
- Login: biancaatt
- Password: ab181818ab

TESTES:
1. Login admin
2. Salvar mode="button" e verificar persistência
3. Verificar button_config
4. Salvar mode="ia" e verificar persistência
5. Verificar no MongoDB
6. Salvar mode="hybrid" e verificar persistência

CRITÉRIOS DE SUCESSO:
- Todos os 3 modos devem ser salvos corretamente
- GET deve retornar o mode salvo
- Mode deve persistir no MongoDB
- Nenhum mode deve reverter ao valor anterior
"""

import requests
import json
from pymongo import MongoClient
import os

# Configurações
BACKEND_URL = "https://suporte.help/api"
ADMIN_LOGIN = "biancaatt"
ADMIN_PASSWORD = "ab181818ab"

# MongoDB
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'support_chat')

def print_header(text):
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80)

def print_test(test_num, description):
    print(f"\n🧪 TESTE {test_num}: {description}")
    print("-" * 80)

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def print_info(message):
    print(f"ℹ️  {message}")

def test_admin_login():
    """TESTE 1: Login admin"""
    print_test(1, "ADMIN LOGIN")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/agent/login",
            json={
                "login": ADMIN_LOGIN,
                "password": ADMIN_PASSWORD
            },
            timeout=10
        )
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            
            if token:
                print_success(f"Login bem-sucedido!")
                print_info(f"Token: {token[:50]}...")
                return token
            else:
                print_error("Token não retornado")
                return None
        else:
            print_error(f"Login falhou: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Erro na requisição: {e}")
        return None

def test_save_mode(token, mode, empresa_nome="CyberTV"):
    """Salvar configuração com mode específico"""
    print_test(f"SAVE MODE", f"Salvando mode='{mode}'")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Payload mínimo conforme review request
        payload = {
            "empresa_nome": empresa_nome,
            "usa_ia": mode in ["ia", "hybrid"],
            "is_active": True,
            "mode": mode,
            "ia_config": {
                "name": "Juliana",
                "role": "Consultora de Vendas",
                "personality": "Profissional, amigável e prestativa",
                "instructions": "Você é Juliana, consultora especializada em IPTV.",
                "knowledge_base": {
                    "enabled": False,
                    "sources": [],
                    "fallback_text": ""
                },
                "llm_provider": "openai",
                "llm_model": "gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": 500,
                "top_p": 1.0,
                "api_key": "",
                "use_system_key": True,
                "auto_transfer_keywords": ["humano", "atendente", "pessoa"],
                "greeting_message": "Olá! Como posso ajudar você hoje?",
                "fallback_message": "Desculpe, não entendi.",
                "transfer_message": "Vou transferir você para um atendente.",
                "conversation_history_limit": 10,
                "remember_context": True
            }
        }
        
        print_info(f"POST /admin/vendas-bot/simple-config")
        print_info(f"Payload mode: {mode}")
        
        response = requests.post(
            f"{BACKEND_URL}/admin/vendas-bot/simple-config",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Configuração salva com sucesso!")
            print_info(f"Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print_error(f"Falha ao salvar: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Erro na requisição: {e}")
        return False

def test_get_simple_config(token, expected_mode):
    """TESTE: Verificar persistência via GET /admin/vendas-bot/simple-config"""
    print_test("GET SIMPLE CONFIG", f"Verificando se mode='{expected_mode}' foi salvo")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(
            f"{BACKEND_URL}/admin/vendas-bot/simple-config",
            headers=headers,
            timeout=10
        )
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            actual_mode = data.get("mode")
            
            print_info(f"Mode retornado: {actual_mode}")
            
            if actual_mode == expected_mode:
                print_success(f"✅ ESPERADO: mode='{expected_mode}'")
                print_success(f"✅ RECEBIDO: mode='{actual_mode}'")
                return True
            else:
                print_error(f"❌ ESPERADO: mode='{expected_mode}'")
                print_error(f"❌ RECEBIDO: mode='{actual_mode}'")
                return False
        else:
            print_error(f"Falha ao buscar config: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Erro na requisição: {e}")
        return False

def test_get_button_config(token, expected_mode):
    """TESTE: Verificar button_config via GET /admin/vendas-bot/buttons/config"""
    print_test("GET BUTTON CONFIG", f"Verificando se button_config.mode='{expected_mode}'")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(
            f"{BACKEND_URL}/admin/vendas-bot/buttons/config",
            headers=headers,
            timeout=10
        )
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            actual_mode = data.get("mode")
            
            print_info(f"Button config mode retornado: {actual_mode}")
            
            if actual_mode == expected_mode:
                print_success(f"✅ ESPERADO: mode='{expected_mode}'")
                print_success(f"✅ RECEBIDO: mode='{actual_mode}'")
                return True
            else:
                print_error(f"❌ ESPERADO: mode='{expected_mode}'")
                print_error(f"❌ RECEBIDO: mode='{actual_mode}'")
                return False
        else:
            print_error(f"Falha ao buscar button config: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Erro na requisição: {e}")
        return False

def test_mongodb_persistence(expected_mode):
    """TESTE: Verificar no MongoDB se mode foi salvo"""
    print_test("MONGODB PERSISTENCE", f"Verificando collection 'config' no MongoDB")
    
    try:
        client = MongoClient(MONGO_URL)
        db = client[DB_NAME]
        
        # Verificar collection config
        config_doc = db.config.find_one({"id": "config"})
        
        if config_doc:
            button_config = config_doc.get("button_config", {})
            actual_mode = button_config.get("mode")
            
            print_info(f"MongoDB config.button_config.mode: {actual_mode}")
            
            if actual_mode == expected_mode:
                print_success(f"✅ ESPERADO: mode='{expected_mode}'")
                print_success(f"✅ RECEBIDO: mode='{actual_mode}'")
                print_success(f"✅ Mode persistiu no MongoDB!")
                return True
            else:
                print_error(f"❌ ESPERADO: mode='{expected_mode}'")
                print_error(f"❌ RECEBIDO: mode='{actual_mode}'")
                return False
        else:
            print_error("❌ Documento config não encontrado no MongoDB")
            return False
            
    except Exception as e:
        print_error(f"Erro ao conectar no MongoDB: {e}")
        return False

def run_full_test():
    """Executar todos os testes"""
    print_header("🧪 TESTE DE PERSISTÊNCIA - /vendas Modo de Operação")
    
    results = {
        "login": False,
        "save_button": False,
        "get_button": False,
        "button_config_button": False,
        "mongodb_button": False,
        "save_ia": False,
        "get_ia": False,
        "button_config_ia": False,
        "mongodb_ia": False,
        "save_hybrid": False,
        "get_hybrid": False,
        "button_config_hybrid": False,
        "mongodb_hybrid": False
    }
    
    # TESTE 1: Login
    token = test_admin_login()
    if not token:
        print_error("❌ Login falhou. Abortando testes.")
        return results
    results["login"] = True
    
    # TESTE 2: Salvar mode="button"
    print_header("TESTE 2: SALVAR MODO 'button'")
    results["save_button"] = test_save_mode(token, "button")
    
    # TESTE 3: Verificar persistência via GET simple-config
    print_header("TESTE 3: VERIFICAR PERSISTÊNCIA (simple-config)")
    results["get_button"] = test_get_simple_config(token, "button")
    
    # TESTE 4: Verificar button_config
    print_header("TESTE 4: VERIFICAR BUTTON_CONFIG")
    results["button_config_button"] = test_get_button_config(token, "button")
    
    # TESTE 5: Verificar no MongoDB
    print_header("TESTE 5: VERIFICAR NO MONGODB")
    results["mongodb_button"] = test_mongodb_persistence("button")
    
    # TESTE 6: Salvar mode="ia"
    print_header("TESTE 6: SALVAR MODO 'ia'")
    results["save_ia"] = test_save_mode(token, "ia")
    
    # TESTE 7: Verificar persistência
    print_header("TESTE 7: VERIFICAR PERSISTÊNCIA (ia)")
    results["get_ia"] = test_get_simple_config(token, "ia")
    
    # TESTE 8: Verificar button_config
    print_header("TESTE 8: VERIFICAR BUTTON_CONFIG (ia)")
    results["button_config_ia"] = test_get_button_config(token, "ia")
    
    # TESTE 9: Verificar no MongoDB
    print_header("TESTE 9: VERIFICAR NO MONGODB (ia)")
    results["mongodb_ia"] = test_mongodb_persistence("ia")
    
    # TESTE 10: Salvar mode="hybrid"
    print_header("TESTE 10: SALVAR MODO 'hybrid'")
    results["save_hybrid"] = test_save_mode(token, "hybrid")
    
    # TESTE 11: Verificar persistência
    print_header("TESTE 11: VERIFICAR PERSISTÊNCIA (hybrid)")
    results["get_hybrid"] = test_get_simple_config(token, "hybrid")
    
    # TESTE 12: Verificar button_config
    print_header("TESTE 12: VERIFICAR BUTTON_CONFIG (hybrid)")
    results["button_config_hybrid"] = test_get_button_config(token, "hybrid")
    
    # TESTE 13: Verificar no MongoDB
    print_header("TESTE 13: VERIFICAR NO MONGODB (hybrid)")
    results["mongodb_hybrid"] = test_mongodb_persistence("hybrid")
    
    return results

def print_final_report(results):
    """Imprimir relatório final"""
    print_header("📊 RELATÓRIO FINAL")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    failed_tests = total_tests - passed_tests
    
    print(f"\n📈 ESTATÍSTICAS:")
    print(f"   Total de testes: {total_tests}")
    print(f"   ✅ Passaram: {passed_tests}")
    print(f"   ❌ Falharam: {failed_tests}")
    print(f"   📊 Taxa de sucesso: {(passed_tests/total_tests)*100:.1f}%")
    
    print(f"\n📋 DETALHAMENTO:")
    
    # Agrupar por modo
    print(f"\n🔐 LOGIN:")
    print(f"   {'✅' if results['login'] else '❌'} Admin login")
    
    print(f"\n🔘 MODO 'button':")
    print(f"   {'✅' if results['save_button'] else '❌'} Salvar configuração")
    print(f"   {'✅' if results['get_button'] else '❌'} GET simple-config")
    print(f"   {'✅' if results['button_config_button'] else '❌'} GET button-config")
    print(f"   {'✅' if results['mongodb_button'] else '❌'} Persistência MongoDB")
    
    print(f"\n🤖 MODO 'ia':")
    print(f"   {'✅' if results['save_ia'] else '❌'} Salvar configuração")
    print(f"   {'✅' if results['get_ia'] else '❌'} GET simple-config")
    print(f"   {'✅' if results['button_config_ia'] else '❌'} GET button-config")
    print(f"   {'✅' if results['mongodb_ia'] else '❌'} Persistência MongoDB")
    
    print(f"\n🔀 MODO 'hybrid':")
    print(f"   {'✅' if results['save_hybrid'] else '❌'} Salvar configuração")
    print(f"   {'✅' if results['get_hybrid'] else '❌'} GET simple-config")
    print(f"   {'✅' if results['button_config_hybrid'] else '❌'} GET button-config")
    print(f"   {'✅' if results['mongodb_hybrid'] else '❌'} Persistência MongoDB")
    
    # Verificar critérios de sucesso
    print(f"\n🎯 CRITÉRIOS DE SUCESSO:")
    
    all_modes_saved = (
        results['save_button'] and results['save_ia'] and results['save_hybrid']
    )
    print(f"   {'✅' if all_modes_saved else '❌'} Todos os 3 modos salvos corretamente")
    
    all_gets_working = (
        results['get_button'] and results['get_ia'] and results['get_hybrid']
    )
    print(f"   {'✅' if all_gets_working else '❌'} GET retorna o mode salvo")
    
    all_mongodb_persisted = (
        results['mongodb_button'] and results['mongodb_ia'] and results['mongodb_hybrid']
    )
    print(f"   {'✅' if all_mongodb_persisted else '❌'} Mode persiste no MongoDB")
    
    no_reversion = (
        results['get_button'] and results['get_ia'] and results['get_hybrid'] and
        results['mongodb_button'] and results['mongodb_ia'] and results['mongodb_hybrid']
    )
    print(f"   {'✅' if no_reversion else '❌'} Nenhum mode reverte ao valor anterior")
    
    # Conclusão final
    all_success = all_modes_saved and all_gets_working and all_mongodb_persisted and no_reversion
    
    print(f"\n{'='*80}")
    if all_success:
        print("🎉 TODOS OS CRITÉRIOS DE SUCESSO FORAM ATENDIDOS!")
        print("✅ PERSISTÊNCIA DO MODO DE OPERAÇÃO ESTÁ FUNCIONANDO 100%")
    else:
        print("❌ ALGUNS CRITÉRIOS DE SUCESSO NÃO FORAM ATENDIDOS")
        print("⚠️  PERSISTÊNCIA DO MODO DE OPERAÇÃO TEM PROBLEMAS")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    results = run_full_test()
    print_final_report(results)
