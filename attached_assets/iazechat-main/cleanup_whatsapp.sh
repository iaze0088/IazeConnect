#!/bin/bash
# Script de limpeza completa WhatsApp Evolution API + MongoDB

echo "🧹 LIMPEZA COMPLETA DO SISTEMA WHATSAPP"
echo "========================================"
echo ""

# 1. Buscar todas as instâncias da Evolution API
echo "📋 Buscando instâncias na Evolution API..."
INSTANCES=$(curl -s -X GET "http://45.157.157.69:8080/instance/fetchInstances" \
  -H "apikey: B4F8E9A2C5D7F1E3A9B6C8D2E5F7A1B3")

# Contar instâncias
INSTANCE_COUNT=$(echo "$INSTANCES" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data))")
echo "   Encontradas: $INSTANCE_COUNT instâncias"

# 2. Deletar cada instância
if [ "$INSTANCE_COUNT" -gt 0 ]; then
    echo ""
    echo "🗑️  Deletando instâncias da Evolution API..."
    echo "$INSTANCES" | python3 << 'PYTHON'
import json, sys, subprocess

instances = json.load(sys.stdin)
for inst_data in instances:
    inst_name = inst_data.get("instance", {}).get("instanceName")
    if inst_name:
        print(f"   Deletando: {inst_name}...")
        # Logout primeiro
        subprocess.run([
            "curl", "-s", "-X", "DELETE",
            f"http://45.157.157.69:8080/instance/logout/{inst_name}",
            "-H", "apikey: B4F8E9A2C5D7F1E3A9B6C8D2E5F7A1B3"
        ], capture_output=True)
        
        # Aguardar 1 segundo
        import time
        time.sleep(1)
        
        # Deletar
        result = subprocess.run([
            "curl", "-s", "-X", "DELETE",
            f"http://45.157.157.69:8080/instance/delete/{inst_name}",
            "-H", "apikey: B4F8E9A2C5D7F1E3A9B6C8D2E5F7A1B3"
        ], capture_output=True, text=True)
        print(f"      Resultado: {result.stdout[:50]}...")
PYTHON
fi

# 3. Limpar banco de dados
echo ""
echo "🗑️  Limpando banco de dados MongoDB..."
cd /app/backend && python3 << 'EOF'
import os, asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def cleanup():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client.cybertv_db
    
    result = await db.whatsapp_connections.delete_many({})
    print(f"   Deletadas: {result.deleted_count} conexões")

asyncio.run(cleanup())
EOF

# 4. Verificar limpeza
echo ""
echo "✅ Verificando limpeza..."
FINAL_INSTANCES=$(curl -s -X GET "http://45.157.157.69:8080/instance/fetchInstances" \
  -H "apikey: B4F8E9A2C5D7F1E3A9B6C8D2E5F7A1B3")
FINAL_COUNT=$(echo "$FINAL_INSTANCES" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data))")

echo ""
echo "========================================"
echo "📊 RESULTADO DA LIMPEZA:"
echo "   Evolution API: $FINAL_COUNT instâncias restantes"
if [ "$FINAL_COUNT" -eq 0 ]; then
    echo "   ✅ Evolution API completamente limpa!"
else
    echo "   ⚠️  Ainda há $FINAL_COUNT instância(s)"
fi
echo "========================================"
echo ""
echo "✅ LIMPEZA CONCLUÍDA!"
echo ""
echo "Agora você pode:"
echo "1. Acessar o painel: /admin ou /reseller-dashboard"
echo "2. Clicar em 'WhatsApp'"
echo "3. Clicar em 'Adicionar Número'"
echo ""
