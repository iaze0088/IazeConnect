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

@export_router.get("/download/vendas_routes.py")
async def download_vendas_routes():
    """Endpoint para baixar vendas_routes.py"""
    file_path = "/app/backend/vendas_routes.py"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="vendas_routes.py not found")
    return FileResponse(file_path, filename="vendas_routes.py", media_type="text/plain")

@export_router.get("/download/vendas_ai_service.py")
async def download_vendas_ai_service():
    """Endpoint para baixar vendas_ai_service.py"""
    file_path = "/app/backend/vendas_ai_service.py"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="vendas_ai_service.py not found")
    return FileResponse(file_path, filename="vendas_ai_service.py", media_type="text/plain")

@export_router.get("/download/vendas_bot_service.py")
async def download_vendas_bot_service():
    """Endpoint para baixar vendas_bot_service.py"""
    file_path = "/app/backend/vendas_bot_service.py"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="vendas_bot_service.py not found")
    return FileResponse(file_path, filename="vendas_bot_service.py", media_type="text/plain")

@export_router.get("/download/vendas_models.py")
async def download_vendas_models():
    """Endpoint para baixar vendas_models.py"""
    file_path = "/app/backend/vendas_models.py"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="vendas_models.py not found")
    return FileResponse(file_path, filename="vendas_models.py", media_type="text/plain")

@export_router.get("/download/vendas_bot_config_models.py")
async def download_vendas_bot_config_models():
    """Endpoint para baixar vendas_bot_config_models.py"""
    file_path = "/app/backend/vendas_bot_config_models.py"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="vendas_bot_config_models.py not found")
    return FileResponse(file_path, filename="vendas_bot_config_models.py", media_type="text/plain")

@export_router.get("/download/AIAgentsManager.js")
async def download_ai_agents_manager():
    """Endpoint para baixar AIAgentsManager.js (frontend)"""
    file_path = "/app/frontend/src/components/AIAgentsManager.js"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="AIAgentsManager.js not found")
    return FileResponse(file_path, filename="AIAgentsManager.js", media_type="text/plain")

@export_router.get("/download/ai_learning_routes.py")
async def download_ai_learning_routes():
    """Endpoint para baixar ai_learning_routes.py (NOVO)"""
    file_path = "/app/backend/ai_learning_routes.py"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="ai_learning_routes.py not found")
    return FileResponse(file_path, filename="ai_learning_routes.py", media_type="text/plain")

@export_router.get("/download/AgentDashboard.js")
async def download_agent_dashboard():
    """Endpoint para baixar AgentDashboard.js (frontend)"""
    file_path = "/app/frontend/src/pages/AgentDashboard.js"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="AgentDashboard.js not found")
    return FileResponse(file_path, filename="AgentDashboard.js", media_type="text/plain")

@export_router.get("/download/cleanup_ai_conversations.sh")
async def download_cleanup_script():
    """Script de limpeza de conversas"""
    file_path = "/root/cleanup_ai_conversations.sh"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="cleanup_ai_conversations.sh not found")
    return FileResponse(file_path, filename="cleanup_ai_conversations.sh", media_type="text/plain")

@export_router.get("/download/sync_learning_system.sh")
async def download_sync_learning_system():
    """Script completo de sincronização do sistema de aprendizado"""
    file_path = "/root/sync_learning_system.sh"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="sync_learning_system.sh not found")
    return FileResponse(file_path, filename="sync_learning_system.sh", media_type="text/plain")

@export_router.get("/download/sync-ai-improvements.sh")
async def download_sync_ai_improvements():
    """Script de sincronização de melhorias de IA"""
    file_path = "/root/sync_ai_improvements.sh"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="sync-ai-improvements.sh not found")
    return FileResponse(file_path, filename="sync-ai-improvements.sh", media_type="text/plain")

@export_router.get("/download/sync-script")
async def download_sync_script():
    """Script de sincronização para o servidor externo"""
    script_content = '''#!/bin/bash
# Auto-sync Emergent → Servidor Externo
# Gerado automaticamente

# NOTA: Esta URL será substituída automaticamente no deploy
EMERGENT_URL="${REACT_APP_BACKEND_URL:-https://wppconnect-fix.preview.emergentagent.com}"
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
