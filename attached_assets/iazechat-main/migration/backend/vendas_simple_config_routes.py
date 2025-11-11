"""
Rotas Simples para WA Site (Vendas com IA)
"""
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid
from datetime import datetime, timezone
import logging
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/vendas-bot", tags=["admin-wa-site"])

class SimpleConfig(BaseModel):
    empresa_nome: str
    usa_ia: bool
    api_teste_url: str
    agent_id: Optional[str] = None
    custom_instructions: Optional[str] = None  # Instruções customizadas diretas

def get_db():
    """Dependency para obter database"""
    from server import db
    return db

@router.get("/simple-config")
async def get_simple_config(db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Obter configuração simples do WA Site
    """
    try:
        config = await db.vendas_simple_config.find_one(
            {"is_active": True},
            {"_id": 0}
        )
        
        if not config:
            # Retornar config padrão
            return {
                "config_id": None,
                "empresa_nome": "CyberTV",
                "usa_ia": True,
                "api_teste_url": "https://gesth.io/api/get-teste?hash=TG1OTW5QWHlaTW5Q",
                "agent_id": None,
                "custom_instructions": None,
                "is_active": True
            }
        
        return config
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar config simples: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simple-config")
async def save_simple_config(
    request: SimpleConfig,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Salvar configuração simples do WA Site
    """
    try:
        # Desativar todas as configs existentes
        await db.vendas_simple_config.update_many(
            {},
            {"$set": {"is_active": False}}
        )
        
        # Criar nova config
        config_id = str(uuid.uuid4())
        config_data = {
            "config_id": config_id,
            "empresa_nome": request.empresa_nome,
            "usa_ia": request.usa_ia,
            "api_teste_url": request.api_teste_url,
            "agent_id": request.agent_id,
            "custom_instructions": request.custom_instructions,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.vendas_simple_config.insert_one(config_data)
        
        logger.info(f"✅ Config simples salva: {config_id}")
        
        return {"success": True, "config_id": config_id}
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar config simples: {e}")
        raise HTTPException(status_code=500, detail=str(e))
