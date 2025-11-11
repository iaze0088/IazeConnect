"""
Script para criar o Reseller Principal com domínio suporte.help
"""
import asyncio
import os
import uuid
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

# Configuração do MongoDB
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'support_chat')

# Configuração de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_main_reseller():
    """Criar o reseller principal"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("🚀 CRIANDO RESELLER PRINCIPAL...\n")
    print("="*80)
    
    # Dados do reseller
    reseller_id = str(uuid.uuid4())
    reseller_data = {
        "id": reseller_id,
        "name": "suporte",
        "email": "admin@suporte.help",
        "password": pwd_context.hash("102030@ab"),
        "custom_domain": "suporte.help",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "parent_id": None,  # Revenda raiz
        "commission_percentage": 0,
        "subscription_active": True,
        "client_logo_url": "",
        "logo_url": "",
        "company_name": "IAZE Suporte",
        "company_address": "",
        "company_phone": "",
        "allow_subresellers": True,
    }
    
    # Verificar se já existe
    existing = await db.resellers.find_one({"email": "admin@suporte.help"})
    if existing:
        print(f"⚠️  Reseller com email admin@suporte.help já existe!")
        print(f"   ID: {existing['id']}")
        print(f"   Atualizando domínio customizado para: suporte.help")
        
        # Atualizar apenas o domínio
        await db.resellers.update_one(
            {"id": existing['id']},
            {"$set": {"custom_domain": "suporte.help"}}
        )
        reseller_id = existing['id']
        print(f"✅ Domínio atualizado com sucesso!\n")
    else:
        # Criar novo reseller
        await db.resellers.insert_one(reseller_data)
        print(f"✅ RESELLER CRIADO COM SUCESSO!\n")
        print(f"📋 DETALHES:")
        print(f"   ID: {reseller_id}")
        print(f"   Nome: suporte")
        print(f"   Email: admin@suporte.help")
        print(f"   Domínio: suporte.help")
        print(f"   Senha: 102030@ab")
        print(f"   Status: ATIVO\n")
    
    # Criar subscription ativa (1 ano)
    subscription_id = str(uuid.uuid4())
    end_date = datetime.now(timezone.utc) + timedelta(days=365)
    
    existing_sub = await db.subscriptions.find_one({"reseller_id": reseller_id})
    if not existing_sub:
        subscription_data = {
            "id": subscription_id,
            "reseller_id": reseller_id,
            "status": "active",
            "start_date": datetime.now(timezone.utc).isoformat(),
            "end_date": end_date.isoformat(),
            "plan": "premium",
            "amount": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.subscriptions.insert_one(subscription_data)
        print(f"✅ SUBSCRIPTION CRIADA:")
        print(f"   Status: active")
        print(f"   Válida até: {end_date.strftime('%d/%m/%Y')}\n")
    else:
        print(f"✅ Subscription já existe para este reseller\n")
    
    # Criar config do reseller
    existing_config = await db.reseller_configs.find_one({"reseller_id": reseller_id})
    if not existing_config:
        config_data = {
            "reseller_id": reseller_id,
            "business_hours_start": "09:00",
            "business_hours_end": "23:00",
            "manual_away_mode": False,
            "away_message": "Estamos ausentes no momento. Deixe sua mensagem que retornaremos em breve!",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.reseller_configs.insert_one(config_data)
        print(f"✅ CONFIG CRIADA:")
        print(f"   Horário: 09:00 - 23:00")
        print(f"   Modo ausente: Desativado\n")
    else:
        print(f"✅ Config já existe para este reseller\n")
    
    print("="*80)
    print("\n🎉 RESELLER PRINCIPAL CONFIGURADO COM SUCESSO!\n")
    print("📍 PRÓXIMOS PASSOS:")
    print("   1. Acesse: https://suporte.help/revenda/login")
    print("   2. Login: admin@suporte.help")
    print("   3. Senha: 102030@ab")
    print("   4. Configure seus atendentes e AI agents nesta revenda")
    print("   5. O /vendas agora funcionará em: https://suporte.help/vendas\n")
    print("🔐 ADMIN MASTER continua em:")
    print("   https://wppconnect-fix.preview.emergentagent.com/admin\n")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_main_reseller())
