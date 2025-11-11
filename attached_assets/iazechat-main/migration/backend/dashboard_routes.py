"""
Rotas do Dashboard - Estatísticas e métricas em tempo real
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

def get_db_dep():
    from server import db
    return db

def get_current_user(request):
    from server import get_current_user as gcu
    return gcu

@router.get("/admin/dashboard/stats")
@router.get("/dashboard/admin-stats")  # Alias para compatibilidade
async def get_dashboard_stats(
    request: Request,
    current_user: dict = Depends(get_current_user),
    reseller_id: Optional[str] = None
):
    """Obter estatísticas gerais do dashboard com filtro opcional por revenda"""
    from tenant_helpers import get_request_tenant
    
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Apenas admin")
    
    db = get_db_dep()
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Determinar filtro baseado no domínio ou parâmetro
    tenant = get_request_tenant(request)
    filter_reseller_id = reseller_id or tenant.reseller_id
    
    # Construir query base
    query = {}
    if filter_reseller_id:
        query["reseller_id"] = filter_reseller_id
    
    # Total de tickets/conversas
    total_tickets = await db.tickets.count_documents(query)
    
    # Tickets em entrada (status: open, não atribuído)
    entrada_query = {**query, "status": "open", "agent_id": {"$exists": False}}
    tickets_entrada = await db.tickets.count_documents(entrada_query)
    
    # Em atendimento (status: open, com agente)
    atendimento_query = {**query, "status": "open", "agent_id": {"$exists": True}}
    tickets_atendimento = await db.tickets.count_documents(atendimento_query)
    
    # Finalizadas hoje
    finalizadas_query = {
        **query,
        "status": "closed",
        "updated_at": {"$gte": today_start.isoformat()}
    }
    tickets_finalizadas_hoje = await db.tickets.count_documents(finalizadas_query)
    
    # Total de mensagens hoje
    msg_query = {**query, "timestamp": {"$gte": today_start.isoformat()}}
    mensagens_hoje = await db.messages.count_documents(msg_query)
    
    # Tempo médio de resposta (simplificado)
    tempo_medio = "< 5min"  # Placeholder
    
    return {
        "total_tickets": total_tickets,
        "tickets_entrada": tickets_entrada,
        "tickets_atendimento": tickets_atendimento,
        "tickets_finalizadas_hoje": tickets_finalizadas_hoje,
        "mensagens_hoje": mensagens_hoje,
        "tempo_medio_resposta": tempo_medio,
        "filtered_by_reseller": filter_reseller_id
    }

@router.get("/admin/dashboard/agents-online")
async def get_agents_online(
    request: Request,
    current_user: dict = Depends(get_current_user),
    reseller_id: Optional[str] = None
):
    """Obter lista de atendentes online com filtro opcional por revenda"""
    from tenant_helpers import get_request_tenant
    
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Apenas admin")
    
    db = get_db_dep()
    
    # Determinar filtro baseado no domínio ou parâmetro
    tenant = get_request_tenant(request)
    filter_reseller_id = reseller_id or tenant.reseller_id
    
    # Construir query
    query = {"user_type": "agent"}
    if filter_reseller_id:
        query["reseller_id"] = filter_reseller_id
    
    # Buscar agentes
    agents = await db.users.find(
        query,
        {"_id": 0, "id": 1, "name": 1, "email": 1, "last_seen": 1, "reseller_id": 1}
    ).to_list(None)
    
    now = datetime.now(timezone.utc)
    five_min_ago = now - timedelta(minutes=5)
    
    agents_with_status = []
    for agent in agents:
        last_seen = agent.get("last_seen")
        is_online = False
        
        if last_seen:
            try:
                last_seen_dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                is_online = last_seen_dt > five_min_ago
            except:
                is_online = False
        
        # Contar tickets ativos do agente
        ticket_query = {"agent_id": agent["id"], "status": "open"}
        if filter_reseller_id:
            ticket_query["reseller_id"] = filter_reseller_id
        
        active_tickets = await db.tickets.count_documents(ticket_query)
        
        agents_with_status.append({
            "id": agent["id"],
            "name": agent["name"],
            "email": agent["email"],
            "is_online": is_online,
            "active_tickets": active_tickets,
            "last_seen": last_seen or "Nunca",
            "reseller_id": agent.get("reseller_id")
        })
    
    online_agents = [a for a in agents_with_status if a["is_online"]]
    offline_agents = [a for a in agents_with_status if not a["is_online"]]
    
    return {
        "total": len(agents_with_status),
        "online_count": len(online_agents),
        "offline_count": len(offline_agents),
        "online_agents": online_agents,
        "offline_agents": offline_agents,
        "filtered_by_reseller": filter_reseller_id
    }

@router.get("/admin/dashboard/monitor-agent/{agent_id}")
async def monitor_agent(
    agent_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Monitorar atividade de um agente específico (tickets ativos e mensagens recentes)"""
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Apenas admin")
    
    db = get_db_dep()
    
    # Buscar informações do agente
    agent = await db.users.find_one(
        {"id": agent_id, "user_type": "agent"},
        {"_id": 0, "id": 1, "name": 1, "email": 1, "last_seen": 1}
    )
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    
    # Buscar tickets ativos do agente
    active_tickets = await db.tickets.find(
        {"agent_id": agent_id, "status": "open"},
        {"_id": 0}
    ).sort("updated_at", -1).to_list(10)  # Últimos 10
    
    # Para cada ticket, buscar última mensagem
    for ticket in active_tickets:
        last_msg = await db.messages.find_one(
            {"ticket_id": ticket["id"]},
            {"_id": 0},
            sort=[("created_at", -1)]
        )
        ticket["last_message"] = last_msg
        
        # Buscar cliente
        client = await db.users.find_one({"id": ticket["client_id"]}) or \
                 await db.clients.find_one({"id": ticket["client_id"]})
        if client:
            ticket["client_name"] = client.get("display_name") or client.get("name", "Desconhecido")
    
    # Estatísticas do agente
    total_tickets_today = await db.tickets.count_documents({
        "agent_id": agent_id,
        "created_at": {"$gte": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0).isoformat()}
    })
    
    closed_today = await db.tickets.count_documents({
        "agent_id": agent_id,
        "status": "closed",
        "updated_at": {"$gte": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0).isoformat()}
    })
    
    return {
        "agent": agent,
        "active_tickets": active_tickets,
        "stats": {
            "active_count": len(active_tickets),
            "total_today": total_tickets_today,
            "closed_today": closed_today
        }
    }

@router.get("/admin/dashboard/ai-agents-status")
async def get_ai_agents_status(current_user: dict = Depends(get_current_user)):
    """Obter status dos agentes de IA"""
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Apenas admin")
    
    db = get_db_dep()
    
    # Buscar configuração de IA
    config = await db.config.find_one({"id": "global_config"}, {"_id": 0})
    
    ai_agents = []
    
    if config and config.get("ai_agent"):
        ai_config = config["ai_agent"]
        
        # Verificar se IA está habilitada
        enabled = ai_config.get("enabled", False)
        
        if enabled:
            # Contar interações de IA hoje
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            
            ai_messages_today = await db.messages.count_documents({
                "sender_type": "ai",
                "timestamp": {"$gte": today_start.isoformat()}
            })
            
            ai_agents.append({
                "name": "Agente IA Principal",
                "status": "active",
                "enabled": True,
                "interactions_today": ai_messages_today,
                "model": ai_config.get("model", "N/A")
            })
        else:
            ai_agents.append({
                "name": "Agente IA Principal",
                "status": "disabled",
                "enabled": False,
                "interactions_today": 0,
                "model": "N/A"
            })
    else:
        ai_agents.append({
            "name": "Agente IA Principal",
            "status": "not_configured",
            "enabled": False,
            "interactions_today": 0,
            "model": "N/A"
        })
    
    active_count = sum(1 for a in ai_agents if a["status"] == "active")
    
    return {
        "total": len(ai_agents),
        "active_count": active_count,
        "agents": ai_agents
    }


# ========================================
# ENDPOINTS PARA RESELLER DASHBOARD
# ========================================

@router.get("/reseller/dashboard/stats")
async def get_reseller_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Obter estatísticas do dashboard do reseller (ISOLAMENTO TOTAL)"""
    if current_user.get("user_type") != "reseller":
        raise HTTPException(status_code=403, detail="Apenas revendedores")
    
    reseller_id = current_user.get("reseller_id")
    if not reseller_id:
        raise HTTPException(status_code=400, detail="Reseller ID não encontrado")
    
    db = get_db_dep()
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # ISOLAMENTO: apenas tickets deste reseller
    total_tickets = await db.tickets.count_documents({"reseller_id": reseller_id})
    
    tickets_entrada = await db.tickets.count_documents({
        "reseller_id": reseller_id,
        "status": "open",
        "agent_id": {"$exists": False}
    })
    
    tickets_atendimento = await db.tickets.count_documents({
        "reseller_id": reseller_id,
        "status": "open",
        "agent_id": {"$exists": True}
    })
    
    tickets_finalizadas_hoje = await db.tickets.count_documents({
        "reseller_id": reseller_id,
        "status": "closed",
        "updated_at": {"$gte": today_start.isoformat()}
    })
    
    mensagens_hoje = await db.messages.count_documents({
        "reseller_id": reseller_id,
        "timestamp": {"$gte": today_start.isoformat()}
    })
    
    tempo_medio = "< 5min"
    
    return {
        "total_tickets": total_tickets,
        "tickets_entrada": tickets_entrada,
        "tickets_atendimento": tickets_atendimento,
        "tickets_finalizadas_hoje": tickets_finalizadas_hoje,
        "mensagens_hoje": mensagens_hoje,
        "tempo_medio_resposta": tempo_medio
    }


@router.get("/reseller/dashboard/agents-online")
async def get_reseller_agents_online(current_user: dict = Depends(get_current_user)):
    """Obter atendentes online do reseller (ISOLAMENTO TOTAL)"""
    if current_user.get("user_type") != "reseller":
        raise HTTPException(status_code=403, detail="Apenas revendedores")
    
    reseller_id = current_user.get("reseller_id")
    if not reseller_id:
        raise HTTPException(status_code=400, detail="Reseller ID não encontrado")
    
    db = get_db_dep()
    
    # ISOLAMENTO: apenas agentes deste reseller
    agents = await db.users.find(
        {"user_type": "agent", "reseller_id": reseller_id},
        {"_id": 0, "id": 1, "name": 1, "email": 1, "last_seen": 1}
    ).to_list(None)
    
    now = datetime.now(timezone.utc)
    five_min_ago = now - timedelta(minutes=5)
    
    agents_with_status = []
    for agent in agents:
        last_seen = agent.get("last_seen")
        is_online = False
        
        if last_seen:
            try:
                last_seen_dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                is_online = last_seen_dt > five_min_ago
            except:
                is_online = False
        
        # ISOLAMENTO: contar apenas tickets deste reseller
        active_tickets = await db.tickets.count_documents({
            "reseller_id": reseller_id,
            "agent_id": agent["id"],
            "status": "open"
        })
        
        agents_with_status.append({
            "id": agent["id"],
            "name": agent["name"],
            "email": agent["email"],
            "is_online": is_online,
            "active_tickets": active_tickets,
            "last_seen": last_seen or "Nunca"
        })
    
    online_agents = [a for a in agents_with_status if a["is_online"]]
    offline_agents = [a for a in agents_with_status if not a["is_online"]]
    
    return {
        "total": len(agents_with_status),
        "online_count": len(online_agents),
        "offline_count": len(offline_agents),
        "online_agents": online_agents,
        "offline_agents": offline_agents
    }


@router.get("/reseller/dashboard/ai-agents-status")
async def get_reseller_ai_agents_status(current_user: dict = Depends(get_current_user)):
    """Obter status dos agentes de IA do reseller (ISOLAMENTO TOTAL)"""
    if current_user.get("user_type") != "reseller":
        raise HTTPException(status_code=403, detail="Apenas revendedores")
    
    reseller_id = current_user.get("reseller_id")
    if not reseller_id:
        raise HTTPException(status_code=400, detail="Reseller ID não encontrado")
    
    db = get_db_dep()
    
    # ISOLAMENTO: buscar config deste reseller apenas
    config = await db.reseller_configs.find_one({"reseller_id": reseller_id}, {"_id": 0})
    
    ai_agents = []
    
    if config and config.get("ai_agent"):
        ai_config = config["ai_agent"]
        enabled = ai_config.get("enabled", False)
        
        if enabled:
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            
            # ISOLAMENTO: contar apenas mensagens de IA deste reseller
            ai_messages_today = await db.messages.count_documents({
                "reseller_id": reseller_id,
                "sender_type": "ai",
                "timestamp": {"$gte": today_start.isoformat()}
            })
            
            ai_agents.append({
                "name": "Agente IA Principal",
                "status": "active",
                "enabled": True,
                "interactions_today": ai_messages_today,
                "model": ai_config.get("model", "N/A")
            })
        else:
            ai_agents.append({
                "name": "Agente IA Principal",
                "status": "disabled",
                "enabled": False,
                "interactions_today": 0,
                "model": "N/A"
            })
    else:
        ai_agents.append({
            "name": "Agente IA Principal",
            "status": "not_configured",
            "enabled": False,
            "interactions_today": 0,
            "model": "N/A"
        })
    
    active_count = sum(1 for a in ai_agents if a["status"] == "active")
    
    return {
        "total": len(ai_agents),
        "active_count": active_count,
        "agents": ai_agents
    }


# ========================================
# ENDPOINTS PARA "AVISO IMPORTANTE"
# ========================================

@router.get("/admin/dashboard/important-alerts")
async def get_admin_important_alerts(current_user: dict = Depends(get_current_user)):
    """Obter avisos importantes para o Admin (WhatsApp, IA, Manutenção)"""
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Apenas admin")
    
    db = get_db_dep()
    alerts = []
    
    # 1. Verificar WhatsApp desconectado (todas as conexões)
    whatsapp_connections = await db.whatsapp_connections.find({}, {"_id": 0}).to_list(None)
    disconnected_count = sum(1 for conn in whatsapp_connections if conn.get("status") != "connected")
    
    if disconnected_count > 0:
        alerts.append({
            "type": "whatsapp",
            "severity": "warning",
            "title": "WhatsApp Desconectado",
            "message": f"{disconnected_count} conexão(ões) WhatsApp desconectada(s)",
            "icon": "📱"
        })
    
    # 2. Verificar IA parada (global)
    config = await db.config.find_one({"id": "global_config"}, {"_id": 0})
    if config and config.get("ai_agent"):
        ai_enabled = config["ai_agent"].get("enabled", False)
        if not ai_enabled:
            alerts.append({
                "type": "ai",
                "severity": "info",
                "title": "IA Desativada",
                "message": "Agente de IA está desativado no sistema",
                "icon": "🤖"
            })
    
    # 3. Avisos de manutenção do Admin (collection system_notices)
    system_notices = await db.system_notices.find(
        {"active": True, "target": "all"},
        {"_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    for notice in system_notices:
        alerts.append({
            "type": "maintenance",
            "severity": notice.get("severity", "info"),
            "title": notice.get("title", "Aviso de Manutenção"),
            "message": notice.get("message", ""),
            "icon": "🔧"
        })
    
    return {"alerts": alerts, "total": len(alerts)}


@router.get("/reseller/dashboard/important-alerts")
async def get_reseller_important_alerts(current_user: dict = Depends(get_current_user)):
    """Obter avisos importantes para o Reseller (ISOLAMENTO TOTAL)"""
    if current_user.get("user_type") != "reseller":
        raise HTTPException(status_code=403, detail="Apenas revendedores")
    
    reseller_id = current_user.get("reseller_id")
    if not reseller_id:
        raise HTTPException(status_code=400, detail="Reseller ID não encontrado")
    
    db = get_db_dep()
    alerts = []
    
    # 1. Verificar WhatsApp desconectado (ISOLAMENTO: apenas deste reseller)
    whatsapp_connections = await db.whatsapp_connections.find(
        {"reseller_id": reseller_id},
        {"_id": 0}
    ).to_list(None)
    
    disconnected_count = sum(1 for conn in whatsapp_connections if conn.get("status") != "connected")
    
    if disconnected_count > 0:
        alerts.append({
            "type": "whatsapp",
            "severity": "warning",
            "title": "WhatsApp Desconectado",
            "message": f"{disconnected_count} conexão(ões) WhatsApp desconectada(s)",
            "icon": "📱"
        })
    
    # 2. Verificar IA parada (ISOLAMENTO: config deste reseller)
    config = await db.reseller_configs.find_one({"reseller_id": reseller_id}, {"_id": 0})
    if config and config.get("ai_agent"):
        ai_enabled = config["ai_agent"].get("enabled", False)
        if not ai_enabled:
            alerts.append({
                "type": "ai",
                "severity": "info",
                "title": "IA Desativada",
                "message": "Agente de IA está desativado no seu sistema",
                "icon": "🤖"
            })
    
    # 3. Avisos de manutenção do Admin (enviados para resellers)
    system_notices = await db.system_notices.find(
        {
            "active": True,
            "$or": [
                {"target": "all"},
                {"target": "resellers"},
                {"target_reseller_id": reseller_id}
            ]
        },
        {"_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    for notice in system_notices:
        alerts.append({
            "type": "maintenance",
            "severity": notice.get("severity", "info"),
            "title": notice.get("title", "Aviso de Manutenção"),
            "message": notice.get("message", ""),
            "icon": "🔧"
        })
    
    return {"alerts": alerts, "total": len(alerts)}
