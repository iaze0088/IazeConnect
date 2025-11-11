#!/bin/bash

echo "🚀 Atualizando backend e frontend para fluxo '12'..."

# Backend
echo "📝 Atualizando vendas_ai_service.py..."
cat > /opt/iaze/backend/vendas_ai_service.py << 'EOFBACKEND'
