"""
Script de teste para verificar redirecionamento de "reembolso"
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime, timezone

load_dotenv('/app/backend/.env')

async def test_reembolso_redirect():
    mongo_url = os.environ.get('MONGO_URL')
    client = AsyncIOMotorClient(mongo_url)
    db = client['support_chat']
    
    print("=" * 80)
    print("TESTE DE REDIRECIONAMENTO - PALAVRA 'REEMBOLSO'")
    print("=" * 80)
    
    # 1. Criar sessão de teste
    session_id = str(uuid.uuid4())
    test_whatsapp = "5511999999999"
    
    print(f"\n1️⃣ Criando sessão de teste...")
    print(f"   Session ID: {session_id}")
    print(f"   WhatsApp: {test_whatsapp}")
    
    # Buscar reseller_id
    first_reseller = await db.resellers.find_one({})
    reseller_id = first_reseller.get("id") if first_reseller else None
    
    session_data = {
        "session_id": session_id,
        "whatsapp": test_whatsapp,
        "reseller_id": reseller_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_message_at": datetime.now(timezone.utc).isoformat(),
        "ai_active": True,
        "status": "active"
    }
    
    await db.vendas_sessions.insert_one(session_data)
    print(f"   ✅ Sessão criada com reseller_id: {reseller_id}")
    
    # 2. Simular mensagem com palavra "reembolso"
    print(f"\n2️⃣ Simulando mensagem: 'quero reembolso'")
    
    # Importar o serviço
    import sys
    sys.path.append('/app/backend')
    from vendas_ai_service import vendas_ai_service
    
    # Chamar função de redirecionamento diretamente
    result = await vendas_ai_service.redirect_to_support(
        session_id=session_id,
        whatsapp=test_whatsapp,
        reason="reembolso",
        db=db
    )
    
    print(f"   ✅ Resultado do redirecionamento:")
    print(f"      Success: {result.get('success')}")
    print(f"      Message: {result.get('message')}")
    
    # 3. Verificar se sessão foi atualizada
    print(f"\n3️⃣ Verificando atualização da sessão...")
    session_updated = await db.vendas_sessions.find_one({"session_id": session_id})
    
    print(f"   AI Active: {session_updated.get('ai_active')}")
    print(f"   Redirected to Support: {session_updated.get('redirected_to_support')}")
    print(f"   Redirect Reason: {session_updated.get('ai_deactivation_reason')}")
    
    # 4. Verificar se ticket foi criado
    print(f"\n4️⃣ Verificando criação do ticket...")
    ticket = await db.tickets.find_one({
        "whatsapp": test_whatsapp,
        "status": "open"
    })
    
    if ticket:
        print(f"   ✅ TICKET CRIADO COM SUCESSO!")
        print(f"      Ticket ID: {ticket.get('id')}")
        print(f"      Ticket Number: {ticket.get('ticket_number')}")
        print(f"      WhatsApp: {ticket.get('whatsapp')}")
        print(f"      Status: {ticket.get('status')}")
        print(f"      Department ID: {ticket.get('department_id')}")
        print(f"      Reseller ID: {ticket.get('reseller_id')}")
        print(f"      Ticket Origin: {ticket.get('ticket_origin')}")
        print(f"      AI Redirected: {ticket.get('ai_redirected')}")
        print(f"      AI Redirect Reason: {ticket.get('ai_redirect_reason')}")
    else:
        print(f"   ❌ TICKET NÃO FOI CRIADO!")
    
    # 5. Verificar departamentos disponíveis
    print(f"\n5️⃣ Verificando departamentos no sistema...")
    departments = await db.departments.find({}).to_list(length=None)
    print(f"   Total de departamentos: {len(departments)}")
    for dept in departments:
        print(f"      - {dept.get('name')} (ID: {dept.get('id')})")
    
    # 6. Limpar dados de teste
    print(f"\n6️⃣ Limpando dados de teste...")
    await db.vendas_sessions.delete_one({"session_id": session_id})
    if ticket:
        await db.tickets.delete_one({"id": ticket.get('id')})
    print(f"   ✅ Dados de teste removidos")
    
    print("\n" + "=" * 80)
    print("TESTE CONCLUÍDO")
    print("=" * 80)
    
    client.close()

asyncio.run(test_reembolso_redirect())
