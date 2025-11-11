#!/usr/bin/env python3
"""
Teste do novo endpoint /api/vendas/config
"""
import requests
import json

def test_localhost():
    """Testar endpoint em localhost"""
    print("🧪 TESTE 1: LOCALHOST")
    print("="*60)
    
    try:
        response = requests.get("http://localhost:8001/api/vendas/config")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data.get('status')}")
            print(f"✅ Enabled: {data.get('is_enabled')}")
            print(f"✅ Botões: {len(data.get('buttons', []))}")
            
            for btn in data.get('buttons', []):
                print(f"   - {btn.get('label')}")
                if btn.get('sub_buttons'):
                    for sub in btn['sub_buttons']:
                        print(f"     └─ {sub.get('label')}")
            
            return True
        else:
            print(f"❌ Erro: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_production():
    """Testar endpoint em produção"""
    print("\n🧪 TESTE 2: PRODUÇÃO (suporte.help)")
    print("="*60)
    
    try:
        response = requests.get("https://suporte.help/api/vendas/config")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data.get('status')}")
            print(f"✅ Enabled: {data.get('is_enabled')}")
            print(f"✅ Botões: {len(data.get('buttons', []))}")
            
            for btn in data.get('buttons', []):
                print(f"   - {btn.get('label')}")
                if btn.get('sub_buttons'):
                    for sub in btn['sub_buttons']:
                        print(f"     └─ {sub.get('label')}")
            
            return True
        elif response.status_code == 404:
            print("⚠️ Endpoint não encontrado (404)")
            print("   Isso é normal se o código ainda não foi deployado")
            return None
        else:
            print(f"❌ Erro: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_frontend_flow():
    """Testar fluxo completo do frontend"""
    print("\n🧪 TESTE 3: FLUXO COMPLETO")
    print("="*60)
    
    try:
        # 1. Criar sessão
        print("1️⃣ Criando sessão...")
        start_response = requests.post(
            "http://localhost:8001/api/vendas/start",
            json={"name": "Teste", "whatsapp": "5511999999999"}
        )
        
        if start_response.status_code != 200:
            print(f"❌ Erro ao criar sessão: {start_response.text}")
            return False
        
        start_data = start_response.json()
        session_id = start_data.get('session_id')
        print(f"✅ Sessão criada: {session_id}")
        
        # 2. Buscar config
        print("2️⃣ Buscando configuração...")
        config_response = requests.get("http://localhost:8001/api/vendas/config")
        
        if config_response.status_code != 200:
            print(f"❌ Erro ao buscar config: {config_response.text}")
            return False
        
        config_data = config_response.json()
        print(f"✅ Config recebida:")
        print(f"   - Status: {config_data.get('status')}")
        print(f"   - Enabled: {config_data.get('is_enabled')}")
        print(f"   - Botões: {len(config_data.get('buttons', []))}")
        
        # 3. Verificar se frontend vai mostrar botões
        status = config_data.get('status')
        is_enabled = config_data.get('is_enabled')
        buttons = config_data.get('buttons', [])
        
        print("\n📊 ANÁLISE DO COMPORTAMENTO:")
        if is_enabled and len(buttons) > 0:
            if status == 1:
                print("✅ Modo BUTTON - Apenas botões (sem campo de input)")
            elif status == 2:
                print("✅ Modo IA - Apenas IA responde (sem botões visíveis)")
            elif status == 3:
                print("✅ Modo HYBRID - Botões E campo de input")
            else:
                print(f"⚠️ Status desconhecido: {status}")
        else:
            print("⚠️ Botões desabilitados ou não configurados")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TESTE DO NOVO ENDPOINT /api/vendas/config\n")
    
    # Testes
    localhost_ok = test_localhost()
    production_ok = test_production()
    flow_ok = test_frontend_flow()
    
    # Resumo
    print("\n" + "="*60)
    print("📋 RESUMO DOS TESTES:")
    print("="*60)
    print(f"Localhost:  {'✅ OK' if localhost_ok else '❌ FALHOU'}")
    print(f"Produção:   {'✅ OK' if production_ok else '⚠️ PENDENTE (deploy necessário)' if production_ok is None else '❌ FALHOU'}")
    print(f"Fluxo:      {'✅ OK' if flow_ok else '❌ FALHOU'}")
    
    if localhost_ok and flow_ok:
        print("\n🎉 SOLUÇÃO FUNCIONANDO EM LOCALHOST!")
        print("📦 Aguardando deploy para testar em produção (suporte.help)")
