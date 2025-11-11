#!/bin/bash
# Script completo para sincronizar arquivos de vendas da Emergent para servidor externo
# Execute no servidor: 198.96.94.106

set -e

EMERGENT_URL="https://wppconnect-fix.preview.emergentagent.com"
BACKEND_PATH="/opt/iaze/backend"

echo "========================================="
echo "  SINCRONIZACAO VENDAS: Emergent -> Servidor"
echo "========================================="
echo ""

# 1. Fazer backup
echo "[1/6] Fazendo backup..."
mkdir -p /tmp/vendas_backup_$(date +%Y%m%d_%H%M%S)
cp ${BACKEND_PATH}/vendas*.py /tmp/vendas_backup_$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || true
echo "✓ Backup completo"

# 2. Baixar arquivos da Emergent
echo ""
echo "[2/6] Baixando arquivos da Emergent..."
cd ${BACKEND_PATH}

curl -f -o vendas_routes.py "${EMERGENT_URL}/api/download/vendas_routes.py"
curl -f -o vendas_ai_service.py "${EMERGENT_URL}/api/download/vendas_ai_service.py"
curl -f -o vendas_bot_service.py "${EMERGENT_URL}/api/download/vendas_bot_service.py"
curl -f -o vendas_models.py "${EMERGENT_URL}/api/download/vendas_models.py"
curl -f -o vendas_bot_config_models.py "${EMERGENT_URL}/api/download/vendas_bot_config_models.py"

echo "✓ Arquivos baixados"

# 3. Verificar tamanho dos arquivos
echo ""
echo "[3/6] Verificando arquivos..."
for file in vendas_routes.py vendas_ai_service.py vendas_bot_service.py vendas_models.py vendas_bot_config_models.py; do
    size=$(stat -c%s "$file")
    if [ $size -lt 100 ]; then
        echo "✗ Erro: $file muito pequeno ($size bytes)"
        exit 1
    fi
    echo "✓ $file: $size bytes"
done

# 4. Copiar para o container
echo ""
echo "[4/6] Copiando para container..."
docker cp vendas_routes.py iaze_backend:/app/backend/
docker cp vendas_ai_service.py iaze_backend:/app/backend/
docker cp vendas_bot_service.py iaze_backend:/app/backend/
docker cp vendas_models.py iaze_backend:/app/backend/
docker cp vendas_bot_config_models.py iaze_backend:/app/backend/
docker cp vendas_bot_config_routes.py iaze_backend:/app/backend/ 2>/dev/null || true
docker cp vendas_simple_config_routes.py iaze_backend:/app/backend/ 2>/dev/null || true
echo "✓ Arquivos copiados"

# 5. Reiniciar backend
echo ""
echo "[5/6] Reiniciando backend..."
cd /opt/iaze
docker-compose restart backend
sleep 15
echo "✓ Backend reiniciado"

# 6. Testar
echo ""
echo "[6/6] Testando rotas de vendas..."
response=$(curl -s -X POST http://localhost:8001/api/vendas/start -H "Content-Type: application/json" -d '{}')

if echo "$response" | grep -q "session_id"; then
    echo "✓ Rotas de vendas funcionando!"
    echo ""
    echo "========================================="
    echo "  SINCRONIZACAO COMPLETA COM SUCESSO!"
    echo "========================================="
    echo ""
    echo "Teste no navegador: http://198.96.94.106:3000/vendas"
else
    echo "✗ Erro: rotas não estão respondendo"
    echo "Response: $response"
    echo ""
    echo "Verificando logs..."
    docker-compose logs --tail=20 backend | grep -i "vendas\|error"
    exit 1
fi
