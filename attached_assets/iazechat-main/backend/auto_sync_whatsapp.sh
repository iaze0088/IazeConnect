#!/bin/bash
# Auto-sync WhatsApp - Roda em loop infinito

while true; do
    echo "🔄 $(date '+%H:%M:%S') - Sincronizando WhatsApp..."
    python3 /app/backend/fix_whatsapp_sync_robust.py 2>&1 | grep -E "✅|❌|🔄|➕|🗑️"
    sleep 10
done
