"""
Rotas exclusivas para gerenciamento de credenciais do Office
Arquivo criado para evitar conflitos de imports
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid
import logging

# Importar dependências compartilhadas
from dependencies import get_current_user, db

logger = logging.getLogger(__name__)

# Router com prefix
router = APIRouter(prefix="/api/office-sync", tags=["office-credentials"])

# ==================== MODELS ====================

class OfficeCredentials(BaseModel):
    url: str
    username: str
    password: str
    nome: Optional[str] = None

# ==================== ROUTES ====================

@router.post("/credentials")
async def add_office_credentials(
    credentials: OfficeCredentials,
    current_user: dict = Depends(get_current_user)
):
    """
    Adicionar credenciais do Office (gestor.my)
    """
    try:
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
        
        logger.info(f"✅ Credenciais do Office cadastradas: {credential_id} por {current_user.get('email', current_user.get('login'))}")
        
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
        
        logger.info(f"✅ Credenciais removidas: {credential_id} por {current_user.get('email', current_user.get('login'))}")
        
        return {
            "success": True,
            "message": "Credenciais removidas com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao remover credenciais: {e}")
        raise HTTPException(status_code=500, detail=str(e))
