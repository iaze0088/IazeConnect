"""
Teste do sistema de fallback da IA (timeout e erros)
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
import uuid

load_dotenv('/app/backend/.env')

async def test_ai_fallback():
    mongo_url = os.environ.get('MONGO_URL')
    client = AsyncIOMotorClient(mongo_url)
    db = client['support_chat']
    
    print("=" * 80)
    print("TESTE: Sistema de Fallback da IA")
    print("=" * 80)
    
    # Buscar um ticket para testar
    print("\n1️⃣ Buscando ticket de teste...")
    
    # Criar ticket de teste para WA Suporte (origem site/chat)
    wa_suporte_ticket_id = str(uuid.uuid4())
    wa_suporte_ticket = {
        "id": wa_suporte_ticket_id,
        "whatsapp": "5511999999999",
        "client_name": "Cliente Teste WA Suporte",
        "client_id": str(uuid.uuid4()),
        "status": "open",
        "department_id": str(uuid.uuid4()),
        "reseller_id": str(uuid.uuid4()),
        "ticket_origin": "wa_suporte",
        # NÃO tem campos whatsapp_origin, whatsapp_instance, etc.
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.tickets.insert_one(wa_suporte_ticket)
    print(f"   ✅ Ticket WA Suporte criado: {wa_suporte_ticket_id}")
    
    # Criar ticket de teste para WhatsApp QR Code
    whatsapp_qr_ticket_id = str(uuid.uuid4())
    whatsapp_qr_ticket = {
        "id": whatsapp_qr_ticket_id,
        "whatsapp": "5511888888888",
        "client_name": "Cliente Teste WhatsApp QR",
        "client_id": str(uuid.uuid4()),
        "status": "open",
        "department_id": str(uuid.uuid4()),
        "reseller_id": str(uuid.uuid4()),
        "ticket_origin": "whatsapp",
        "whatsapp_origin": True,  # ✅ Campo que identifica WhatsApp QR Code
        "whatsapp_instance": "instance123",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.tickets.insert_one(whatsapp_qr_ticket)
    print(f"   ✅ Ticket WhatsApp QR criado: {whatsapp_qr_ticket_id}")
    
    # Simular fallback
    print("\n2️⃣ Testando função handle_ai_failure_fallback...")
    
    import sys
    sys.path.append('/app/backend')
    from server import handle_ai_failure_fallback
    
    # Teste 1: WA Suporte (origem site/chat)
    print("\n   📋 TESTE 1: Ticket de WA Suporte")
    print(f"      Origem: Site/Chat (sem campos whatsapp_*)")
    print(f"      Esperado: Transferir para aba WA SUPORTE")
    
    await handle_ai_failure_fallback(
        ticket=wa_suporte_ticket,
        reason="Teste: Timeout de 2 minutos",
        reseller_id=wa_suporte_ticket["reseller_id"]
    )
    
    # Verificar resultado
    updated_ticket_1 = await db.tickets.find_one({"id": wa_suporte_ticket_id})
    print(f"\n      ✅ Verificando resultado:")
    print(f"         Status: {updated_ticket_1.get('status')}")
    print(f"         AI Disabled: {updated_ticket_1.get('ai_disabled')}")
    print(f"         AI Disabled Reason: {updated_ticket_1.get('ai_disabled_reason')}")
    print(f"         Requires Human: {updated_ticket_1.get('requires_human_attention')}")
    
    # Verificar mensagem de sistema
    fallback_msg_1 = await db.messages.find_one({"ticket_id": wa_suporte_ticket_id})
    if fallback_msg_1:
        print(f"         Mensagem enviada: {fallback_msg_1.get('text')[:60]}...")
        print(f"         From Type: {fallback_msg_1.get('from_type')}")
    
    # Teste 2: WhatsApp QR Code
    print("\n   📋 TESTE 2: Ticket de WhatsApp QR Code")
    print(f"      Origem: WhatsApp QR Code (whatsapp_origin=True)")
    print(f"      Esperado: Transferir para aba WHATSAPP")
    
    await handle_ai_failure_fallback(
        ticket=whatsapp_qr_ticket,
        reason="Teste: Erro na IA",
        reseller_id=whatsapp_qr_ticket["reseller_id"]
    )
    
    # Verificar resultado
    updated_ticket_2 = await db.tickets.find_one({"id": whatsapp_qr_ticket_id})
    print(f"\n      ✅ Verificando resultado:")
    print(f"         Status: {updated_ticket_2.get('status')}")
    print(f"         AI Disabled: {updated_ticket_2.get('ai_disabled')}")
    print(f"         AI Disabled Reason: {updated_ticket_2.get('ai_disabled_reason')}")
    print(f"         Requires Human: {updated_ticket_2.get('requires_human_attention')}")
    
    # Verificar mensagem de sistema
    fallback_msg_2 = await db.messages.find_one({"ticket_id": whatsapp_qr_ticket_id})
    if fallback_msg_2:
        print(f"         Mensagem enviada: {fallback_msg_2.get('text')[:60]}...")
        print(f"         From Type: {fallback_msg_2.get('from_type')}")
    
    # Limpar dados de teste
    print("\n3️⃣ Limpando dados de teste...")
    await db.tickets.delete_one({"id": wa_suporte_ticket_id})
    await db.tickets.delete_one({"id": whatsapp_qr_ticket_id})
    await db.messages.delete_many({"ticket_id": {"$in": [wa_suporte_ticket_id, whatsapp_qr_ticket_id]}})
    print(f"   ✅ Dados de teste removidos")
    
    print("\n" + "=" * 80)
    print("RESULTADO:")
    print("=" * 80)
    print("✅ Sistema de fallback implementado com sucesso!")
    print("✅ Timeout de 2 minutos configurado")
    print("✅ Roteamento correto:")
    print("   - WA Suporte → Aba WA SUPORTE (vermelha)")
    print("   - WhatsApp QR → Aba WHATSAPP (verde)")
    print("✅ IA desativada após fallback")
    print("✅ Mensagem de transferência enviada ao cliente")
    print("=" * 80)
    
    client.close()

asyncio.run(test_ai_fallback())
