#!/usr/bin/env python3
"""
Teste do Middleware de Bloqueio de Assinaturas Expiradas
"""
import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient

# Get MongoDB URL
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/cybertv_support')

async def test_subscription_middleware():
    print("🧪 TESTE: Middleware de Bloqueio de Assinaturas Expiradas")
    print("=" * 80)
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.cybertv_support
    
    print("\n📊 1. VERIFICANDO REVENDEDORES EXISTENTES...")
    resellers = await db.resellers.find({}, {"id": 1, "name": 1, "email": 1}).to_list(None)
    print(f"   Total de revendedores: {len(resellers)}")
    
    if not resellers:
        print("   ⚠️ Nenhum revendedor encontrado! Criando revendedores de teste...")
        
        # Criar 2 revendedores de teste
        import bcrypt
        import uuid
        
        reseller1 = {
            "id": str(uuid.uuid4()),
            "name": "Revenda Teste Expirada",
            "email": "teste.expirada@example.com",
            "pass_hash": bcrypt.hashpw(b"teste123", bcrypt.gensalt()).decode(),
            "domain": "",
            "custom_domain": "",
            "test_domain": "teste-expirada.suporte.help",
            "test_domain_active": True,
            "is_active": True,
            "parent_id": None,
            "level": 0,
            "first_login": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        reseller2 = {
            "id": str(uuid.uuid4()),
            "name": "Revenda Teste Ativa",
            "email": "teste.ativa@example.com",
            "pass_hash": bcrypt.hashpw(b"teste123", bcrypt.gensalt()).decode(),
            "domain": "",
            "custom_domain": "",
            "test_domain": "teste-ativa.suporte.help",
            "test_domain_active": True,
            "is_active": True,
            "parent_id": None,
            "level": 0,
            "first_login": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.resellers.insert_one(reseller1)
        await db.resellers.insert_one(reseller2)
        
        resellers = [reseller1, reseller2]
        print(f"   ✅ Revendedores de teste criados!")
    
    for r in resellers[:2]:  # Mostrar apenas os 2 primeiros
        print(f"   - {r['name']} ({r['email']}) - ID: {r['id']}")
    
    print("\n📊 2. VERIFICANDO ASSINATURAS EXISTENTES...")
    subscriptions = await db.subscriptions.find({}, {"_id": 0}).to_list(None)
    print(f"   Total de assinaturas: {len(subscriptions)}")
    
    if subscriptions:
        for sub in subscriptions[:3]:  # Mostrar apenas as 3 primeiras
            reseller_id = sub.get('reseller_id')
            status = sub.get('status')
            end_date = sub.get('current_period_end')
            plan = sub.get('plan_type')
            
            # Find reseller name
            reseller = await db.resellers.find_one({"id": reseller_id})
            reseller_name = reseller['name'] if reseller else 'Desconhecido'
            
            print(f"\n   📌 {reseller_name}:")
            print(f"      Plano: {plan}")
            print(f"      Status: {status}")
            print(f"      Expira em: {end_date}")
            
            # Check if expired
            if end_date:
                try:
                    end = datetime.fromisoformat(end_date)
                    now = datetime.now(timezone.utc)
                    days_left = (end - now).days
                    print(f"      Dias restantes: {days_left}")
                except:
                    pass
    
    print("\n📊 3. CRIANDO CENÁRIOS DE TESTE...")
    
    # Usar os 2 primeiros revendedores para teste
    test_reseller = resellers[0]
    reseller_id = test_reseller['id']
    reseller_name = test_reseller['name']
    reseller_email = test_reseller['email']
    
    print(f"\n   🧪 Revendedor 1 (EXPIRADO): {reseller_name}")
    
    # Criar assinatura expirada para teste
    now = datetime.now(timezone.utc)
    expired_date = now - timedelta(days=2)  # Expirou há 2 dias
    
    expired_subscription = {
        "id": f"test_sub_{reseller_id}",
        "reseller_id": reseller_id,
        "parent_reseller_id": None,
        "plan_type": "basico",
        "status": "expired",
        "trial_ends_at": expired_date.isoformat(),
        "current_period_start": (expired_date - timedelta(days=5)).isoformat(),
        "current_period_end": expired_date.isoformat(),
        "last_payment_date": None,
        "bonus_balance": 0.0,
        "created_at": (expired_date - timedelta(days=5)).isoformat(),
        "updated_at": now.isoformat()
    }
    
    # Deletar assinatura antiga se existir e criar nova
    await db.subscriptions.delete_one({"reseller_id": reseller_id})
    await db.subscriptions.insert_one(expired_subscription)
    
    print(f"      ✅ Assinatura EXPIRADA criada")
    print(f"      - Status: expired")
    print(f"      - Expirou há: 2 dias")
    
    # Criar assinatura ativa para segundo reseller
    if len(resellers) > 1:
        test_reseller2 = resellers[1]
        reseller_id2 = test_reseller2['id']
        reseller_name2 = test_reseller2['name']
        reseller_email2 = test_reseller2['email']
        
        print(f"\n   🧪 Revendedor 2 (ATIVO): {reseller_name2}")
        
        active_date = now + timedelta(days=25)  # Expira em 25 dias
        
        active_subscription = {
            "id": f"test_sub_{reseller_id2}",
            "reseller_id": reseller_id2,
            "parent_reseller_id": None,
            "plan_type": "plus",
            "status": "active",
            "trial_ends_at": now.isoformat(),
            "current_period_start": now.isoformat(),
            "current_period_end": active_date.isoformat(),
            "last_payment_date": now.isoformat(),
            "bonus_balance": 0.0,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
        await db.subscriptions.delete_one({"reseller_id": reseller_id2})
        await db.subscriptions.insert_one(active_subscription)
        
        print(f"      ✅ Assinatura ATIVA criada")
        print(f"      - Status: active")
        print(f"      - Expira em: 25 dias")
    
    print("\n" + "=" * 80)
    print("✅ CENÁRIOS DE TESTE CRIADOS COM SUCESSO!")
    print("\n📋 INSTRUÇÕES PARA TESTE MANUAL:")
    print(f"\n   1️⃣ TESTE ASSINATURA EXPIRADA:")
    print(f"      Email: {reseller_email}")
    print(f"      Senha: teste123")
    print(f"      ❌ Resultado esperado: Erro 403 - Assinatura expirada")
    
    if len(resellers) > 1:
        print(f"\n   2️⃣ TESTE ASSINATURA ATIVA:")
        print(f"      Email: {reseller_email2}")
        print(f"      Senha: teste123")
        print(f"      ✅ Resultado esperado: Login bem-sucedido")
    
    print("\n🔗 URL de teste: https://wppconnect-fix.preview.emergentagent.com/reseller-login")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test_subscription_middleware())
