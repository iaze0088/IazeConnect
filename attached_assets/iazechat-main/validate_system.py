#!/usr/bin/env python3
"""
SCRIPT DE VALIDAÇÃO FINAL - PRÉ-DEPLOY
Verifica TUDO antes de fazer deploy em produção
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')

async def validate_system():
    print("=" * 80)
    print("🔍 VALIDAÇÃO FINAL DO SISTEMA - PRÉ-DEPLOY")
    print("=" * 80)
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.support_chat
    
    errors = []
    warnings = []
    success = []
    
    # 1. Verificar Collections Essenciais
    print("\n📦 VERIFICANDO COLLECTIONS...")
    required_collections = [
        'users', 'resellers', 'departments', 'tickets', 'messages',
        'whatsapp_connections', 'subscriptions', 'payments',
        'bonus_transactions', 'mercado_pago_config'
    ]
    
    existing_collections = await db.list_collection_names()
    
    for coll in required_collections:
        if coll in existing_collections:
            count = await db[coll].count_documents({})
            success.append(f"✅ {coll}: {count} documentos")
        else:
            warnings.append(f"⚠️ {coll}: Collection não existe (será criada automaticamente)")
    
    # 2. Verificar Usuários Admin
    print("\n👤 VERIFICANDO USUÁRIOS...")
    admin_count = await db.users.count_documents({"user_type": "admin"})
    reseller_count = await db.resellers.count_documents({})
    agent_count = await db.users.count_documents({"user_type": "agent"})
    
    if admin_count > 0:
        success.append(f"✅ {admin_count} admin(s) cadastrado(s)")
    else:
        errors.append("❌ CRÍTICO: Nenhum admin cadastrado!")
    
    success.append(f"✅ {reseller_count} revenda(s) cadastrada(s)")
    success.append(f"✅ {agent_count} atendente(s) cadastrado(s)")
    
    # 3. Verificar Departamentos
    print("\n🏢 VERIFICANDO DEPARTAMENTOS...")
    dept_count = await db.departments.count_documents({})
    whatsapp_dept_count = await db.departments.count_documents({"name": {"$regex": "WHATSAPP"}})
    
    success.append(f"✅ {dept_count} departamento(s) total")
    success.append(f"✅ {whatsapp_dept_count} departamento(s) WhatsApp")
    
    # 4. Verificar WhatsApp
    print("\n📱 VERIFICANDO WHATSAPP...")
    wa_connections = await db.whatsapp_connections.count_documents({})
    wa_connected = await db.whatsapp_connections.count_documents({"status": "connected"})
    
    if wa_connections > 0:
        success.append(f"✅ {wa_connections} conexão(ões) WhatsApp configurada(s)")
        success.append(f"✅ {wa_connected} conexão(ões) ativa(s)")
    else:
        warnings.append("⚠️ Nenhuma conexão WhatsApp configurada")
    
    # 5. Verificar Assinaturas
    print("\n💳 VERIFICANDO ASSINATURAS...")
    subscription_count = await db.subscriptions.count_documents({})
    trial_count = await db.subscriptions.count_documents({"status": "trial"})
    active_count = await db.subscriptions.count_documents({"status": "active"})
    expired_count = await db.subscriptions.count_documents({"status": "expired"})
    
    if subscription_count > 0:
        success.append(f"✅ {subscription_count} assinatura(s) total")
        success.append(f"   - Trial: {trial_count}")
        success.append(f"   - Ativas: {active_count}")
        success.append(f"   - Expiradas: {expired_count}")
    else:
        warnings.append("⚠️ Nenhuma assinatura criada ainda")
    
    # 6. Verificar Config Mercado Pago
    print("\n💰 VERIFICANDO MERCADO PAGO...")
    mp_config = await db.mercado_pago_config.find_one({})
    
    if mp_config:
        if mp_config.get('access_token') and mp_config.get('public_key'):
            success.append("✅ Mercado Pago configurado")
            if mp_config.get('enabled'):
                success.append("✅ Mercado Pago habilitado")
            else:
                warnings.append("⚠️ Mercado Pago desabilitado")
        else:
            warnings.append("⚠️ Mercado Pago sem credenciais")
    else:
        warnings.append("⚠️ Mercado Pago não configurado")
    
    # 7. Verificar Multi-Tenant (Isolamento)
    print("\n🔒 VERIFICANDO ISOLAMENTO MULTI-TENANT...")
    
    # Verificar se há departamentos sem reseller_id (pode indicar vazamento)
    depts_without_reseller = await db.departments.count_documents({
        "reseller_id": {"$exists": False}
    })
    
    if depts_without_reseller > 0:
        warnings.append(f"⚠️ {depts_without_reseller} departamento(s) sem reseller_id")
    else:
        success.append("✅ Todos departamentos têm reseller_id")
    
    # Verificar se há connections sem reseller_id
    wa_without_reseller = await db.whatsapp_connections.count_documents({
        "reseller_id": {"$exists": False}
    })
    
    if wa_without_reseller > 0:
        warnings.append(f"⚠️ {wa_without_reseller} conexão(ões) WhatsApp sem reseller_id")
    else:
        success.append("✅ Todas conexões WhatsApp têm reseller_id")
    
    # 8. Verificar Tickets
    print("\n🎫 VERIFICANDO TICKETS...")
    ticket_count = await db.tickets.count_documents({})
    open_tickets = await db.tickets.count_documents({"status": "open"})
    closed_tickets = await db.tickets.count_documents({"status": "closed"})
    
    success.append(f"✅ {ticket_count} ticket(s) total")
    success.append(f"   - Abertos: {open_tickets}")
    success.append(f"   - Fechados: {closed_tickets}")
    
    # 9. Verificar Mensagens
    print("\n💬 VERIFICANDO MENSAGENS...")
    message_count = await db.messages.count_documents({})
    whatsapp_messages = await db.messages.count_documents({"is_whatsapp": True})
    
    success.append(f"✅ {message_count} mensagem(ns) total")
    success.append(f"✅ {whatsapp_messages} mensagem(ns) do WhatsApp")
    
    # RELATÓRIO FINAL
    print("\n" + "=" * 80)
    print("📊 RELATÓRIO FINAL")
    print("=" * 80)
    
    if success:
        print("\n✅ SUCESSOS:")
        for s in success:
            print(f"  {s}")
    
    if warnings:
        print("\n⚠️ AVISOS (não bloqueiam deploy):")
        for w in warnings:
            print(f"  {w}")
    
    if errors:
        print("\n❌ ERROS CRÍTICOS (BLOQUEIAM DEPLOY):")
        for e in errors:
            print(f"  {e}")
    
    print("\n" + "=" * 80)
    
    if errors:
        print("🚫 SISTEMA NÃO ESTÁ PRONTO PARA DEPLOY")
        print("Corrija os erros críticos antes de fazer deploy!")
        print("=" * 80)
        return False
    else:
        print("✅ SISTEMA PRONTO PARA DEPLOY!")
        print("Todos os checks passaram com sucesso!")
        print("=" * 80)
        return True

if __name__ == "__main__":
    result = asyncio.run(validate_system())
    sys.exit(0 if result else 1)
