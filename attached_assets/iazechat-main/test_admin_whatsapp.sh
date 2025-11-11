#!/bin/bash

echo "🧪 Testing Admin WhatsApp Connection Creation"
echo "=============================================="

# Login as admin
echo "1️⃣ Login as admin..."
LOGIN=$(curl -s -X POST "https://wppconnect-fix.preview.emergentagent.com/api/auth/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "102030@ab"}')

TOKEN=$(echo "$LOGIN" | jq -r '.token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
  echo "❌ Admin login failed"
  echo "$LOGIN"
  exit 1
fi

echo "✅ Admin login successful"

# Test creating WhatsApp connection
echo ""
echo "2️⃣ Creating WhatsApp connection for admin..."

RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "https://wppconnect-fix.preview.emergentagent.com/api/whatsapp/connections" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "reseller_id": null
  }')

# Extract HTTP status
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS:/d')

echo "HTTP Status: $HTTP_STATUS"
echo "Response:"
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"

if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "201" ]; then
  echo ""
  echo "✅ WhatsApp connection created successfully!"
else
  echo ""
  echo "❌ Failed with status $HTTP_STATUS"
fi

echo ""
echo "=============================================="
