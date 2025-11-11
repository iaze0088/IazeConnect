"""
Routes para funcionalidades administrativas adicionais:
- IPTV Apps
- WhatsApp Plans
- WhatsApp Instances  
- Mercado Pago Config
- Subscriptions
"""

from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone
import uuid
import os

router = APIRouter()

# MongoDB connection
from server import db

# ==================================================================
# MODELS
# ==================================================================

class IPTVAppCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    download_url: str
    version: Optional[str] = None
    enabled: bool = True

class IPTVAppUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon_url: Optional[str] = None
    download_url: Optional[str] = None
    version: Optional[str] = None
    enabled: Optional[bool] = None

class WhatsAppPlanCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    max_instances: int
    features: List[str] = []
    enabled: bool = True

class WhatsAppPlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    max_instances: Optional[int] = None
    features: Optional[List[str]] = None
    enabled: Optional[bool] = None

class WhatsAppInstanceCreate(BaseModel):
    name: str
    phone_number: Optional[str] = None
    qr_code: Optional[str] = None
    status: str = "disconnected"  # disconnected, connected, qr_pending
    enabled: bool = True

class WhatsAppInstanceUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    qr_code: Optional[str] = None
    status: Optional[str] = None
    enabled: Optional[bool] = None

class MercadoPagoConfig(BaseModel):
    public_key: str
    access_token: str
    webhook_url: Optional[str] = None
    enabled: bool = True

# ==================================================================
# IPTV APPS ROUTES
# ==================================================================

@router.get("/iptv/apps")
async def list_iptv_apps():
    """Lista todos os apps IPTV"""
    apps = await db.iptv_apps.find({}).to_list(length=None)
    return apps

@router.post("/iptv/apps")
async def create_iptv_app(app: IPTVAppCreate):
    """Cria novo app IPTV"""
    app_data = app.dict()
    app_data["id"] = str(uuid.uuid4())
    app_data["created_at"] = datetime.now(timezone.utc).isoformat()
    app_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.iptv_apps.insert_one(app_data)
    return app_data

@router.get("/iptv/apps/{app_id}")
async def get_iptv_app(app_id: str):
    """Obter app IPTV específico"""
    app = await db.iptv_apps.find_one({"id": app_id})
    if not app:
        raise HTTPException(status_code=404, detail="App IPTV não encontrado")
    return app

@router.put("/iptv/apps/{app_id}")
async def update_iptv_app(app_id: str, app: IPTVAppUpdate):
    """Atualiza app IPTV"""
    update_data = {k: v for k, v in app.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.iptv_apps.update_one(
        {"id": app_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="App IPTV não encontrado")
    
    return {"message": "App atualizado com sucesso"}

@router.delete("/iptv/apps/{app_id}")
async def delete_iptv_app(app_id: str):
    """Deleta app IPTV"""
    result = await db.iptv_apps.delete_one({"id": app_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="App IPTV não encontrado")
    
    return {"message": "App deletado com sucesso"}

# ==================================================================
# WHATSAPP PLANS ROUTES
# ==================================================================

@router.get("/whatsapp/plans")
async def list_whatsapp_plans():
    """Lista todos os planos WhatsApp"""
    plans = await db.whatsapp_plans.find({}).to_list(length=None)
    return plans

@router.post("/whatsapp/plans")
async def create_whatsapp_plan(plan: WhatsAppPlanCreate):
    """Cria novo plano WhatsApp"""
    plan_data = plan.dict()
    plan_data["id"] = str(uuid.uuid4())
    plan_data["created_at"] = datetime.now(timezone.utc).isoformat()
    plan_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.whatsapp_plans.insert_one(plan_data)
    return plan_data

@router.get("/whatsapp/plans/{plan_id}")
async def get_whatsapp_plan(plan_id: str):
    """Obter plano WhatsApp específico"""
    plan = await db.whatsapp_plans.find_one({"id": plan_id})
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    return plan

@router.put("/whatsapp/plans/{plan_id}")
async def update_whatsapp_plan(plan_id: str, plan: WhatsAppPlanUpdate):
    """Atualiza plano WhatsApp"""
    update_data = {k: v for k, v in plan.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.whatsapp_plans.update_one(
        {"id": plan_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    
    return {"message": "Plano atualizado com sucesso"}

@router.delete("/whatsapp/plans/{plan_id}")
async def delete_whatsapp_plan(plan_id: str):
    """Deleta plano WhatsApp"""
    result = await db.whatsapp_plans.delete_one({"id": plan_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    
    return {"message": "Plano deletado com sucesso"}

# ==================================================================
# WHATSAPP INSTANCES ROUTES
# ==================================================================

@router.get("/whatsapp/instances")
async def list_whatsapp_instances():
    """Lista todas as instâncias WhatsApp"""
    instances = await db.whatsapp_instances.find({}).to_list(length=None)
    return instances

@router.post("/whatsapp/instances")
async def create_whatsapp_instance(instance: WhatsAppInstanceCreate):
    """Cria nova instância WhatsApp"""
    instance_data = instance.dict()
    instance_data["id"] = str(uuid.uuid4())
    instance_data["created_at"] = datetime.now(timezone.utc).isoformat()
    instance_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.whatsapp_instances.insert_one(instance_data)
    return instance_data

@router.get("/whatsapp/instances/{instance_id}")
async def get_whatsapp_instance(instance_id: str):
    """Obter instância WhatsApp específica"""
    instance = await db.whatsapp_instances.find_one({"id": instance_id})
    if not instance:
        raise HTTPException(status_code=404, detail="Instância não encontrada")
    return instance

@router.put("/whatsapp/instances/{instance_id}")
async def update_whatsapp_instance(instance_id: str, instance: WhatsAppInstanceUpdate):
    """Atualiza instância WhatsApp"""
    update_data = {k: v for k, v in instance.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.whatsapp_instances.update_one(
        {"id": instance_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Instância não encontrada")
    
    return {"message": "Instância atualizada com sucesso"}

@router.delete("/whatsapp/instances/{instance_id}")
async def delete_whatsapp_instance(instance_id: str):
    """Deleta instância WhatsApp"""
    result = await db.whatsapp_instances.delete_one({"id": instance_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Instância não encontrada")
    
    return {"message": "Instância deletada com sucesso"}

# ==================================================================
# MERCADO PAGO CONFIG ROUTES
# ==================================================================

@router.get("/mercadopago/config")
async def get_mercadopago_config():
    """Obter configuração do Mercado Pago"""
    config = await db.mercadopago_config.find_one({})
    if not config:
        # Retornar config vazia se não existir
        return {
            "public_key": "",
            "access_token": "",
            "webhook_url": "",
            "enabled": False
        }
    return config

@router.post("/mercadopago/config")
async def update_mercadopago_config(config: MercadoPagoConfig):
    """Atualiza configuração do Mercado Pago"""
    config_data = config.dict()
    config_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Upsert: update if exists, insert if not
    await db.mercadopago_config.update_one(
        {},
        {"$set": config_data},
        upsert=True
    )
    
    return {"message": "Configuração do Mercado Pago atualizada com sucesso"}

# ==================================================================
# SUBSCRIPTIONS ROUTES
# ==================================================================

@router.get("/subscriptions")
async def list_subscriptions():
    """Lista todas as assinaturas"""
    subscriptions = await db.subscriptions.find({}).to_list(length=None)
    return subscriptions

@router.get("/subscriptions/{subscription_id}")
async def get_subscription(subscription_id: str):
    """Obter assinatura específica"""
    subscription = await db.subscriptions.find_one({"id": subscription_id})
    if not subscription:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada")
    return subscription
