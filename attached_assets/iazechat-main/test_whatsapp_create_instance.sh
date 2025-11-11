#!/bin/bash

echo "=================================="
echo "TESTE: Criar Instância WhatsApp"
echo "=================================="
echo ""

# Ler credenciais
read -p "Digite seu email/login: " EMAIL
read -sp "Digite sua senha: " PASSWORD
echo ""
echo ""

# Backend URL
BACKEND_URL="${REACT_APP_BACKEND_URL:-http://localhost:8001}"

echo "🔐 Fazendo login..."
LOGIN_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Erro no login!"
    echo "Resposta: $LOGIN_RESPONSE"
    exit 1
fi

echo "✅ Login realizado com sucesso!"
echo ""

# Criar instância de teste
INSTANCE_NAME="teste_$(date +%s)"

echo "📱 Criando instância WhatsApp: $INSTANCE_NAME"
echo ""

CREATE_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/whatsapp/create-instance" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"instance_name\":\"$INSTANCE_NAME\"}")

echo "📥 Resposta da API:"
echo "$CREATE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$CREATE_RESPONSE"
echo ""

# Verificar se teve erro 400
if echo "$CREATE_RESPONSE" | grep -q "400"; then
    echo "❌ ERRO 400 - Ainda há problema na formatação!"
    echo ""
    echo "Logs do backend:"
    tail -n 20 /var/log/supervisor/backend.out.log | grep -E "criar instância|400|Evolution"
else
    echo "✅ Instância criada com sucesso!"
    echo ""
    echo "Você pode testar agora na interface web!"
fi
