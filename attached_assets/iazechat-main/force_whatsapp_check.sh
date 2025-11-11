#!/bin/bash

# Script para forçar verificação e atualização de status WhatsApp

echo "🔍 MONITORAMENTO E ATUALIZAÇÃO FORÇADA"
echo "====================================="
echo ""

# Obter token
TOKEN=$(curl -s -X POST "https://suporte.help/api/auth/admin/login" -H "Content-Type: application/json" -d '{"email":"admin@admin.com","password":"102030@ab"}' | jq -r '.token')

# Buscar última conexão
CONN_DATA=$(curl -s "https://suporte.help/api/whatsapp/connections" -H "Authorization: Bearer $TOKEN" | jq '.[0]')
CONN_ID=$(echo "$CONN_DATA" | jq -r '.id')
INSTANCE=$(echo "$CONN_DATA" | jq -r '.instance_name')
CONN_TOKEN=$(echo "$CONN_DATA" | jq -r '.token')

echo "Conexão: $CONN_ID"
echo "Instance: $INSTANCE"
echo ""
echo "⚠️  ESCANEIE O QR CODE AGORA!"
echo ""

# Monitorar por 90 segundos
for i in {1..30}; do
  sleep 3
  
  # Verificar status no WPPConnect
  WPP_STATUS=$(curl -s "http://151.243.218.223:21465/api/$INSTANCE:$CONN_TOKEN/status-session" 2>/dev/null | jq -r '.status')
  
  echo "[$i/30] $(date +%H:%M:%S) - Status: $WPP_STATUS"
  
  if [ "$WPP_STATUS" == "CONNECTED" ]; then
    echo ""
    echo "🎉🎉🎉 CONECTADO DETECTADO! 🎉🎉🎉"
    echo ""
    
    # Forçar atualização no banco
    echo "Forçando atualização no banco de dados..."
    
    # Método 1: Via endpoint
    curl -s -X POST "https://suporte.help/api/whatsapp/connections/$CONN_ID/refresh-status" \
      -H "Authorization: Bearer $TOKEN" > /dev/null
    
    # Método 2: Atualização direta (fallback)
    echo "Aguarde 5 segundos..."
    sleep 5
    
    # Verificar se atualizou
    DB_STATUS=$(curl -s "https://suporte.help/api/whatsapp/connections" -H "Authorization: Bearer $TOKEN" | jq -r '.[0].connected')
    
    if [ "$DB_STATUS" == "true" ]; then
      echo "✅ STATUS ATUALIZADO NO BANCO!"
      echo ""
      echo "🎉 SUCESSO! Recarregue o dashboard (F5)"
    else
      echo "⚠️ Status não atualizou. Tentando novamente..."
      
      # Forçar novamente
      curl -s -X POST "https://suporte.help/api/whatsapp/connections/$CONN_ID/refresh-status" \
        -H "Authorization: Bearer $TOKEN" | jq '{status, connected}'
    fi
    
    exit 0
  fi
  
  if [ "$WPP_STATUS" == "CLOSED" ]; then
    echo ""
    echo "❌ Sessão fechou. A conexão não persistiu."
    echo ""
    echo "CAUSA: Número já conectado em outro dispositivo."
    echo "SOLUÇÃO: Desconecte TODOS os outros dispositivos WhatsApp Web."
    echo ""
    exit 1
  fi
done

echo ""
echo "⏰ Timeout. QR code não foi escaneado ou expirou."
