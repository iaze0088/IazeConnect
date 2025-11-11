"""
Rotas para Configuração do Bot de Vendas (Admin)
"""
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid
from datetime import datetime, timezone
import logging

from vendas_bot_config_models import BotFlowConfigRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/vendas-bot", tags=["admin-vendas-bot"])

def get_db():
    """Dependency para obter database"""
    from server import db
    return db

@router.get("/config")
async def get_bot_config(
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Obter configuração do bot de vendas
    Retorna a configuração ativa
    """
    try:
        config = await db.vendas_bot_config.find_one(
            {"is_active": True},
            {"_id": 0}
        )
        
        if not config:
            # Retornar config padrão se não houver
            return {
                "config_id": None,
                "name": "Configuração Padrão",
                "is_active": True,
                "initial_message": "Olá! 👋 Seja bem-vindo à **CyberTV**!\n\nTemos o melhor serviço de IPTV do Brasil! 📺\n\nDigite **TESTE** para ganhar 3 horas grátis! 🎁",
                "steps": [
                    {
                        "step_id": "1",
                        "step_name": "Confirmação de Teste",
                        "trigger_keywords": ["sim", "quero", "teste", "gratis", "grátis", "ok"],
                        "bot_message": "Ótimo! 🎉\n\nPara gerar seu teste GRÁTIS, preciso de algumas informações:\n\n📱 **Seu WhatsApp** (formato: 5511999999999)\n🔐 **Escolha uma senha de 2 dígitos** (ex: 25)\n\nEnvie no formato: WhatsApp Senha\nExemplo: 5511987654321 25",
                        "next_step": "2",
                        "requires_validation": False
                    },
                    {
                        "step_id": "2",
                        "step_name": "Captura de Credenciais",
                        "trigger_keywords": [],
                        "bot_message": "",
                        "next_step": None,
                        "requires_validation": True,
                        "validation_type": "whatsapp_pin",
                        "action": "generate_test"
                    }
                ]
            }
        
        return config
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar config do bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/config")
async def save_bot_config(
    request: BotFlowConfigRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Salvar configuração do bot de vendas
    """
    try:
        # Desativar todas as configs existentes
        await db.vendas_bot_config.update_many(
            {},
            {"$set": {"is_active": False}}
        )
        
        # Gerar IDs para steps
        steps_with_ids = []
        for idx, step in enumerate(request.steps):
            steps_with_ids.append({
                "step_id": str(idx + 1),
                "step_name": step.step_name,
                "trigger_keywords": step.trigger_keywords,
                "bot_message": step.bot_message,
                "next_step": step.next_step,
                "requires_validation": step.requires_validation,
                "validation_type": step.validation_type,
                "action": step.action
            })
        
        # Criar nova config
        config_id = str(uuid.uuid4())
        config_data = {
            "config_id": config_id,
            "name": request.name,
            "is_active": request.is_active,
            "initial_message": request.initial_message,
            "steps": steps_with_ids,
            "reseller_id": None,  # Global (admin)
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.vendas_bot_config.insert_one(config_data)
        
        logger.info(f"✅ Configuração do bot salva: {config_id}")
        
        return {"success": True, "config_id": config_id}
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar config do bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/config/{config_id}")
async def update_bot_config(
    config_id: str,
    request: BotFlowConfigRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Atualizar configuração existente
    """
    try:
        # Desativar todas as outras configs
        await db.vendas_bot_config.update_many(
            {"config_id": {"$ne": config_id}},
            {"$set": {"is_active": False}}
        )
        
        # Gerar IDs para steps
        steps_with_ids = []
        for idx, step in enumerate(request.steps):
            steps_with_ids.append({
                "step_id": str(idx + 1),
                "step_name": step.step_name,
                "trigger_keywords": step.trigger_keywords,
                "bot_message": step.bot_message,
                "next_step": step.next_step,
                "requires_validation": step.requires_validation,
                "validation_type": step.validation_type,
                "action": step.action
            })
        
        # Atualizar config
        result = await db.vendas_bot_config.update_one(
            {"config_id": config_id},
            {"$set": {
                "name": request.name,
                "is_active": request.is_active,
                "initial_message": request.initial_message,
                "steps": steps_with_ids,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Config não encontrada")
        
        logger.info(f"✅ Configuração do bot atualizada: {config_id}")
        
        return {"success": True, "config_id": config_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar config do bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/config/{config_id}")
async def delete_bot_config(
    config_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Deletar configuração
    """
    try:
        result = await db.vendas_bot_config.delete_one({"config_id": config_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Config não encontrada")
        
        logger.info(f"✅ Configuração do bot deletada: {config_id}")
        
        return {"success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao deletar config do bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/configs")
async def list_bot_configs(
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Listar todas as configurações
    """
    try:
        configs = await db.vendas_bot_config.find(
            {},
            {"_id": 0}
        ).sort("created_at", -1).to_list(length=None)
        
        return {"configs": configs}
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar configs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
