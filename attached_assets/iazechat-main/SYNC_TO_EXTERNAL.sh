#!/bin/bash

# ========================================
# SCRIPT DE SINCRONIZAÇÃO EMERGENT → SERVIDOR EXTERNO
# ========================================

EXTERNAL_SERVER="198.96.94.106"
EXTERNAL_USER="root"
EXTERNAL_PASSWORD="102030ab"
EXTERNAL_PATH="/opt/iaze"

echo "🚀 INICIANDO SINCRONIZAÇÃO PARA SERVIDOR EXTERNO"
echo "================================================"
echo ""

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Instalar sshpass se não existir
if ! command -v sshpass &> /dev/null; then
    echo "📦 Instalando sshpass..."
    apt-get update && apt-get install -y sshpass
fi

# Função para executar comandos no servidor externo
remote_exec() {
    sshpass -p "$EXTERNAL_PASSWORD" ssh -o StrictHostKeyChecking=no "$EXTERNAL_USER@$EXTERNAL_SERVER" "$1"
}

# Função para copiar arquivo
copy_file() {
    local source=$1
    local dest=$2
    echo -e "${YELLOW}📤 Copiando: $source${NC}"
    sshpass -p "$EXTERNAL_PASSWORD" scp -o StrictHostKeyChecking=no "$source" "$EXTERNAL_USER@$EXTERNAL_SERVER:$dest"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Copiado com sucesso${NC}"
    else
        echo -e "${RED}❌ Erro ao copiar${NC}"
    fi
}

# Função para copiar diretório
copy_dir() {
    local source=$1
    local dest=$2
    echo -e "${YELLOW}📤 Copiando diretório: $source${NC}"
    sshpass -p "$EXTERNAL_PASSWORD" scp -r -o StrictHostKeyChecking=no "$source" "$EXTERNAL_USER@$EXTERNAL_SERVER:$dest"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Diretório copiado${NC}"
    else
        echo -e "${RED}❌ Erro ao copiar diretório${NC}"
    fi
}

echo "1️⃣ CRIANDO BACKUP NO SERVIDOR EXTERNO..."
remote_exec "cp -r $EXTERNAL_PATH ${EXTERNAL_PATH}_backup_\$(date +%Y%m%d_%H%M%S)"
echo -e "${GREEN}✅ Backup criado${NC}\n"

echo "2️⃣ PARANDO SERVIÇOS NO SERVIDOR EXTERNO..."
remote_exec "supervisorctl stop all"
echo -e "${GREEN}✅ Serviços parados${NC}\n"

echo "3️⃣ SINCRONIZANDO ARQUIVOS BACKEND..."
echo "======================================"

# Backend - Arquivos principais modificados
copy_file "/app/backend/server.py" "$EXTERNAL_PATH/backend/"
copy_file "/app/backend/vendas_models.py" "$EXTERNAL_PATH/backend/"
copy_file "/app/backend/vendas_routes.py" "$EXTERNAL_PATH/backend/"
copy_file "/app/backend/vendas_ai_service.py" "$EXTERNAL_PATH/backend/"
copy_file "/app/backend/vendas_bot_service.py" "$EXTERNAL_PATH/backend/"
copy_file "/app/backend/whatsapp_routes.py" "$EXTERNAL_PATH/backend/"
copy_file "/app/backend/whatsapp_service.py" "$EXTERNAL_PATH/backend/"
copy_file "/app/backend/office_service_playwright.py" "$EXTERNAL_PATH/backend/"
copy_file "/app/backend/office_routes.py" "$EXTERNAL_PATH/backend/"
copy_file "/app/backend/keyword_credential_search.py" "$EXTERNAL_PATH/backend/"
copy_file "/app/backend/backup_routes.py" "$EXTERNAL_PATH/backend/"
copy_file "/app/backend/backup_scheduler.py" "$EXTERNAL_PATH/backend/"
copy_file "/app/backend/export_routes.py" "$EXTERNAL_PATH/backend/"
copy_file "/app/backend/create_main_reseller.py" "$EXTERNAL_PATH/backend/"

# Novos arquivos
copy_file "/app/backend/client_name_service.py" "$EXTERNAL_PATH/backend/"
copy_file "/app/backend/client_name_routes.py" "$EXTERNAL_PATH/backend/"

echo ""
echo "4️⃣ SINCRONIZANDO ARQUIVOS FRONTEND..."
echo "======================================"

# Frontend - Componentes
copy_file "/app/frontend/src/components/AIAgentsManager.js" "$EXTERNAL_PATH/frontend/src/components/"

# Frontend - Pages
copy_file "/app/frontend/src/pages/VendasChatNew.js" "$EXTERNAL_PATH/frontend/src/pages/"
copy_file "/app/frontend/src/pages/AgentDashboard.js" "$EXTERNAL_PATH/frontend/src/pages/"

# Frontend - Public
copy_file "/app/frontend/public/index.html" "$EXTERNAL_PATH/frontend/public/"

echo ""
echo "5️⃣ SINCRONIZANDO DOCUMENTAÇÃO..."
echo "======================================"
copy_file "/app/ATUALIZACAO_NOMES_CLIENTES.md" "$EXTERNAL_PATH/"
copy_file "/app/test_update_client_names.py" "$EXTERNAL_PATH/"

echo ""
echo "6️⃣ REINICIANDO SERVIÇOS NO SERVIDOR EXTERNO..."
remote_exec "supervisorctl start all"
sleep 5
remote_exec "supervisorctl status"
echo -e "${GREEN}✅ Serviços reiniciados${NC}\n"

echo ""
echo "================================================"
echo -e "${GREEN}✅ SINCRONIZAÇÃO CONCLUÍDA!${NC}"
echo "================================================"
echo ""
echo "📋 Próximos passos no servidor externo:"
echo "   1. Verificar logs: tail -f /var/log/supervisor/backend.err.log"
echo "   2. Testar funcionalidades"
echo ""
