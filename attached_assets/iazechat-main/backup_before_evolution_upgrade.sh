#!/bin/bash

# Script de Backup antes do upgrade Evolution API v2.3.6
# Data: $(date +%Y-%m-%d_%H-%M-%S)

BACKUP_DIR="/app/backups/evolution_upgrade_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "=========================================="
echo "INICIANDO BACKUP PARA UPGRADE EVOLUTION API"
echo "Diretório: $BACKUP_DIR"
echo "=========================================="

# 1. Backup MongoDB
echo ""
echo "[1/5] Fazendo backup do MongoDB..."
MONGO_URL=$(grep MONGO_URL /app/backend/.env | cut -d '=' -f2)
mongodump --uri="$MONGO_URL" --out="$BACKUP_DIR/mongodb_backup" 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Backup MongoDB concluído"
else
    echo "✗ ERRO no backup MongoDB"
fi

# 2. Backup arquivos .env
echo ""
echo "[2/5] Fazendo backup dos arquivos .env..."
cp /app/backend/.env "$BACKUP_DIR/backend.env.bak" 2>&1
cp /app/frontend/.env "$BACKUP_DIR/frontend.env.bak" 2>&1
echo "✓ Arquivos .env salvos"

# 3. Backup docker-compose Evolution API
echo ""
echo "[3/5] Fazendo backup do docker-compose Evolution API..."
if [ -f /app/docker-compose.evolution.yml ]; then
    cp /app/docker-compose.evolution.yml "$BACKUP_DIR/docker-compose.evolution.yml.bak"
    echo "✓ docker-compose.evolution.yml salvo"
else
    echo "⚠ docker-compose.evolution.yml não encontrado"
fi

# 4. Backup código backend WhatsApp
echo ""
echo "[4/5] Fazendo backup do código backend WhatsApp..."
mkdir -p "$BACKUP_DIR/backend_code"
cp /app/backend/whatsapp_service.py "$BACKUP_DIR/backend_code/" 2>&1
cp /app/backend/whatsapp_routes.py "$BACKUP_DIR/backend_code/" 2>&1
cp /app/backend/whatsapp_models.py "$BACKUP_DIR/backend_code/" 2>&1
if [ -f /app/backend/whatsapp_polling.py ]; then
    cp /app/backend/whatsapp_polling.py "$BACKUP_DIR/backend_code/"
fi
echo "✓ Código backend salvo"

# 5. Backup documentação
echo ""
echo "[5/5] Fazendo backup da documentação..."
cp /app/GUIA_WHATSAPP_EVOLUTION.md "$BACKUP_DIR/" 2>/dev/null
cp /app/TESTE_WHATSAPP_COMPLETO.md "$BACKUP_DIR/" 2>/dev/null
cp /app/WHATSAPP_CLEANUP_FIX.md "$BACKUP_DIR/" 2>/dev/null
cp /app/STATUS_WHATSAPP_COMPLETO.md "$BACKUP_DIR/" 2>/dev/null
echo "✓ Documentação salva"

# Criar arquivo de informações do backup
echo ""
echo "Criando arquivo de informações..."
cat > "$BACKUP_DIR/BACKUP_INFO.txt" << EOF
========================================
BACKUP PARA UPGRADE EVOLUTION API
========================================

Data do Backup: $(date)
Versão Atual Evolution API: v1.8.7
Versão Alvo: v2.3.6

Conteúdo do Backup:
- MongoDB (todas as collections)
- Arquivos .env (backend e frontend)
- docker-compose.evolution.yml
- Código backend WhatsApp (service, routes, models)
- Documentação relacionada

Status: Backup concluído com sucesso

Para restaurar:
1. MongoDB: mongorestore --uri="MONGO_URL" "$BACKUP_DIR/mongodb_backup"
2. Código: Copiar arquivos de backend_code/ de volta para /app/backend/
3. Configs: Copiar .env.bak de volta para .env

========================================
EOF

# Mostrar resumo
echo ""
echo "=========================================="
echo "BACKUP CONCLUÍDO COM SUCESSO!"
echo "=========================================="
echo "Localização: $BACKUP_DIR"
echo ""
du -sh "$BACKUP_DIR"
echo ""
echo "Conteúdo:"
ls -lah "$BACKUP_DIR"
echo "=========================================="
