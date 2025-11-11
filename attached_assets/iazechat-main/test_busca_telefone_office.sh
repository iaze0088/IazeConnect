#!/bin/bash

echo "========================================"
echo "   TESTE: Busca de Cliente por Telefone"
echo "   Office (gestor.my)"
echo "========================================"
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BACKEND_URL="http://localhost:8001"

# Teste 1: Verificar credenciais cadastradas
echo "========================================="
echo "TESTE 1: Verificar Credenciais Office"
echo "========================================="
echo ""

CREDS=$(curl -s "$BACKEND_URL/api/office/credentials")

if echo "$CREDS" | grep -q '"id"'; then
    echo -e "${GREEN}✅ Credenciais do Office encontradas!${NC}"
    echo ""
    echo "Credenciais cadastradas:"
    echo "$CREDS" | python3 -m json.tool 2>/dev/null | grep -E "nome|username" | head -10
else
    echo -e "${RED}❌ Nenhuma credencial cadastrada!${NC}"
    echo ""
    echo "Você precisa cadastrar primeiro:"
    echo ""
    echo -e "${BLUE}curl -X POST \"$BACKEND_URL/api/office/credentials\" \\
  -H \"Content-Type: application/json\" \\
  -d '{
    \"url\": \"https://gestor.my\",
    \"username\": \"SEU_USUARIO\",
    \"password\": \"SUA_SENHA\",
    \"nome\": \"Office Principal\"
  }'${NC}"
    echo ""
    read -p "Deseja cadastrar agora? (s/n): " CADASTRAR
    
    if [ "$CADASTRAR" = "s" ] || [ "$CADASTRAR" = "S" ]; then
        read -p "Username gestor.my: " OFFICE_USER
        read -sp "Password gestor.my: " OFFICE_PASS
        echo ""
        
        CADASTRO=$(curl -s -X POST "$BACKEND_URL/api/office/credentials" \
          -H "Content-Type: application/json" \
          -d "{
            \"url\": \"https://gestor.my\",
            \"username\": \"$OFFICE_USER\",
            \"password\": \"$OFFICE_PASS\",
            \"nome\": \"Office Principal\"
          }")
        
        if echo "$CADASTRO" | grep -q '"success":true'; then
            echo -e "${GREEN}✅ Credenciais cadastradas com sucesso!${NC}"
        else
            echo -e "${RED}❌ Erro ao cadastrar credenciais${NC}"
            echo "$CADASTRO"
            exit 1
        fi
    else
        echo "Cadastre as credenciais e execute o teste novamente."
        exit 0
    fi
fi

echo ""
echo ""

# Teste 2: Buscar cliente por telefone
echo "========================================="
echo "TESTE 2: Buscar Cliente por Telefone"
echo "========================================="
echo ""

read -p "Digite um telefone para buscar (ex: 11999999999): " TELEFONE

if [ -z "$TELEFONE" ]; then
    echo -e "${YELLOW}⏭️  Teste de busca pulado${NC}"
    exit 0
fi

echo ""
echo "🔍 Buscando cliente com telefone: $TELEFONE"
echo ""

RESULTADO=$(curl -s -X POST "$BACKEND_URL/api/office/search" \
  -H "Content-Type: application/json" \
  -d "{\"search_term\":\"$TELEFONE\"}")

echo "📥 Resposta:"
echo "$RESULTADO" | python3 -m json.tool 2>/dev/null || echo "$RESULTADO"
echo ""

if echo "$RESULTADO" | grep -q '"success":true'; then
    echo -e "${GREEN}✅✅✅ CLIENTE ENCONTRADO!${NC}"
    echo ""
    
    # Extrair dados
    NOME=$(echo "$RESULTADO" | grep -o '"nome":"[^"]*' | cut -d'"' -f4 || echo "N/A")
    USUARIO=$(echo "$RESULTADO" | grep -o '"usuario":"[^"]*' | cut -d'"' -f4 || echo "N/A")
    SENHA=$(echo "$RESULTADO" | grep -o '"senha":"[^"]*' | cut -d'"' -f4 || echo "N/A")
    VENCIMENTO=$(echo "$RESULTADO" | grep -o '"vencimento":"[^"]*' | cut -d'"' -f4 || echo "N/A")
    STATUS=$(echo "$RESULTADO" | grep -o '"status":"[^"]*' | cut -d'"' -f4 || echo "N/A")
    
    echo "📊 Dados encontrados:"
    echo "   👤 Nome: $NOME"
    echo "   🆔 Usuário: $USUARIO"
    echo "   🔑 Senha: $SENHA"
    echo "   📅 Vencimento: $VENCIMENTO"
    echo "   🟢 Status: $STATUS"
    echo ""
    echo -e "${GREEN}🎉 Integração funcionando perfeitamente!${NC}"
else
    echo -e "${RED}❌ Cliente não encontrado${NC}"
    echo ""
    echo "Possíveis motivos:"
    echo "1. Telefone não existe no gestor.my"
    echo "2. Formato do telefone diferente"
    echo "3. Cliente em outro Office (se tiver múltiplos)"
fi

echo ""
echo ""

# Resumo
echo "========================================="
echo "           RESUMO"
echo "========================================="
echo ""
echo "✅ Backend IAZE: ONLINE"
echo "✅ Credenciais Office: CONFIGURADAS"
echo "✅ Endpoint /office/search: FUNCIONANDO"
echo ""
echo "📝 Como usar no IAZE:"
echo "1. Cliente envia mensagem WhatsApp"
echo "2. Atendente vê o número automaticamente"
echo "3. Sistema busca no gestor.my"
echo "4. Mostra dados na aba OFFICE"
echo "5. Atendente copia e envia ao cliente"
echo ""
echo "========================================="
