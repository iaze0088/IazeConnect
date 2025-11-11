#!/bin/bash

# Test script to verify client message → ticket creation flow

BACKEND_URL="https://wppconnect-fix.preview.emergentagent.com"

echo "=========================================="
echo "TEST: Client Message → Ticket Creation"
echo "=========================================="

# Step 1: Login as test client
echo -e "\n1️⃣ Login as test client (5511999999999 / 00)..."
LOGIN_RESPONSE=$(curl -s -X POST "${BACKEND_URL}/api/auth/client/login" \
  -H "Content-Type: application/json" \
  -d '{"whatsapp": "5511999999999", "pin": "00"}')

echo "$LOGIN_RESPONSE" | jq '.' 2>/dev/null || echo "$LOGIN_RESPONSE"

# Extract token
TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.token' 2>/dev/null)
if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
  echo "❌ Login failed - no token received"
  exit 1
fi

CLIENT_ID=$(echo "$LOGIN_RESPONSE" | jq -r '.user_data.id' 2>/dev/null)
echo "✅ Login successful! Client ID: ${CLIENT_ID:0:20}..."
echo "Token: ${TOKEN:0:30}..."

# Step 2: Get first agent (for to_id)
echo -e "\n2️⃣ Getting first agent..."
AGENTS_RESPONSE=$(curl -s -X GET "${BACKEND_URL}/api/agents" \
  -H "Authorization: Bearer $TOKEN")

AGENT_ID=$(echo "$AGENTS_RESPONSE" | jq -r '.[0].id' 2>/dev/null)
if [ "$AGENT_ID" = "null" ] || [ -z "$AGENT_ID" ]; then
  echo "❌ No agents found"
  exit 1
fi
echo "✅ Agent found: ${AGENT_ID:0:20}..."

# Step 3: Send a message
echo -e "\n3️⃣ Sending message from client..."
MESSAGE_RESPONSE=$(curl -s -X POST "${BACKEND_URL}/api/messages" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"ticket_id\": \"\",
    \"from_type\": \"client\",
    \"from_id\": \"$CLIENT_ID\",
    \"to_type\": \"agent\",
    \"to_id\": \"$AGENT_ID\",
    \"kind\": \"text\",
    \"text\": \"Olá! Preciso de suporte urgente. (teste automatizado)\",
    \"file_url\": \"\"
  }")

echo "$MESSAGE_RESPONSE" | jq '.' 2>/dev/null || echo "$MESSAGE_RESPONSE"

# Check if successful (200 OK)
if echo "$MESSAGE_RESPONSE" | grep -q "detail"; then
  echo "❌ Message failed with error"
  exit 1
fi

echo "✅ Message sent successfully!"

# Step 4: Verify ticket was created
echo -e "\n4️⃣ Verifying ticket was created..."
python3 << 'PYTHON_EOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys

async def verify_ticket():
    MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(MONGO_URL)
    # Use correct database name
    db_name = os.environ.get('DB_NAME', 'support_chat')
    db = client[db_name]
    
    # Check tickets
    tickets = await db.tickets.find({}, {"_id": 0}).to_list(None)
    print(f"📊 Total tickets in DB: {len(tickets)}")
    
    if tickets:
        for ticket in tickets:
            print(f"   ✅ Ticket ID: {ticket['id'][:20]}...")
            print(f"      Status: {ticket.get('status')}")
            print(f"      Client: {ticket.get('client_id')[:20]}...")
            print(f"      Origin: {ticket.get('ticket_origin')}")
    else:
        print("   ❌ NO TICKETS FOUND!")
        sys.exit(1)
    
    # Check messages
    messages = await db.messages.find({}, {"_id": 0}).to_list(None)
    print(f"\n📨 Total messages in DB: {len(messages)}")
    
    if messages:
        for msg in messages:
            print(f"   ✅ Message from {msg.get('from_type')}: {msg.get('text')[:50]}...")
    else:
        print("   ❌ NO MESSAGES FOUND!")
        sys.exit(1)
    
    # Check if status is 'open'
    open_tickets = [t for t in tickets if t.get('status') == 'open']
    if open_tickets:
        print(f"\n✅ SUCCESS! {len(open_tickets)} ticket(s) with status='open' found!")
    else:
        print("\n❌ ERROR! No tickets with status='open' found!")
        sys.exit(1)
    
    client.close()

asyncio.run(verify_ticket())
PYTHON_EOF

echo -e "\n=========================================="
echo "✅ TEST COMPLETED SUCCESSFULLY!"
echo "=========================================="
