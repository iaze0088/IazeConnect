#!/usr/bin/env python3
"""
Test script to diagnose why client messages are not being saved as tickets
"""
import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
import uuid
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def test_message_flow():
    MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.zendesk_ai
    
    print("=" * 80)
    print("DIAGNOSTIC TEST: Client Message → Ticket Creation Flow")
    print("=" * 80)
    
    # Step 1: Check if there's a test client user
    print("\n1️⃣ Checking for test client user...")
    test_client = await db.users.find_one({
        "user_type": "client",
        "whatsapp": "5511999999999"
    })
    
    if not test_client:
        print("❌ Test client not found. Creating one...")
        test_client_id = str(uuid.uuid4())
        test_client = {
            "id": test_client_id,
            "name": "Cliente Teste",
            "whatsapp": "5511999999999",
            "pin": pwd_context.hash("00"),
            "user_type": "client",
            "reseller_id": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(test_client)
        print(f"✅ Created test client: {test_client_id}")
    else:
        print(f"✅ Test client found: {test_client['id']}")
        test_client_id = test_client['id']
    
    # Step 2: Check if there's an agent
    print("\n2️⃣ Checking for agent...")
    agent = await db.users.find_one({"user_type": "agent"})
    if not agent:
        print("❌ No agent found. Creating one...")
        agent_id = str(uuid.uuid4())
        agent = {
            "id": agent_id,
            "name": "Agente Teste",
            "username": "agente_teste",
            "password": pwd_context.hash("teste123"),
            "user_type": "agent",
            "reseller_id": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(agent)
        print(f"✅ Created test agent: {agent_id}")
    else:
        print(f"✅ Agent found: {agent['id']}")
        agent_id = agent['id']
    
    # Step 3: Simulate what ClientChat.js does - create a message via the backend logic
    print("\n3️⃣ Simulating client message creation...")
    
    # Check if ticket already exists
    existing_ticket = await db.tickets.find_one({"client_id": test_client_id})
    if existing_ticket:
        print(f"⚠️ Ticket already exists: {existing_ticket['id']}")
        ticket_id = existing_ticket['id']
    else:
        print("📝 Creating new ticket...")
        ticket_id = str(uuid.uuid4())
        ticket = {
            "id": ticket_id,
            "client_id": test_client_id,
            "status": "EM_ESPERA",
            "department_id": None,
            "awaiting_department_choice": True,
            "department_choice_sent_at": None,
            "unread_count": 0,
            "reseller_id": None,
            "ticket_origin": "wa_suporte",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        result = await db.tickets.insert_one(ticket)
        print(f"✅ Ticket created: {ticket_id}")
    
    # Step 4: Create a message
    print("\n4️⃣ Creating test message...")
    message_id = str(uuid.uuid4())
    message = {
        "id": message_id,
        "ticket_id": ticket_id,
        "from_type": "client",
        "from_id": test_client_id,
        "to_type": "agent",
        "to_id": agent_id,
        "kind": "text",
        "text": "Olá, preciso de ajuda! (teste automatizado)",
        "pix_key": None,
        "file_url": "",
        "reseller_id": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = await db.messages.insert_one(message)
    print(f"✅ Message created: {message_id}")
    
    # Step 5: Verify data was saved
    print("\n5️⃣ Verifying data in database...")
    
    ticket_check = await db.tickets.find_one({"id": ticket_id})
    if ticket_check:
        print(f"✅ Ticket found in DB: {ticket_id}")
        print(f"   Status: {ticket_check.get('status')}")
        print(f"   Client ID: {ticket_check.get('client_id')}")
        print(f"   Origin: {ticket_check.get('ticket_origin')}")
    else:
        print(f"❌ Ticket NOT found in DB!")
    
    message_check = await db.messages.find_one({"id": message_id})
    if message_check:
        print(f"✅ Message found in DB: {message_id}")
        print(f"   From: {message_check.get('from_type')} ({message_check.get('from_id')})")
        print(f"   Text: {message_check.get('text')}")
    else:
        print(f"❌ Message NOT found in DB!")
    
    # Step 6: Test what the agent dashboard would see
    print("\n6️⃣ Testing agent dashboard query...")
    
    # Simulate the query from server.py list_tickets for an agent
    query = {}
    if agent.get("reseller_id"):
        query["reseller_id"] = agent.get("reseller_id")
    
    # Check for department_ids
    agent_dept_ids = agent.get("department_ids", [])
    if agent_dept_ids:
        query["$or"] = [
            {"department_id": {"$in": agent_dept_ids}},
            {"department_id": {"$exists": False}},
            {"department_id": None}
        ]
    
    tickets_for_agent = await db.tickets.find(query, {"_id": 0}).to_list(None)
    print(f"📊 Agent would see {len(tickets_for_agent)} ticket(s)")
    
    if tickets_for_agent:
        for t in tickets_for_agent:
            print(f"   - Ticket {t['id'][:15]}... Status: {t.get('status')} Client: {t.get('client_id')[:15]}...")
    
    # Step 7: Check with different status filters
    print("\n7️⃣ Testing status filters...")
    for status in ["EM_ESPERA", "open", "ATENDENDO", "FINALIZADO"]:
        count = await db.tickets.count_documents({"status": status})
        print(f"   {status}: {count} ticket(s)")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETED")
    print("=" * 80)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test_message_flow())
