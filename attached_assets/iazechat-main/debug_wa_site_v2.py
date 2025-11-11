#!/usr/bin/env python3
"""
DEBUG: Verificar estrutura atual do WA Site Manager V2
"""

import asyncio
import httpx
import json

BACKEND_URL = "https://wppconnect-fix.preview.emergentagent.com"
ADMIN_PASSWORD = "102030@ab"

async def debug_config_structure():
    """Debug da estrutura atual"""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Login
        login_response = await client.post(
            f"{BACKEND_URL}/api/auth/admin/login",
            json={"password": ADMIN_PASSWORD}
        )
        
        token = login_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # GET config
        get_response = await client.get(
            f"{BACKEND_URL}/api/admin/vendas-bot/simple-config",
            headers=headers
        )
        
        config = get_response.json()
        
        print("🔍 ESTRUTURA ATUAL DO CONFIG:")
        print("=" * 50)
        print(json.dumps(config, indent=2, ensure_ascii=False))
        
        print("\n📋 CAMPOS PRINCIPAIS:")
        for key in config.keys():
            print(f"  - {key}: {type(config[key])}")
            
        print("\n🤖 ia_config DETALHADO:")
        ia_config = config.get("ia_config", {})
        if ia_config:
            for key, value in ia_config.items():
                print(f"  - {key}: {value}")
        else:
            print("  ❌ ia_config está vazio ou não existe")

if __name__ == "__main__":
    asyncio.run(debug_config_structure())