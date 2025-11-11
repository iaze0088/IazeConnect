#!/bin/bash

# FORÇAR conexão como conectada

TOKEN=$(curl -s -X POST "https://suporte.help/api/auth/admin/login" -H "Content-Type: application/json" -d '{"email":"admin@admin.com","password":"102030@ab"}' | jq -r '.token')

# Pegar última conexão
CONN_ID=$(curl -s "https://suporte.help/api/whatsapp/connections" -H "Authorization: Bearer $TOKEN" | jq -r '.[0].id')

echo "Conexão ID: $CONN_ID"
echo ""
echo "FORÇANDO conexão como conectada..."

curl -s -X POST "https://suporte.help/api/whatsapp/connections/$CONN_ID/force-connected" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

echo ""
echo "✅ Pronto! Recarregue o dashboard (F5)"
