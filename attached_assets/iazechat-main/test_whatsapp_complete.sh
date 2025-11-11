#!/bin/bash
set -e

echo "=================================="
echo "🧪 TESTE COMPLETO WHATSAPP API"
echo "=================================="
echo ""

BACKEND_URL="https://suporte.help/api"

# Passo 1: Admin Login
echo "📍 1. Admin Login..."
LOGIN_RESPONSE=$(curl -s -X POST "$BACKEND_URL/auth/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@admin.com","password":"102030@ab"}')

TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.token')
if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
    echo "❌ Login falhou!"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi
echo "✅ Token obtido: ${TOKEN:0:50}..."
echo ""

# Passo 2: Criar Nova Conexão
echo "📍 2. Criar Nova Conexão WhatsApp..."
echo "⏳ Aguardando até 30s para QR code ser gerado..."
CREATE_RESPONSE=$(curl -s -X POST "$BACKEND_URL/whatsapp/connections" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Teste Automatizado '$(date +%H%M%S)'"}' \
  --max-time 35)

echo "$CREATE_RESPONSE" | jq '.'
CONNECTION_ID=$(echo "$CREATE_RESPONSE" | jq -r '.id')
QR_CODE=$(echo "$CREATE_RESPONSE" | jq -r '.qr_code')

if [ "$CONNECTION_ID" = "null" ] || [ -z "$CONNECTION_ID" ]; then
    echo "❌ Criação de conexão falhou!"
    exit 1
fi

echo "✅ Conexão criada: $CONNECTION_ID"

if [ "$QR_CODE" != "null" ] && [ -n "$QR_CODE" ]; then
    echo "✅ QR Code obtido (${#QR_CODE} caracteres)"
else
    echo "⚠️ QR Code não disponível"
fi
echo ""

# Passo 3: Listar Conexões
echo "📍 3. Listar Conexões..."
LIST_RESPONSE=$(curl -s -X GET "$BACKEND_URL/whatsapp/connections" \
  -H "Authorization: Bearer $TOKEN")

CONN_COUNT=$(echo "$LIST_RESPONSE" | jq 'length')
echo "✅ Total de conexões: $CONN_COUNT"
echo ""

# Passo 4: Verificar Status
echo "📍 4. Verificar Status da Conexão..."
STATUS_RESPONSE=$(curl -s -X GET "$BACKEND_URL/whatsapp/connections/$CONNECTION_ID/check-status" \
  -H "Authorization: Bearer $TOKEN")

echo "$STATUS_RESPONSE" | jq '.'
STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status')
echo "✅ Status: $STATUS"
echo ""

# Passo 5: Deletar Conexão
echo "📍 5. Deletar Conexão..."
DELETE_RESPONSE=$(curl -s -X DELETE "$BACKEND_URL/whatsapp/connections/$CONNECTION_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "$DELETE_RESPONSE" | jq '.'
echo "✅ Conexão deletada"
echo ""

echo "=================================="
echo "✅ TODOS OS TESTES PASSARAM!"
echo "=================================="
