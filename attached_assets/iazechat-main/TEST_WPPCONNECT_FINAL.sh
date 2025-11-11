#!/bin/bash
# Teste Final da Integração WPPConnect

set -e

echo "========================================="
echo "🧪 TESTE FINAL WPPCONNECT"
echo "========================================="
echo ""

WPPCONNECT_URL="http://151.243.218.223:21465"
SECRET_KEY="THISISMYSECURETOKEN"
SESSION="teste_final_iaze"

echo "📍 Passo 1: Gerar Token"
TOKEN_RESPONSE=$(curl -s -X POST "$WPPCONNECT_URL/api/$SESSION/$SECRET_KEY/generate-token")
echo "Response: $TOKEN_RESPONSE"
TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.token' | sed 's/\//_/g' | sed 's/+/-/g')
echo "✅ Token: $TOKEN"
echo ""

echo "📍 Passo 2: Iniciar Sessão"
START_RESPONSE=$(curl -s -X POST "$WPPCONNECT_URL/api/$SESSION:$TOKEN/start-session" \
  -H "Content-Type: application/json" \
  -d '{"waitQrCode": false, "webhook": "https://suporte.help/api/whatsapp/webhook/wppconnect"}')
echo "Response: $START_RESPONSE"
echo ""

echo "📍 Passo 3: Verificar Status e Obter QR Code"
sleep 3
STATUS_RESPONSE=$(curl -s -X GET "$WPPCONNECT_URL/api/$SESSION:$TOKEN/status-session")
echo "Status: $(echo "$STATUS_RESPONSE" | jq -r '.status')"
QR_CODE=$(echo "$STATUS_RESPONSE" | jq -r '.qrcode' 2>/dev/null || echo "")

if [ -n "$QR_CODE" ] && [ "$QR_CODE" != "null" ]; then
    echo "✅ QR Code obtido com sucesso!"
    echo "QR Code length: ${#QR_CODE} caracteres"
else
    echo "⚠️ QR Code não disponível ainda (normal para sessões já conectadas)"
fi
echo ""

echo "📍 Passo 4: Fechar Sessão"
CLOSE_RESPONSE=$(curl -s -X POST "$WPPCONNECT_URL/api/$SESSION:$TOKEN/close-session")
echo "Response: $CLOSE_RESPONSE"
echo ""

echo "========================================="
echo "✅ TESTE COMPLETO!"
echo "========================================="
echo ""
echo "🎯 PRÓXIMOS PASSOS:"
echo "1. Acesse: http://suporte.help/admin"
echo "2. Vá para aba WhatsApp"
echo "3. Clique em 'Nova Conexão'"
echo "4. Digite um nome (ex: 'Suporte Principal')"
echo "5. O QR Code deve aparecer automaticamente!"
echo ""
echo "📝 BACKEND LOGS:"
echo "tail -f /var/log/supervisor/backend.*.log | grep -E 'WPPConnect|WhatsApp'"
