#!/bin/bash

# Script de Health Check para Deploy
# Verifica se todos os serviços essenciais estão funcionando

set -e

echo "🔍 Verificando saúde do sistema..."

# 1. Verificar Backend
echo -n "Backend... "
BACKEND_STATUS=$(curl -s http://localhost:8001/api/health | jq -r '.status' 2>/dev/null || echo "error")
if [ "$BACKEND_STATUS" = "healthy" ]; then
    echo "✅"
else
    echo "❌ FALHOU"
    exit 1
fi

# 2. Verificar MongoDB
echo -n "MongoDB... "
MONGO_STATUS=$(mongosh mongodb://localhost:27017/admin --quiet --eval "db.runCommand({ ping: 1 }).ok" 2>/dev/null || echo "0")
if [ "$MONGO_STATUS" = "1" ]; then
    echo "✅"
else
    echo "❌ FALHOU"
    exit 1
fi

# 3. Verificar Frontend (se está servindo)
echo -n "Frontend... "
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo "✅"
else
    echo "❌ FALHOU (código: $FRONTEND_STATUS)"
    exit 1
fi

# 4. Verificar dados persistentes
echo -n "Dados persistentes... "
if [ -d "/data/db" ] && [ -d "/data/uploads" ]; then
    echo "✅"
else
    echo "❌ FALHOU"
    exit 1
fi

echo ""
echo "✅ Todos os serviços estão saudáveis!"
exit 0
