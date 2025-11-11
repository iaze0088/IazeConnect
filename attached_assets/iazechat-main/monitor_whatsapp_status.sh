#!/bin/bash

CONN_ID="0d9b9fa8-788a-4261-90b5-582661bcbc8f"
INSTANCE="whatsapp_iaze_principal_0d9b9fa8"

echo "🔍 MONITORANDO STATUS DA CONEXÃO"
echo "================================"
echo "Conexão ID: $CONN_ID"
echo "Instance: $INSTANCE"
echo ""

TOKEN=$(curl -s -X POST "http://localhost:8001/api/auth/admin/login" -H "Content-Type: application/json" -d '{"email":"admin@admin.com","password":"102030@ab"}' | jq -r '.token')

for i in {1..20}; do
  echo "[$i] $(date +%H:%M:%S)"
  
  # Status no banco
  DB_STATUS=$(curl -s "http://localhost:8001/api/whatsapp/connections" -H "Authorization: Bearer $TOKEN" | jq -r '.[0] | {status, connected}')
  echo "  📊 Banco: $DB_STATUS"
  
  # Status no WPPConnect
  CONN_TOKEN=$(curl -s "http://localhost:8001/api/whatsapp/connections" -H "Authorization: Bearer $TOKEN" | jq -r '.[0].token')
  WPP_STATUS=$(curl -s "http://151.243.218.223:21465/api/$INSTANCE:$CONN_TOKEN/status-session" 2>/dev/null | jq -r '.status')
  echo "  🌐 WPPConnect: $WPP_STATUS"
  
  if [ "$WPP_STATUS" == "CONNECTED" ]; then
    echo ""
    echo "🎉 WhatsApp CONECTADO!"
    echo "Chamando endpoint de atualização..."
    curl -s -X POST "http://localhost:8001/api/whatsapp/connections/$CONN_ID/refresh-status" -H "Authorization: Bearer $TOKEN" | jq '.'
    break
  fi
  
  echo ""
  sleep 5
done
