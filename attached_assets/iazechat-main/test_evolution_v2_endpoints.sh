#!/bin/bash

# Script de Teste Evolution API v2.3.6
# Valida se todos os endpoints estão funcionando após upgrade

EVOLUTION_API_URL=${1:-"http://localhost:8080"}
EVOLUTION_API_KEY=${2:-"cybertv-suporte-evolution-key-2024"}

echo "=========================================="
echo "TESTE EVOLUTION API v2.3.6"
echo "=========================================="
echo "URL: $EVOLUTION_API_URL"
echo "API Key: ${EVOLUTION_API_KEY:0:10}..."
echo ""

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Testar API Info
echo -e "${YELLOW}[1/5] Testando GET / (API Info)...${NC}"
response=$(curl -s -w "\n%{http_code}" \
  -H "apikey: $EVOLUTION_API_KEY" \
  "$EVOLUTION_API_URL/")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 201 ]; then
    echo -e "${GREEN}✅ API Info OK${NC}"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo -e "${RED}❌ ERRO: HTTP $http_code${NC}"
    echo "$body"
fi
echo ""

# 2. Testar Fetch Instances
echo -e "${YELLOW}[2/5] Testando GET /instance/fetchInstances...${NC}"
response=$(curl -s -w "\n%{http_code}" \
  -H "apikey: $EVOLUTION_API_KEY" \
  "$EVOLUTION_API_URL/instance/fetchInstances")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 201 ]; then
    echo -e "${GREEN}✅ Fetch Instances OK${NC}"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
else
    echo -e "${RED}❌ ERRO: HTTP $http_code${NC}"
    echo "$body"
fi
echo ""

# 3. Testar Create Instance
TEST_INSTANCE_NAME="test_cybertv_$(date +%s)"
echo -e "${YELLOW}[3/5] Testando POST /instance/create...${NC}"
echo "Nome da instância teste: $TEST_INSTANCE_NAME"
response=$(curl -s -w "\n%{http_code}" \
  -X POST \
  -H "Content-Type: application/json" \
  -H "apikey: $EVOLUTION_API_KEY" \
  -d "{\"instanceName\": \"$TEST_INSTANCE_NAME\", \"qrcode\": true}" \
  "$EVOLUTION_API_URL/instance/create")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 201 ]; then
    echo -e "${GREEN}✅ Create Instance OK${NC}"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
    INSTANCE_CREATED=true
else
    echo -e "${RED}❌ ERRO: HTTP $http_code${NC}"
    echo "$body"
    INSTANCE_CREATED=false
fi
echo ""

# 4. Testar Connect (obter QR Code)
if [ "$INSTANCE_CREATED" = true ]; then
    echo -e "${YELLOW}[4/5] Testando GET /instance/connect/$TEST_INSTANCE_NAME...${NC}"
    sleep 2  # Aguardar instância inicializar
    response=$(curl -s -w "\n%{http_code}" \
      -H "apikey: $EVOLUTION_API_KEY" \
      "$EVOLUTION_API_URL/instance/connect/$TEST_INSTANCE_NAME")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 201 ]; then
        echo -e "${GREEN}✅ Connect/QR Code OK${NC}"
        # Verificar se tem base64 ou qrcode no response
        if echo "$body" | grep -q "base64\|qrcode\|code"; then
            echo "QR Code encontrado no response!"
        fi
        echo "$body" | python3 -m json.tool 2>/dev/null | head -20 || echo "$body" | head -20
    else
        echo -e "${RED}❌ ERRO: HTTP $http_code${NC}"
        echo "$body"
    fi
    echo ""
fi

# 5. Deletar instância de teste
if [ "$INSTANCE_CREATED" = true ]; then
    echo -e "${YELLOW}[5/5] Limpando: DELETE /instance/delete/$TEST_INSTANCE_NAME...${NC}"
    response=$(curl -s -w "\n%{http_code}" \
      -X DELETE \
      -H "apikey: $EVOLUTION_API_KEY" \
      "$EVOLUTION_API_URL/instance/delete/$TEST_INSTANCE_NAME")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 201 ]; then
        echo -e "${GREEN}✅ Delete Instance OK${NC}"
    else
        echo -e "${RED}❌ ERRO: HTTP $http_code${NC}"
        echo "$body"
    fi
    echo ""
fi

echo "=========================================="
echo "TESTES CONCLUÍDOS"
echo "=========================================="
echo ""
echo "Próximos passos:"
echo "1. Se todos os testes passaram, a Evolution API v2.3.6 está funcionando!"
echo "2. Agora teste criar uma instância real pelo frontend"
echo "3. Conecte seu WhatsApp e envie uma mensagem de teste"
echo "4. Verifique se a mensagem aparece no dashboard do agente"
echo "=========================================="
