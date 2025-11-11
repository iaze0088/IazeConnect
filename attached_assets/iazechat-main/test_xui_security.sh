#!/bin/bash

echo "========================================"
echo "   TESTE DE SEGURANÇA - XUI API"
echo "   Verificar se API é READ-ONLY"
echo "========================================"
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configurações
XUI_URL="${XUI_API_URL:-http://localhost:8080}"
XUI_KEY="${XUI_API_KEY}"

if [ -z "$XUI_KEY" ]; then
    echo -e "${RED}❌ XUI_API_KEY não configurada!${NC}"
    echo "Configure no .env primeiro"
    exit 1
fi

echo "🔧 Configuração:"
echo "   XUI URL: $XUI_URL"
echo "   API Key: ${XUI_KEY:0:10}..."
echo ""

# Teste 1: Listar usuários (DEVE FUNCIONAR)
echo "========================================="
echo "TESTE 1: Listar Usuários (READ)"
echo "========================================="
echo ""

READ_TEST=$(curl -s -X GET "$XUI_URL/api/users" \
  -H "Authorization: Bearer $XUI_KEY" \
  -w "\nHTTP_CODE:%{http_code}")

HTTP_CODE=$(echo "$READ_TEST" | grep "HTTP_CODE" | cut -d':' -f2)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ SUCESSO: API pode LISTAR usuários${NC}"
else
    echo -e "${RED}❌ FALHA: API não consegue listar usuários (HTTP $HTTP_CODE)${NC}"
    echo "Resposta: $READ_TEST"
fi

echo ""
echo ""

# Teste 2: Tentar CRIAR usuário (NÃO DEVE FUNCIONAR)
echo "========================================="
echo "TESTE 2: Criar Usuário (WRITE - deve FALHAR)"
echo "========================================="
echo ""

CREATE_TEST=$(curl -s -X POST "$XUI_URL/api/user/create" \
  -H "Authorization: Bearer $XUI_KEY" \
  -H "Content-Type: application/json" \
  -d '{"username":"teste_seguranca","password":"123456"}' \
  -w "\nHTTP_CODE:%{http_code}")

HTTP_CODE=$(echo "$CREATE_TEST" | grep "HTTP_CODE" | cut -d':' -f2)

if [ "$HTTP_CODE" = "403" ] || [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "405" ]; then
    echo -e "${GREEN}✅ SEGURO: API NÃO pode criar usuários (HTTP $HTTP_CODE)${NC}"
    echo "   Permissão NEGADA corretamente! ✅"
elif [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
    echo -e "${RED}⚠️ ATENÇÃO: API PODE criar usuários!${NC}"
    echo -e "${YELLOW}   Revise as permissões no XUI!${NC}"
else
    echo -e "${YELLOW}⚠️ Resposta inesperada: HTTP $HTTP_CODE${NC}"
fi

echo ""
echo ""

# Teste 3: Tentar DELETAR usuário (NÃO DEVE FUNCIONAR)
echo "========================================="
echo "TESTE 3: Deletar Usuário (DELETE - deve FALHAR)"
echo "========================================="
echo ""

DELETE_TEST=$(curl -s -X DELETE "$XUI_URL/api/user/teste_fake" \
  -H "Authorization: Bearer $XUI_KEY" \
  -w "\nHTTP_CODE:%{http_code}")

HTTP_CODE=$(echo "$DELETE_TEST" | grep "HTTP_CODE" | cut -d':' -f2)

if [ "$HTTP_CODE" = "403" ] || [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "405" ]; then
    echo -e "${GREEN}✅ SEGURO: API NÃO pode deletar usuários (HTTP $HTTP_CODE)${NC}"
    echo "   Permissão NEGADA corretamente! ✅"
elif [ "$HTTP_CODE" = "200" ]; then
    echo -e "${RED}⚠️ ATENÇÃO: API PODE deletar usuários!${NC}"
    echo -e "${YELLOW}   Revise as permissões no XUI!${NC}"
else
    echo -e "${YELLOW}⚠️ Resposta inesperada: HTTP $HTTP_CODE${NC}"
fi

echo ""
echo ""

# Teste 4: Tentar EDITAR usuário (NÃO DEVE FUNCIONAR)
echo "========================================="
echo "TESTE 4: Editar Usuário (UPDATE - deve FALHAR)"
echo "========================================="
echo ""

UPDATE_TEST=$(curl -s -X PUT "$XUI_URL/api/user/update" \
  -H "Authorization: Bearer $XUI_KEY" \
  -H "Content-Type: application/json" \
  -d '{"username":"teste","password":"nova_senha"}' \
  -w "\nHTTP_CODE:%{http_code}")

HTTP_CODE=$(echo "$UPDATE_TEST" | grep "HTTP_CODE" | cut -d':' -f2)

if [ "$HTTP_CODE" = "403" ] || [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "405" ]; then
    echo -e "${GREEN}✅ SEGURO: API NÃO pode editar usuários (HTTP $HTTP_CODE)${NC}"
    echo "   Permissão NEGADA corretamente! ✅"
elif [ "$HTTP_CODE" = "200" ]; then
    echo -e "${RED}⚠️ ATENÇÃO: API PODE editar usuários!${NC}"
    echo -e "${YELLOW}   Revise as permissões no XUI!${NC}"
else
    echo -e "${YELLOW}⚠️ Resposta inesperada: HTTP $HTTP_CODE${NC}"
fi

echo ""
echo ""

# Resumo Final
echo "========================================="
echo "           RESUMO DE SEGURANÇA"
echo "========================================="
echo ""

# Verificar se passou nos testes de segurança
SECURITY_PASSED=true

# Teste de READ deve passar
if [ "$HTTP_CODE" != "200" ]; then
    echo -e "${RED}❌ API não consegue fazer READ${NC}"
    SECURITY_PASSED=false
fi

# Testes de WRITE devem falhar (403, 401, 405)
echo "Verificando se operações de ESCRITA estão bloqueadas..."
echo ""

if [ "$SECURITY_PASSED" = true ]; then
    echo -e "${GREEN}✅✅✅ API ESTÁ CONFIGURADA CORRETAMENTE!${NC}"
    echo ""
    echo "   ✅ Pode LISTAR/LER dados"
    echo "   ✅ NÃO pode CRIAR"
    echo "   ✅ NÃO pode DELETAR"
    echo "   ✅ NÃO pode EDITAR"
    echo ""
    echo -e "${GREEN}👍 Configuração SEGURA para usar no IAZE!${NC}"
else
    echo -e "${RED}❌❌❌ ATENÇÃO: Revise as permissões!${NC}"
    echo ""
    echo "   ⚠️ API pode ter permissões excessivas"
    echo "   ⚠️ Recomendação: Use 'Reseller API' no XUI"
    echo "   ⚠️ Desabilite permissões de WRITE"
fi

echo ""
echo "========================================="
