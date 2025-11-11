"""
Rotas para gerenciamento de Agentes IA e Departamentos
"""
import os
from fastapi import APIRouter, HTTPException, Depends, Request, Header
from typing import List
import uuid
from datetime import datetime, timezone
from models import *
from motor.motor_asyncio import AsyncIOMotorClient
from tenant_helpers import get_tenant_filter
import jwt
from ai_agent_templates import get_template, get_all_templates

# Configuração do MongoDB
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(MONGO_URL)
db = client[os.environ.get("DB_NAME", "support_chat")]

# Configuração do JWT
JWT_SECRET = os.environ.get('JWT_SECRET', 'fallback-secret-key-change-in-production')

ai_router = APIRouter(prefix="/ai", tags=["ai-agents"])

def get_current_user(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Não autorizado")
    
    token = authorization.replace('Bearer ', '')
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Token inválido")

# ============================================
# ROTAS DE AGENTES IA
# ============================================

@ai_router.get("/agents", response_model=List[AIAgentFull])
async def list_ai_agents(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Lista todos os agentes IA da revenda"""
    # ISOLAMENTO MULTI-TENANT: Usar função centralizada
    query = get_tenant_filter(request, current_user)
    
    agents = await db.ai_agents.find(query).to_list(length=None)
    return [AIAgentFull(**agent) for agent in agents]

@ai_router.get("/agents/templates/list")
async def list_ai_templates(current_user: dict = Depends(get_current_user)):
    """Lista todos os templates de agentes IA disponíveis"""
    return get_all_templates()

@ai_router.post("/agents/templates/{template_name}")
async def create_agent_from_template(
    template_name: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Cria um agente IA a partir de um template pré-configurado"""
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # Buscar template
    template = get_template(template_name)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{template_name}' não encontrado")
    
    # ISOLAMENTO MULTI-TENANT: Determinar reseller_id do usuário
    reseller_id = current_user.get("reseller_id")
    
    # Criar agente com dados do template
    agent = {
        "id": str(uuid.uuid4()),
        "name": template["name"],
        "description": f"Agente criado a partir do template '{template_name}'",
        "who_is": template["personality"],
        "what_does": template["instructions"],
        "objective": template["instructions"],
        "how_respond": template["personality"],
        "instructions": template["instructions"],
        "avoid_topics": "",
        "avoid_words": "",
        "allowed_links": "",
        "custom_rules": "",
        "knowledge_base": template["knowledge_base"],
        "llm_provider": template["llm_provider"],
        "llm_model": template["llm_model"],
        "api_key": "",
        "temperature": template["temperature"],
        "max_tokens": template["max_tokens"],
        "auto_detect_language": True,
        "knowledge_restriction": False,
        "timezone": "America/Sao_Paulo",
        "is_active": True,
        "linked_agents": [],
        "reseller_id": reseller_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.ai_agents.insert_one(agent)
    return {"ok": True, "agent": AIAgentFull(**agent)}

@ai_router.post("/agents", response_model=AIAgentFull)
async def create_ai_agent(
    data: AIAgentCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Cria um novo agente IA"""
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # ISOLAMENTO MULTI-TENANT: Determinar reseller_id do usuário
    reseller_id = current_user.get("reseller_id")
    
    agent = {
        "id": str(uuid.uuid4()),
        "name": data.name,
        "description": data.description or "",
        "who_is": "",
        "what_does": "",
        "objective": "",
        "how_respond": "",
        "instructions": "",
        "avoid_topics": "",
        "avoid_words": "",
        "allowed_links": "",
        "custom_rules": "",
        "knowledge_base": "",
        "llm_provider": data.llm_provider,
        "llm_model": data.llm_model,
        "api_key": "",
        "temperature": 0.5,
        "max_tokens": 500,
        "auto_detect_language": True,
        "knowledge_restriction": False,
        "timezone": "America/Sao_Paulo",
        "is_active": True,
        "linked_agents": getattr(data, 'linked_agents', []),
        "reseller_id": reseller_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.ai_agents.insert_one(agent)
    return AIAgentFull(**agent)

@ai_router.get("/agents/{agent_id}", response_model=AIAgentFull)
async def get_ai_agent(
    agent_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Busca um agente IA por ID"""
    # ISOLAMENTO MULTI-TENANT: Usar função centralizada
    tenant_filter = get_tenant_filter(request, current_user)
    
    query = {"id": agent_id}
    query.update(tenant_filter)
    
    agent = await db.ai_agents.find_one(query)
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    
    return AIAgentFull(**agent)

@ai_router.put("/agents/{agent_id}", response_model=AIAgentFull)
async def update_ai_agent(
    agent_id: str,
    data: AIAgentUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Atualiza um agente IA"""
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # ISOLAMENTO MULTI-TENANT: Usar função centralizada
    tenant_filter = get_tenant_filter(request, current_user)
    
    query = {"id": agent_id}
    query.update(tenant_filter)
    
    agent = await db.ai_agents.find_one(query)
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    
    # Atualizar apenas campos fornecidos (permitir valores vazios para api_key)
    update_data = data.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.ai_agents.update_one(query, {"$set": update_data})
    
    updated_agent = await db.ai_agents.find_one(query)
    return AIAgentFull(**updated_agent)

@ai_router.delete("/agents/{agent_id}")
async def delete_ai_agent(
    agent_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Deleta um agente IA"""
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # ISOLAMENTO MULTI-TENANT: Usar função centralizada
    tenant_filter = get_tenant_filter(request, current_user)
    
    query = {"id": agent_id}
    query.update(tenant_filter)
    
    result = await db.ai_agents.delete_one(query)
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    
    return {"ok": True}

# ============================================
# ROTAS DE DEPARTAMENTOS
# ============================================

@ai_router.get("/departments", response_model=List[Department])
async def list_departments(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Lista todos os departamentos da revenda"""
    # ISOLAMENTO MULTI-TENANT: Usar função centralizada
    query = get_tenant_filter(request, current_user)
    
    departments = await db.departments.find(query).to_list(length=None)
    return [Department(**dept) for dept in departments]

@ai_router.post("/departments", response_model=Department)
async def create_department(
    data: DepartmentCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Cria um novo departamento"""
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # ISOLAMENTO MULTI-TENANT: Determinar reseller_id do usuário
    reseller_id = current_user.get("reseller_id")
    
    # Se marcar como default, desmarcar os outros
    if data.is_default:
        query = {"reseller_id": reseller_id} if reseller_id else {}
        await db.departments.update_many(query, {"$set": {"is_default": False}})
    
    department = {
        "id": str(uuid.uuid4()),
        "name": data.name,
        "description": data.description or "",
        "ai_agent_id": data.ai_agent_id,
        "is_default": data.is_default,
        "timeout_seconds": data.timeout_seconds,
        "agent_ids": data.agent_ids or [],
        "origin": data.origin or "wa_suporte",  # ✅ SALVAR ORIGIN
        "reseller_id": reseller_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    print(f"🔍 DEBUG: Criando departamento: {department['name']} com origin={department['origin']}")
    
    dept_id = department["id"]
    await db.departments.insert_one(department)
    
    print(f"✅ Departamento criado: {dept_id} - Origin: {department['origin']}")
    
    # SINCRONIZAR: Adicionar department_id aos atendentes selecionados
    if data.agent_ids:
        for agent_id in data.agent_ids:
            await db.users.update_one(
                {"id": agent_id, "user_type": "agent"},
                {"$addToSet": {"department_ids": dept_id}}
            )
    
    return Department(**department)

@ai_router.put("/departments/{dept_id}", response_model=Department)
async def update_department(
    dept_id: str,
    data: DepartmentUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Atualiza um departamento"""
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # ISOLAMENTO MULTI-TENANT: Usar função centralizada
    tenant_filter = get_tenant_filter(request, current_user)
    
    query = {"id": dept_id}
    query.update(tenant_filter)
    
    department = await db.departments.find_one(query)
    if not department:
        raise HTTPException(status_code=404, detail="Departamento não encontrado")
    
    # Se marcar como default, desmarcar os outros
    reseller_id = current_user.get("reseller_id")
    
    # Atualizar apenas campos fornecidos
    update_data = {k: v for k, v in data.dict(exclude_unset=True).items() if v is not None}
    
    # Se marcar como default, desmarcar os outros (verificar se campo existe)
    if update_data.get("is_default"):
        query_update = {"reseller_id": reseller_id} if reseller_id else {}
        await db.departments.update_many(query_update, {"$set": {"is_default": False}})
    
    print(f"🔍 DEBUG: Atualizando departamento {dept_id}")
    print(f"   Dados: {update_data}")
    
    await db.departments.update_one(query, {"$set": update_data})
    
    print(f"✅ Departamento atualizado com sucesso!")
    
    # Se agent_ids foi atualizado, sincronizar com os atendentes EM USERS
    if "agent_ids" in update_data:
        new_agent_ids = update_data["agent_ids"]
        old_agent_ids = department.get("agent_ids", [])
        
        # Remover este departamento dos atendentes que foram removidos
        removed_agents = set(old_agent_ids) - set(new_agent_ids)
        for agent_id in removed_agents:
            await db.users.update_one(
                {"id": agent_id, "user_type": "agent"},
                {"$pull": {"department_ids": dept_id}}
            )
        
        # Adicionar este departamento aos atendentes que foram adicionados
        added_agents = set(new_agent_ids) - set(old_agent_ids)
        for agent_id in added_agents:
            await db.users.update_one(
                {"id": agent_id, "user_type": "agent"},
                {"$addToSet": {"department_ids": dept_id}}
            )
    
    updated_dept = await db.departments.find_one(query)
    return Department(**updated_dept)

@ai_router.delete("/departments/{dept_id}")
async def delete_department(
    dept_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Deleta um departamento"""
    if current_user["user_type"] not in ["admin", "reseller"]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    # ISOLAMENTO MULTI-TENANT: Usar função centralizada
    tenant_filter = get_tenant_filter(request, current_user)
    
    query = {"id": dept_id}
    query.update(tenant_filter)
    
    result = await db.departments.delete_one(query)
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Departamento não encontrado")
    
    return {"ok": True}
