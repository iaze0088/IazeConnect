#!/bin/bash
# Script de agendamento da limpeza automática de mídias
# Roda todo dia à meia-noite

# Adicionar ao crontab
# 0 0 * * * /app/schedule_media_cleanup.sh >> /var/log/media_cleanup.log 2>&1

echo "=========================================="
echo "🕐 $(date '+%Y-%m-%d %H:%M:%S')"
echo "🧹 Executando limpeza automática de mídias antigas..."
echo "=========================================="

cd /app
python3 /app/cleanup_old_media.py

echo ""
echo "✅ Limpeza concluída!"
echo "=========================================="
echo ""
