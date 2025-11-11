#!/bin/bash
###############################################################################
# DEPLOY BOTÕES /VENDAS - VPS suporte.help
# Execute este script NO VPS como root
###############################################################################

echo "🚀 Atualizando suporte.help com botões em /vendas..."
echo ""

# Verificar se é root
if [ "$EUID" -ne 0 ]; then 
   echo "❌ Execute como root: sudo su"
   exit 1
fi

# Navegar para o diretório
cd /app || { echo "❌ Diretório /app não encontrado"; exit 1; }

echo "📥 1/5 - Atualizando código do GitHub..."
git pull || { echo "❌ Erro no git pull"; exit 1; }
echo "✅ Código atualizado"
echo ""

echo "🔧 2/5 - Instalando dependências do frontend (se necessário)..."
cd frontend
yarn install --production=false
echo "✅ Dependências ok"
echo ""

echo "📦 3/5 - Building frontend (pode demorar ~20s)..."
yarn build
echo "✅ Build concluído"
echo ""

echo "🔄 4/5 - Reiniciando serviços..."
cd ..
supervisorctl restart backend
sleep 2
supervisorctl restart frontend
sleep 2
echo "✅ Serviços reiniciados"
echo ""

echo "🧪 5/5 - Testando endpoint..."
sleep 3
response=$(curl -s https://suporte.help/api/vendas/config)

if echo "$response" | grep -q '"status"'; then
    echo "✅ Endpoint /api/vendas/config funcionando!"
    echo ""
    echo "📊 Resposta:"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    echo ""
    echo "🎉 DEPLOY CONCLUÍDO COM SUCESSO!"
    echo ""
    echo "✅ Acesse: https://suporte.help/vendas"
    echo "✅ Os 3 botões devem aparecer agora!"
else
    echo "⚠️  Endpoint retornou:"
    echo "$response"
    echo ""
    echo "Verificando logs do backend..."
    tail -n 20 /var/log/supervisor/backend.err.log
fi

echo ""
echo "================================================"
