#!/bin/bash
###############################################################################
# DEPLOY FRONTEND - VPS suporte.help
# Atualiza apenas o frontend no VPS
###############################################################################

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

VPS_IP="151.243.218.223"
VPS_USER="root"
VPS_PATH="/var/www/iaze"

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         DEPLOY FRONTEND - suporte.help/vendas              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Build já foi feito, agora fazer rsync
echo -e "${BLUE}[1/3] Enviando arquivos para VPS...${NC}"
rsync -avz --delete \
  /app/frontend/build/ \
  ${VPS_USER}@${VPS_IP}:${VPS_PATH}/frontend/build/

echo -e "${GREEN}✅ Arquivos enviados${NC}"

# Copiar arquivo VendasChatNew.js também
echo -e "${BLUE}[2/3] Atualizando código fonte...${NC}"
rsync -avz \
  /app/frontend/src/pages/VendasChatNew.js \
  ${VPS_USER}@${VPS_IP}:${VPS_PATH}/frontend/src/pages/

echo -e "${GREEN}✅ Código fonte atualizado${NC}"

# Reiniciar frontend no VPS
echo -e "${BLUE}[3/3] Reiniciando frontend no VPS...${NC}"
ssh ${VPS_USER}@${VPS_IP} << 'EOF'
cd /var/www/iaze/frontend
supervisorctl restart iaze-frontend
sleep 2
supervisorctl status iaze-frontend
EOF

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    ✅ DEPLOY CONCLUÍDO!                     ║${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}║  Acesse: https://suporte.help/vendas                      ║${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}║  Funcionalidades implementadas:                            ║${NC}"
echo -e "${GREEN}║  ✅ Campos WhatsApp e PIN bloqueados após 1º teste        ║${NC}"
echo -e "${GREEN}║  ✅ Botões para copiar usuário e senha                    ║${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
