#!/bin/bash
###############################################################################
# DEPLOY RÁPIDO - APENAS BOTÕES /VENDAS
# VPS: 151.243.218.223 (suporte.help)
# Atualiza apenas os arquivos modificados para fix dos botões
###############################################################################

echo "🚀 Deploy: Botões em /vendas para suporte.help"
echo "================================================"
echo ""

# Verificar conexão
echo "📡 Verificando conexão com VPS..."
if ! ping -c 1 151.243.218.223 &> /dev/null; then
    echo "❌ Não foi possível conectar ao VPS"
    exit 1
fi
echo "✅ VPS acessível"
echo ""

# Arquivos que foram modificados
echo "📦 Arquivos a serem enviados:"
echo "  - backend/vendas_routes_new.py (endpoint /config)"
echo "  - frontend/src/pages/VendasChatNew.js (busca config)"
echo ""

# Criar diretório temporário
TEMP_DIR="/tmp/deploy_botoes_$(date +%s)"
mkdir -p $TEMP_DIR

# Copiar arquivos modificados
echo "📋 Preparando arquivos..."
cp /app/backend/vendas_routes_new.py $TEMP_DIR/
cp /app/frontend/src/pages/VendasChatNew.js $TEMP_DIR/

# Mostrar resumo
echo "✅ Arquivos preparados em: $TEMP_DIR"
echo ""
echo "📤 PRÓXIMOS PASSOS MANUAIS:"
echo ""
echo "1️⃣ Conecte ao VPS:"
echo "   ssh root@151.243.218.223"
echo ""
echo "2️⃣ Navegue até o diretório do projeto:"
echo "   cd /app"
echo ""
echo "3️⃣ Copie os arquivos (de outro terminal):"
echo "   scp $TEMP_DIR/vendas_routes_new.py root@151.243.218.223:/app/backend/"
echo "   scp $TEMP_DIR/VendasChatNew.js root@151.243.218.223:/app/frontend/src/pages/"
echo ""
echo "4️⃣ No VPS, rebuild o frontend:"
echo "   cd /app/frontend && yarn build"
echo ""
echo "5️⃣ Reinicie os serviços:"
echo "   supervisorctl restart backend"
echo "   supervisorctl restart frontend"
echo ""
echo "6️⃣ Teste:"
echo "   curl https://suporte.help/api/vendas/config"
echo ""
echo "================================================"
echo ""
echo "⚠️  ALTERNATIVA: Deploy Completo"
echo "Se preferir fazer deploy completo do projeto:"
echo "   1. Faça 'Save to GitHub' aqui no Emergent"
echo "   2. No VPS: cd /app && git pull"
echo "   3. No VPS: cd frontend && yarn build"
echo "   4. No VPS: supervisorctl restart all"
echo ""
