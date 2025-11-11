#!/bin/bash

echo "========================================"
echo "   TESTE DE INTEGRAÇÃO XUI + IAZE"
echo "========================================"
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Ler credenciais IAZE
read -p "Digite seu email IAZE: " EMAIL
read -sp "Digite sua senha IAZE: " PASSWORD
echo ""
echo ""

# Backend URL
BACKEND_URL="${REACT_APP_BACKEND_URL:-http://localhost:8001}"

echo "🔐 Fazendo login no IAZE..."
LOGIN_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Erro no login!${NC}"
    echo "Resposta: $LOGIN_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✅ Login realizado com sucesso!${NC}"
echo ""

# Teste 1: Verificar conexão com XUI
echo "========================================="
echo "TESTE 1: Verificar Conexão com XUI"
echo "========================================="
echo ""

CONNECTION_TEST=$(curl -s -X GET "$BACKEND_URL/api/xui/check-connection" \
  -H "Authorization: Bearer $TOKEN")

echo "📥 Resposta:"
echo "$CONNECTION_TEST" | python3 -m json.tool 2>/dev/null || echo "$CONNECTION_TEST"
echo ""

if echo "$CONNECTION_TEST" | grep -q '"connected":true'; then
    echo -e "${GREEN}✅ Conexão com XUI está funcionando!${NC}"
else
    echo -e "${RED}❌ Falha na conexão com XUI!${NC}"
    echo -e "${YELLOW}⚠️ Verifique as configurações no .env:${NC}"
    echo "   - XUI_API_URL"
    echo "   - XUI_API_KEY ou XUI_USERNAME/PASSWORD"
    exit 1
fi

echo ""
echo ""

# Teste 2: Buscar usuário específico
echo "========================================="
echo "TESTE 2: Buscar Usuário Específico"
echo "========================================="
echo ""

read -p "Digite o username para buscar no XUI: " USERNAME

if [ -z "$USERNAME" ]; then
    echo -e "${YELLOW}⚠️ Teste 2 pulado (nenhum username fornecido)${NC}"
else
    echo "🔍 Buscando usuário: $USERNAME"
    echo ""
    
    USER_SEARCH=$(curl -s -X GET "$BACKEND_URL/api/xui/search-user/$USERNAME" \
      -H "Authorization: Bearer $TOKEN")
    
    echo "📥 Resposta:"
    echo "$USER_SEARCH" | python3 -m json.tool 2>/dev/null || echo "$USER_SEARCH"
    echo ""
    
    if echo "$USER_SEARCH" | grep -q '"success":true'; then
        echo -e "${GREEN}✅ Usuário encontrado com sucesso!${NC}"
        
        # Extrair dados
        USERNAME_FOUND=$(echo "$USER_SEARCH" | grep -o '"username":"[^"]*' | cut -d'"' -f4)
        PASSWORD_FOUND=$(echo "$USER_SEARCH" | grep -o '"password":"[^"]*' | cut -d'"' -f4)
        EXPIRATION=$(echo "$USER_SEARCH" | grep -o '"expiration_date":"[^"]*' | cut -d'"' -f4)
        
        echo ""
        echo "📊 Dados encontrados:"
        echo "   👤 Usuário: $USERNAME_FOUND"
        echo "   🔑 Senha: $PASSWORD_FOUND"
        echo "   📅 Vencimento: $EXPIRATION"
    else
        echo -e "${RED}❌ Usuário não encontrado ou erro na busca${NC}"
    fi
fi

echo ""
echo ""

# Teste 3: Buscar por palavra-chave
echo "========================================="
echo "TESTE 3: Buscar por Palavra-Chave"
echo "========================================="
echo ""

read -p "Digite uma palavra-chave para buscar (ex: telefone, nome): " KEYWORD

if [ -z "$KEYWORD" ]; then
    echo -e "${YELLOW}⚠️ Teste 3 pulado (nenhuma keyword fornecida)${NC}"
else
    echo "🔍 Buscando com keyword: $KEYWORD"
    echo ""
    
    KEYWORD_SEARCH=$(curl -s -X POST "$BACKEND_URL/api/xui/search-users" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"keyword\":\"$KEYWORD\"}")
    
    echo "📥 Resposta:"
    echo "$KEYWORD_SEARCH" | python3 -m json.tool 2>/dev/null || echo "$KEYWORD_SEARCH"
    echo ""
    
    USER_COUNT=$(echo "$KEYWORD_SEARCH" | grep -o '"count":[0-9]*' | cut -d':' -f2)
    
    if [ ! -z "$USER_COUNT" ] && [ "$USER_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✅ Encontrados $USER_COUNT usuário(s)!${NC}"
    else
        echo -e "${YELLOW}⚠️ Nenhum usuário encontrado com essa keyword${NC}"
    fi
fi

echo ""
echo ""

# Resumo final
echo "========================================="
echo "           RESUMO DOS TESTES"
echo "========================================="
echo ""

if echo "$CONNECTION_TEST" | grep -q '"connected":true'; then
    echo -e "${GREEN}✅ Conexão XUI: OK${NC}"
else
    echo -e "${RED}❌ Conexão XUI: FALHA${NC}"
fi

if [ ! -z "$USERNAME_FOUND" ]; then
    echo -e "${GREEN}✅ Busca por Username: OK${NC}"
elif [ ! -z "$USERNAME" ]; then
    echo -e "${RED}❌ Busca por Username: FALHA${NC}"
else
    echo -e "${YELLOW}⏭️  Busca por Username: PULADO${NC}"
fi

if [ ! -z "$USER_COUNT" ]; then
    echo -e "${GREEN}✅ Busca por Keyword: OK${NC}"
elif [ ! -z "$KEYWORD" ]; then
    echo -e "${RED}❌ Busca por Keyword: FALHA${NC}"
else
    echo -e "${YELLOW}⏭️  Busca por Keyword: PULADO${NC}"
fi

echo ""
echo "========================================="
echo "✅ Testes concluídos!"
echo "========================================="
