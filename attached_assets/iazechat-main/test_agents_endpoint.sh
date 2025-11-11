#!/bin/bash

echo "Testing /api/agents endpoint..."

# Login as client
LOGIN=$(curl -s -X POST "https://wppconnect-fix.preview.emergentagent.com/api/auth/client/login" \
  -H "Content-Type: application/json" \
  -d '{"whatsapp": "5511999999999", "pin": "00"}')

TOKEN=$(echo "$LOGIN" | jq -r '.token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
  echo "❌ Login failed"
  exit 1
fi

echo "✅ Login successful"
echo ""

# Test GET /api/agents
echo "Testing GET /api/agents:"
RESPONSE=$(curl -s -X GET "https://wppconnect-fix.preview.emergentagent.com/api/agents" \
  -H "Authorization: Bearer $TOKEN")

echo "$RESPONSE" | jq '.'

# Check if it's an error
if echo "$RESPONSE" | jq -e '.detail' > /dev/null 2>&1; then
  echo ""
  echo "❌ Error returned from /api/agents"
else
  COUNT=$(echo "$RESPONSE" | jq '. | length')
  echo ""
  echo "✅ Found $COUNT agent(s)"
fi
