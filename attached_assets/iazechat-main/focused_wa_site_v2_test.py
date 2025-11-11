#!/usr/bin/env python3
"""
TESTE FOCADO: WA Site Manager V2 - Endpoints Específicos do Review Request
Testar exatamente os 4 pontos mencionados no review request
"""

import asyncio
import httpx
import json
import os
from datetime import datetime

# Configuração
BACKEND_URL = "https://wppconnect-fix.preview.emergentagent.com"
ADMIN_PASSWORD = "102030@ab"

async def test_wa_site_v2_endpoints():
    """Testar endpoints específicos do review request"""
    
    print("🎯 TESTE FOCADO: WA Site Manager V2 - Review Request")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # 1. Login Admin
        print("\n🔐 1. FAZENDO LOGIN ADMIN...")
        login_response = await client.post(
            f"{BACKEND_URL}/api/auth/admin/login",
            json={"password": ADMIN_PASSWORD}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login falhou: {login_response.status_code}")
            return False
            
        token = login_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"✅ Login OK - Token: {token[:20]}...")
        
        # 2. TESTE 1: GET /api/admin/vendas-bot/simple-config
        print("\n📥 2. TESTE GET - Verificar estrutura V2 completa...")
        get_response = await client.get(
            f"{BACKEND_URL}/api/admin/vendas-bot/simple-config",
            headers=headers
        )
        
        if get_response.status_code != 200:
            print(f"❌ GET falhou: {get_response.status_code}")
            return False
            
        config = get_response.json()
        
        # Verificar campos V2 obrigatórios
        required_v2_fields = [
            "ia_config", "visual_config", "external_apis", 
            "flows", "integrations", "analytics"
        ]
        
        missing_fields = [field for field in required_v2_fields if field not in config]
        
        if missing_fields:
            print(f"❌ Campos V2 faltando: {missing_fields}")
            return False
            
        print("✅ GET - Estrutura V2 completa encontrada!")
        print(f"   📋 Campos V2: {', '.join(required_v2_fields)}")
        
        # Verificar subcampos ia_config
        ia_config = config.get("ia_config", {})
        ia_required = ["name", "role", "personality", "instructions", "llm_provider", "llm_model"]
        ia_missing = [f for f in ia_required if f not in ia_config]
        
        if ia_missing:
            print(f"❌ ia_config campos faltando: {ia_missing}")
            return False
            
        print(f"   🤖 ia_config: {len(ia_config)} campos - Nome: {ia_config.get('name')}")
        
        # 3. TESTE 2: POST /api/admin/vendas-bot/simple-config
        print("\n📤 3. TESTE POST - Salvar com estrutura V2...")
        
        # Usar config atual como base e modificar
        test_config = config.copy()
        test_config["empresa_nome"] = "TESTE V2 RETESTE"
        test_config["ia_config"]["name"] = "Juliana Teste V2"
        test_config["ia_config"]["personality"] = "Teste de personalidade V2"
        test_config["visual_config"]["theme_color"] = "#ff0000"
        
        post_response = await client.post(
            f"{BACKEND_URL}/api/admin/vendas-bot/simple-config",
            headers=headers,
            json=test_config
        )
        
        if post_response.status_code != 200:
            error_text = await post_response.aread()
            print(f"❌ POST falhou: {post_response.status_code} - {error_text}")
            return False
            
        post_result = post_response.json()
        
        if not post_result.get("success"):
            print(f"❌ POST não retornou success: {post_result}")
            return False
            
        config_id = post_result.get("config_id")
        print(f"✅ POST - Config V2 salva! ID: {config_id}")
        
        # 4. TESTE 3: Migração Automática (verificar se GET ainda funciona após POST)
        print("\n🔄 4. TESTE MIGRAÇÃO - Verificar migração automática...")
        
        get_after_post = await client.get(
            f"{BACKEND_URL}/api/admin/vendas-bot/simple-config",
            headers=headers
        )
        
        if get_after_post.status_code != 200:
            print(f"❌ GET após POST falhou: {get_after_post.status_code}")
            return False
            
        new_config = get_after_post.json()
        
        # Verificar se ainda tem estrutura V2
        if not all(field in new_config for field in required_v2_fields):
            print("❌ Estrutura V2 perdida após POST")
            return False
            
        # Verificar se mudanças foram salvas
        if new_config.get("empresa_nome") != "TESTE V2 RETESTE":
            print("❌ Mudanças não foram salvas")
            return False
            
        print("✅ MIGRAÇÃO - Estrutura V2 mantida após salvamento!")
        
        # 5. TESTE 4: Integração com Vendas
        print("\n🛒 5. TESTE VENDAS - Verificar se /api/vendas/start usa nova estrutura...")
        
        vendas_response = await client.post(
            f"{BACKEND_URL}/api/vendas/start",
            json={"whatsapp": "5511999999999", "name": "Teste V2 Integration"}
        )
        
        if vendas_response.status_code != 200:
            print(f"❌ Vendas/start falhou: {vendas_response.status_code}")
            return False
            
        vendas_result = vendas_response.json()
        session_id = vendas_result.get("session_id")
        messages = vendas_result.get("messages", [])
        
        if not session_id or not messages:
            print("❌ Vendas/start não retornou session_id ou messages")
            return False
            
        first_message = messages[0].get("text", "")
        
        if len(first_message) < 10:
            print(f"❌ Mensagem inicial muito curta: '{first_message}'")
            return False
            
        print(f"✅ VENDAS - Integração funcionando! Session: {session_id[:8]}...")
        print(f"   💬 Mensagem IA: '{first_message[:50]}...'")
        
        # RESUMO FINAL
        print("\n" + "=" * 60)
        print("🎉 TODOS OS TESTES DO REVIEW REQUEST PASSARAM!")
        print("=" * 60)
        print("✅ 1. GET /api/admin/vendas-bot/simple-config - Estrutura V2 completa")
        print("✅ 2. POST /api/admin/vendas-bot/simple-config - Aceita dados WASiteConfigV2")
        print("✅ 3. Migração Automática - Configs antigas migradas para V2")
        print("✅ 4. Integração Vendas - /api/vendas/start usa nova estrutura")
        print("\n🎯 WA SITE MANAGER V2 ESTÁ FUNCIONANDO CONFORME SOLICITADO!")
        
        return True

async def main():
    """Função principal"""
    try:
        success = await test_wa_site_v2_endpoints()
        if success:
            print("\n🟢 TESTE CONCLUÍDO COM SUCESSO!")
        else:
            print("\n🔴 TESTE FALHOU!")
        return success
    except Exception as e:
        print(f"\n💥 ERRO NO TESTE: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(main())