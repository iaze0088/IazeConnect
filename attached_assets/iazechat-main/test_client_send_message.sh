#!/bin/bash

echo "🧪 Testing Client Message Send (Full Flow)"
echo "============================================"

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
echo "   Client ID: $CLIENT_ID"

# Get agents
echo ""
echo "2️⃣ Getting agents..."
AGENTS=$(curl -s -X GET "https://wppconnect-fix.preview.emergentagent.com/api/agents" \
  -H "Authorization: Bearer $TOKEN")

AGENT_ID=$(echo "$AGENTS" | jq -r '.[0].id')

if [ "$AGENT_ID" = "null" ]; then
  echo "❌ No agents found"
  exit 1
fi

echo "✅ Agent found: $AGENT_ID"

# Send message
echo ""
echo "3️⃣ Sending message..."
MESSAGE_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "https://wppconnect-fix.preview.emergentagent.com/api/messages" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"ticket_id\": \"\",
    \"from_type\": \"client\",
    \"from_id\": \"$CLIENT_ID\",
    \"to_type\": \"agent\",
    \"to_id\": \"$AGENT_ID\",
    \"kind\": \"text\",
    \"text\": \"Teste de mensagem - cliente para suporte\",
    \"file_url\": \"\"
  }")

# Extract HTTP status
HTTP_STATUS=$(echo "$MESSAGE_RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
BODY=$(echo "$MESSAGE_RESPONSE" | sed '/HTTP_STATUS:/d')

echo "HTTP Status: $HTTP_STATUS"
echo "Response:"
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"

if [ "$HTTP_STATUS" = "200" ]; then
  echo ""
  echo "✅ Message sent successfully!"
else
  echo ""
  echo "❌ Message failed with status $HTTP_STATUS"
fi

echo ""
echo "============================================"
