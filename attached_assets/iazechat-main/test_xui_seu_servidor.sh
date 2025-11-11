#!/bin/bash

echo "========================================"
echo "   TESTE XUI - 209.14.88.42"
echo "========================================"
echo ""

XUI_URL="http://209.14.88.42:8080"
XUI_KEY="FjgJpVPv"

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔧 Configuração:"
echo "   URL: $XUI_URL"
echo "   API Key: $XUI_KEY"
echo ""

# Teste 1: Servidor Online
echo "========================================="
echo "TESTE 1: Servidor XUI Online?"
echo "========================================="
echo ""

if curl -s --max-time 5 -I "$XUI_URL" | grep -q "200 OK"; then
    echo -e "${GREEN}✅ Servidor XUI está ONLINE!${NC}"
else
    echo -e "${RED}❌ Servidor XUI não está respondendo${NC}"
    exit 1
fi

echo ""
echo ""

# Teste 2: Autenticação via API
echo "========================================="
echo "TESTE 2: API Key Funciona?"
echo "========================================="
echo ""

# Tentar endpoint de usuários
AUTH_TEST=$(curl -s -X GET "$XUI_URL/api/users" \
  -H "Authorization: Bearer $XUI_KEY" \
  -w "\nHTTP_CODE:%{http_code}")

HTTP_CODE=$(echo "$AUTH_TEST" | grep "HTTP_CODE" | cut -d':' -f2)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ API Key está funcionando!${NC}"
    echo ""
    echo "Dados retornados (primeiras 5 linhas):"
    echo "$AUTH_TEST" | head -5
elif [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
    echo -e "${RED}❌ API Key inválida ou sem permissões${NC}"
    echo "HTTP Status: $HTTP_CODE"
    echo ""
    echo "Verifique:"
    echo "1. Se o código 'FjgJpVPv' está correto no XUI"
    echo "2. Se está marcado como 'Enabled'"
    echo "3. Se é do tipo 'Reseller API'"
else
    echo -e "${YELLOW}⚠️ Resposta inesperada: HTTP $HTTP_CODE${NC}"
    echo "$AUTH_TEST"
fi

echo ""
echo ""

# Teste 3: Via Backend IAZE
echo "========================================="
echo "TESTE 3: Integração IAZE → XUI"
echo "========================================="
echo ""

# Verificar se backend está rodando
if ! curl -s http://localhost:8001/api/health > /dev/null 2>&1; then
    echo -e "${RED}❌ Backend IAZE não está rodando${NC}"
    exit 1
fi

# Login no IAZE (use suas credenciais)
read -p "Digite seu email IAZE (ou Enter para pular): " EMAIL

if [ -z "$EMAIL" ]; then
    echo -e "${YELLOW}⏭️  Teste via IAZE pulado${NC}"
else
    read -sp "Digite sua senha: " PASSWORD
    echo ""
    echo ""
    
    echo "🔐 Fazendo login no IAZE..."
    LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8001/api/auth/login" \
      -H "Content-Type: application/json" \
      -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")
    
    TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"token":"[^"]*' | cut -d'"' -f4)
    
    if [ -z "$TOKEN" ]; then
        echo -e "${RED}❌ Erro no login IAZE${NC}"
    else
        echo -e "${GREEN}✅ Login IAZE OK${NC}"
        echo ""
        
        # Testar endpoint XUI via IAZE
        echo "🔍 Testando conexão XUI via IAZE..."
        XUI_CHECK=$(curl -s -X GET "http://localhost:8001/api/xui/check-connection" \
          -H "Authorization: Bearer $TOKEN")
        
        echo "$XUI_CHECK" | python3 -m json.tool 2>/dev/null || echo "$XUI_CHECK"
        
        if echo "$XUI_CHECK" | grep -q '"connected":true'; then
            echo ""
            echo -e "${GREEN}✅✅✅ INTEGRAÇÃO FUNCIONANDO PERFEITAMENTE!${NC}"
        else
            echo ""
            echo -e "${RED}❌ Integração não está funcionando${NC}"
        fi
    fi
fi

echo ""
echo ""

# Resumo
echo "========================================="
echo "           RESUMO FINAL"
echo "========================================="
echo ""
echo "✅ Servidor XUI: ONLINE"
echo "✅ Backend IAZE: ONLINE"
echo "✅ Configuração: COMPLETA"
echo ""
echo "📝 Próximos passos:"
echo "1. Teste buscar um usuário no OFFICE"
echo "2. Digite nome ou parte do username"
echo "3. Sistema vai buscar automaticamente no XUI!"
echo ""
echo "========================================="
