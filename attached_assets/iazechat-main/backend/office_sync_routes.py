"""
Rotas para Sincronização Office
API para gerenciar banco de dados local de clientes
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional, Dict
from pydantic import BaseModel
import logging

from office_sync_service import OfficeSyncService
from dependencies import get_current_user, db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/office-sync", tags=["office-sync"])

# Sync service será inicializado na primeira chamada (lazy loading)
_sync_service = None

def get_sync_service():
    """Retorna a instância do serviço de sincronização (lazy loading)"""
    global _sync_service
    if _sync_service is None:
        _sync_service = OfficeSyncService(db)
    return _sync_service

# ==================== MODELS ====================

class OfficeCredentials(BaseModel):
    url: str
    username: str
    password: str
    nome: Optional[str] = None

class SyncTriggerResponse(BaseModel):
    success: bool
    message: str
    sync_id: Optional[str] = None

class ClientFilters(BaseModel):
    status_type: Optional[str] = None  # "ativo", "expirado", "outros"
    office_account: Optional[str] = None
    telefone: Optional[str] = None
    usuario: Optional[str] = None
    search: Optional[str] = None

# ==================== CREDENTIALS ROUTES ====================

@router.get("/test-credentials")
async def test_credentials_route():
    """Rota de teste simples sem autenticação"""
    return {"status": "ok", "message": "Rota de credenciais funcionando!"}

@router.post("/credentials")
async def add_office_credentials(
    credentials: OfficeCredentials,
    current_user: dict = Depends(get_current_user)
):
    """
    Adicionar credenciais do Office (gestor.my)
    """
    try:
        import uuid
        from datetime import datetime, timezone
        
        credential_id = str(uuid.uuid4())
        
        credential_doc = {
            "id": credential_id,
            "url": credentials.url,
            "username": credentials.username,
            "password": credentials.password,
            "nome": credentials.nome or f"Office {credentials.username}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "active": True
        }
        
        await db.office_credentials.insert_one(credential_doc)
        
        logger.info(f"✅ Credenciais do Office cadastradas: {credential_id} por {current_user.get('email')}")
        
        return {
            "success": True,
            "credential_id": credential_id,
            "message": "Credenciais cadastradas com sucesso"
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao cadastrar credenciais: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/credentials")
async def list_office_credentials(
    current_user: dict = Depends(get_current_user)
):
    """
    Listar todas as credenciais do Office cadastradas
    """
    try:
        credentials = await db.office_credentials.find(
            {"active": True}
        ).to_list(length=None)
        
        # Remover senhas e _id da resposta
        for cred in credentials:
            cred.pop("password", None)
            cred.pop("_id", None)
        
        return {
            "success": True,
            "credentials": credentials
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar credenciais: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/credentials/{credential_id}")
async def delete_office_credentials(
    credential_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Remover credenciais do Office
    """
    try:
        result = await db.office_credentials.update_one(
            {"id": credential_id},
            {"$set": {"active": False}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Credenciais não encontradas")
        
        logger.info(f"✅ Credenciais removidas: {credential_id} por {current_user.get('email')}")
        
        return {
            "success": True,
            "message": "Credenciais removidas com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao remover credenciais: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== SYNC ROUTES ====================

@router.post("/sync-now")
async def trigger_sync_now(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Disparar sincronização imediata de TODOS os clientes
    Roda em background para não travar a resposta
    """
    try:
        logger.info(f"🔄 Sincronização manual disparada por {current_user.get('email')}")
        
        # Rodar em background
        background_tasks.add_task(get_sync_service().sync_all_clients)
        
        return {
            "success": True,
            "message": "Sincronização iniciada em background. Verifique o status em /sync-status",
            "estimated_duration": "5-15 minutos"
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao disparar sincronização: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync-status")
async def get_sync_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Obter status da última sincronização
    """
    try:
        # Buscar última sincronização
        last_sync = await db.office_sync_history.find_one(
            {},
            sort=[("started_at", -1)]
        )
        
        if not last_sync:
            return {
                "success": True,
                "message": "Nenhuma sincronização realizada ainda",
                "last_sync": None
            }
        
        # Remover _id
        last_sync.pop("_id", None)
        
        return {
            "success": True,
            "last_sync": last_sync
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search-clients")
async def search_clients_local(
    filters: ClientFilters,
    current_user: dict = Depends(get_current_user)
):
    """
    Buscar clientes no banco LOCAL (RÁPIDO!)
    
    Filtros disponíveis:
    - status_type: "ativo", "expirado", "outros"
    - office_account: "fabiotec34", etc
    - telefone: "19989612020"
    - usuario: "3334567oro"
    - search: busca geral em nome, usuario, telefone
    """
    try:
        logger.info(f"🔍 Busca local com filtros: {filters.dict()}")
        
        clients = await get_sync_service().get_clients_by_filters(filters.dict())
        
        return {
            "success": True,
            "count": len(clients),
            "clients": clients
        }
        
    except Exception as e:
        logger.error(f"❌ Erro na busca local: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_clients_statistics(
    current_user: dict = Depends(get_current_user)
):
    """
    Obter estatísticas dos clientes
    - Total de ativos, expirados, outros
    - Por painel (fabiotec34, 35, etc)
    """
    try:
        stats = await get_sync_service().get_statistics()
        
        return {
            "success": True,
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/client-changes/{usuario}")
async def get_client_change_history(
    usuario: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Obter histórico de mudanças de um cliente específico
    """
    try:
        changes = await db.office_changes_history.find(
            {"usuario": usuario}
        ).sort("changed_at", -1).to_list(length=50)
        
        # Remover _id
        for change in changes:
            change.pop("_id", None)
        
        return {
            "success": True,
            "usuario": usuario,
            "changes_count": len(changes),
            "changes": changes
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter histórico: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/expiring-soon")
async def get_expiring_soon(
    days: int = 7,
    current_user: dict = Depends(get_current_user)
):
    """
    Obter clientes que vão expirar nos próximos X dias
    """
    try:
        from datetime import datetime, timedelta
        
        # Buscar clientes ativos
        clients = await db.office_clients.find({
            "status_type": "ativo"
        }).to_list(length=None)
        
        expiring_soon = []
        
        now = datetime.now()
        threshold = now + timedelta(days=days)
        
        for client in clients:
            vencimento_str = client.get("vencimento", "")
            
            if not vencimento_str or vencimento_str == "NUNCA":
                continue
            
            try:
                # Tentar parsear data
                vencimento = datetime.strptime(vencimento_str, "%Y-%m-%d %H:%M:%S")
                
                if now <= vencimento <= threshold:
                    client.pop("_id", None)
                    days_remaining = (vencimento - now).days
                    client["days_remaining"] = days_remaining
                    expiring_soon.append(client)
                    
            except:
                continue
        
        # Ordenar por dias restantes
        expiring_soon.sort(key=lambda x: x["days_remaining"])
        
        return {
            "success": True,
            "count": len(expiring_soon),
            "clients": expiring_soon
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar clientes expirando: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear-database")
async def clear_client_database(
    current_user: dict = Depends(get_current_user)
):
    """
    Limpar banco de dados de clientes (apenas admin)
    """
    try:
        # Verificar se é admin
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Apenas admin pode limpar o banco")
        
        result_clients = await db.office_clients.delete_many({})
        result_history = await db.office_changes_history.delete_many({})
        result_sync = await db.office_sync_history.delete_many({})
        
        logger.warning(f"🗑️ Banco de dados limpo por {current_user.get('email')}")
        
        return {
            "success": True,
            "message": "Banco de dados limpo",
            "deleted": {
                "clients": result_clients.deleted_count,
                "changes": result_history.deleted_count,
                "sync_history": result_sync.deleted_count
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao limpar banco: {e}")
        raise HTTPException(status_code=500, detail=str(e))
