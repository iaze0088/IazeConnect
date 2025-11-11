#!/bin/bash

echo "🧪 Testing Client Message Send After ObjectId Fix"
echo "=================================================="

# Login as client
echo "1️⃣ Login as client..."
LOGIN=$(curl -s -X POST "https://wppconnect-fix.preview.emergentagent.com/api/auth/client/login" \
  -H "Content-Type: application/json" \
  -d '{"whatsapp": "5511999999999", "pin": "00"}')

TOKEN=$(echo "$LOGIN" | jq -r '.token')
CLIENT_ID=$(echo "$LOGIN" | jq -r '.user_data.id')

if [ "$TOKEN" = "null" ]; then
  echo "❌ Login failed"
  exit 1
fi

echo "✅ Login successful"
echo "   Client ID: ${CLIENT_ID:0:20}..."

# Get agent
echo ""
echo "2️⃣ Getting agent..."
AGENT_ID=$(curl -s -X GET "https://wppconnect-fix.preview.emergentagent.com/api/agents" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[0].id')

echo "✅ Agent ID: ${AGENT_ID:0:20}..."

# Send message
echo ""
echo "3️⃣ Sending message..."
RESPONSE=$(curl -s -X POST "https://wppconnect-fix.preview.emergentagent.com/api/messages" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"ticket_id\": \"\",
    \"from_type\": \"client\",
    \"from_id\": \"$CLIENT_ID\",
    \"to_type\": \"agent\",
    \"to_id\": \"$AGENT_ID\",
    \"kind\": \"text\",
    \"text\": \"Teste após correção do erro ObjectId\",
    \"file_url\": \"\"
  }")

echo "Response: $RESPONSE"

if echo "$RESPONSE" | jq -e '.ok' > /dev/null 2>&1; then
  echo "✅ Message sent successfully!"
else
  echo "❌ Message send failed"
  echo "$RESPONSE" | jq '.'
fi

echo ""
echo "=================================================="
echo "✅ Test completed"
