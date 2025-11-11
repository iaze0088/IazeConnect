#!/bin/bash

echo "🚀 Criando Sistema de Exportação Emergent → Servidor Externo"

# Criar endpoint de exportação no backend
cat > /app/backend/export_routes.py << 'PYEOF'
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import os
from pathlib import Path

export_router = APIRouter()

@export_router.get("/download/server.py")
async def download_server():
    """Endpoint para baixar o server.py funcional"""
    file_path = "/app/backend/server.py"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="server.py not found")
    return FileResponse(file_path, filename="server.py", media_type="text/plain")

@export_router.get("/download/sync-script")
async def download_sync_script():
    """Script de sincronização para o servidor externo"""
    script_content = '''#!/bin/bash
# Auto-sync Emergent → Servidor Externo
# Gerado automaticamente

EMERGENT_URL="https://wppconnect-fix.preview.emergentagent.com"
BACKEND_PATH="/opt/iaze/backend"

echo "🔄 Sincronizando arquivos da Emergent..."

# Fazer backup antes
echo "💾 Fazendo backup..."
cp ${BACKEND_PATH}/server.py ${BACKEND_PATH}/server.py.backup_$(date +%Y%m%d_%H%M%S)

# Baixar novo server.py
echo "📥 Baixando server.py..."
curl -o ${BACKEND_PATH}/server.py "${EMERGENT_URL}/api/download/server.py"

# Reiniciar backend
echo "🔄 Reiniciando backend..."
cd /opt/iaze
docker-compose restart backend

echo "✅ Sincronização completa!"
echo "🔍 Testando backend..."
sleep 10
curl http://localhost:8001/api/health

'''
    return JSONResponse(content={"script": script_content})

@export_router.get("/export/status")
async def export_status():
    """Status do sistema para exportação"""
    return {
        "status": "ready",
        "files_available": ["server.py", "models.py", "sync-script"],
        "version": "1.0.0",
        "last_update": "2025-10-29"
    }
PYEOF

echo "✅ Arquivo export_routes.py criado"

# Adicionar as rotas ao server.py
echo ""
echo "📝 Para ativar, adicione estas linhas no /app/backend/server.py:"
echo ""
echo "from export_routes import export_router"
echo "app.include_router(export_router, prefix='/api', tags=['export'])"
echo ""

