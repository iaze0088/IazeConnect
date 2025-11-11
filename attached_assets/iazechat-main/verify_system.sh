#!/bin/bash

# Script de Verificação Completa do Sistema
# Execute: bash /app/verify_system.sh

echo "=================================================="
echo "🔍 VERIFICAÇÃO COMPLETA DO SISTEMA CYBERTV"
echo "=================================================="
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Função para verificação
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
        ((ERRORS++))
    fi
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

# 1. BANCO DE DADOS
echo "1️⃣  VERIFICANDO BANCO DE DADOS"
echo "--------------------------------------------------"

python3 << 'EOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys

async def check_db():
    try:
        client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
        db = client[os.environ.get('DB_NAME', 'support_chat')]
        
        resellers = await db.resellers.count_documents({})
        agents = await db.agents.count_documents({})
        tickets = await db.tickets.count_documents({})
        
        print(f"   Revendas: {resellers}")
        print(f"   Agents: {agents}")
        print(f"   Tickets: {tickets}")
        
        if agents == 0:
            sys.exit(1)
        sys.exit(0)
    except Exception as e:
        print(f"   Erro: {e}")
        sys.exit(1)

asyncio.run(check_db())
EOF

check "Banco de dados acessível e com dados"
echo ""

# 2. BACKEND
echo "2️⃣  VERIFICANDO BACKEND"
echo "--------------------------------------------------"

# 2.1 Serviço rodando
sudo supervisorctl status backend | grep RUNNING > /dev/null
check "Backend está rodando"

# 2.2 Login admin
ADMIN_RESPONSE=$(curl -s -X POST http://localhost:8001/api/auth/admin/login \
  -H "Content-Type: application/json" \
  -d '{"password":"102030@ab"}')

echo "$ADMIN_RESPONSE" | grep -q "token"
check "Login de admin funciona"

# 2.3 Login agent
AGENT_RESPONSE=$(curl -s -X POST http://localhost:8001/api/auth/agent/login \
  -H "Content-Type: application/json" \
  -d '{"login":"fabioteste","password":"123"}')

echo "$AGENT_RESPONSE" | grep -q "token"
check "Login de agent funciona"

# 2.4 Filtro multi-tenant
python3 << 'EOF'
import requests
import sys

try:
    # Login
    response = requests.post("http://localhost:8001/api/auth/agent/login",
        json={"login": "fabioteste", "password": "123"}, timeout=5)
    
    if response.status_code != 200:
        sys.exit(1)
    
    token = response.json()['token']
    
    # Buscar tickets
    tickets_response = requests.get("http://localhost:8001/api/tickets",
        headers={"Authorization": f"Bearer {token}"}, timeout=5)
    
    if tickets_response.status_code != 200:
        sys.exit(1)
    
    tickets = tickets_response.json()
    print(f"   Tickets retornados: {len(tickets)}")
    
    sys.exit(0)
except Exception as e:
    print(f"   Erro: {e}")
    sys.exit(1)
EOF

check "Filtro multi-tenant funcionando"
echo ""

# 3. FRONTEND
echo "3️⃣  VERIFICANDO FRONTEND"
echo "--------------------------------------------------"

# 3.1 Serviço rodando
sudo supervisorctl status frontend | grep RUNNING > /dev/null
check "Frontend está rodando"

# 3.2 Build existe
if [ -d "/app/frontend/build" ]; then
    check "Build do frontend existe"
else
    warn "Build do frontend não encontrado"
fi

# 3.3 .env existe
if [ -f "/app/frontend/.env" ]; then
    check "Arquivo .env do frontend existe"
else
    warn "Arquivo .env do frontend não encontrado"
fi

echo ""

# 4. ARQUIVOS CRÍTICOS
echo "4️⃣  VERIFICANDO ARQUIVOS CRÍTICOS"
echo "--------------------------------------------------"

[ -f "/app/backend/server.py" ]
check "server.py existe"

[ -f "/app/backend/tenant_helpers.py" ]
check "tenant_helpers.py existe"

[ -f "/app/backend/.env" ]
check ".env do backend existe"

echo ""

# 5. LOGS
echo "5️⃣  VERIFICANDO LOGS (últimos erros)"
echo "--------------------------------------------------"

ERROR_COUNT=$(tail -100 /var/log/supervisor/backend.err.log 2>/dev/null | grep -i "error\|exception" | wc -l)

if [ "$ERROR_COUNT" -eq 0 ]; then
    check "Sem erros recentes no backend"
else
    warn "Encontrados $ERROR_COUNT erros no log do backend"
fi

echo ""

# 6. SUMMARY
echo "=================================================="
echo "📊 RESUMO DA VERIFICAÇÃO"
echo "=================================================="
echo ""

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ SISTEMA OK! Nenhum erro crítico encontrado.${NC}"
else
    echo -e "${RED}❌ SISTEMA COM PROBLEMAS! $ERRORS erro(s) encontrado(s).${NC}"
fi

if [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  $WARNINGS aviso(s) encontrado(s).${NC}"
fi

echo ""
echo "Para mais detalhes, veja: /app/CHECKLIST_DEPLOY_COMPLETO.md"
echo ""

exit $ERRORS
