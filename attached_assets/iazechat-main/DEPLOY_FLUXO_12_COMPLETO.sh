#!/bin/bash

echo "========================================"
echo "🚀 DEPLOY COMPLETO - FLUXO '12'"
echo "========================================"
echo ""

# 1. Backend - vendas_ai_service.py
echo "📝 Atualizando backend..."
cp /app/backend/vendas_ai_service.py /opt/iaze/backend/vendas_ai_service.py
cp /app/backend/vendas_routes.py /opt/iaze/backend/vendas_routes.py

# 2. Frontend - VendasChatNew.js
echo "📝 Atualizando frontend..."
cp /app/frontend_update_complete.js /opt/iaze/frontend/src/pages/VendasChatNew.js

# 3. CSS
cp /app/frontend/src/pages/VendasChatNew.css /opt/iaze/frontend/src/pages/VendasChatNew.css

echo "✅ Arquivos copiados!"
echo ""

# 4. Reiniciar serviços
echo "🔄 Reiniciando serviços..."
docker stop iaze_frontend iaze_backend
rm -rf /opt/iaze/frontend/.cache
docker start iaze_backend
sleep 3
docker start iaze_frontend

echo "✅ Serviços reiniciados!"
echo ""
echo "🎉 DEPLOY COMPLETO!"
echo "Aguarde 30 segundos e teste: https://suporte.help/vendas"
