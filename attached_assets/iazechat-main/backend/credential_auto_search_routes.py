"""
Rotas para Auto-Busca de Credenciais
"""
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid
import logging
from credential_auto_search import credential_auto_search
from office_service_playwright import office_service_playwright

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency para obter db
async def get_db(request: Request):
    return request.app.state.db

class AutoSearchRequest(BaseModel):
    """Request para busca automática"""
    ticket_id: str
    whatsapp: str
    source: str  # "wa_suporte_pwa", "whatsapp_evolution", etc

@router.post("/auto-search-credentials")
async def auto_search_credentials(
    request: AutoSearchRequest,
    background_tasks: BackgroundTasks,
    db=Depends(get_db)
):
    """
    Busca automática de credenciais por telefone e fixa na conversa
    (Chamado automaticamente quando cliente envia primeira mensagem do dia)
    """
    try:
        # 1. Verificar se é WA SUPORTE
        if request.source != "wa_suporte_pwa":
            return {
                "success": False,
                "message": "Busca automática apenas para WA SUPORTE",
                "searched": False
            }
        
        # 2. Verificar se já buscou hoje
        ticket = await db.tickets.find_one({"id": request.ticket_id})
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket não encontrado")
        
        last_search = ticket.get("credentials_last_search")
        
        if not credential_auto_search.should_search_today(last_search):
            logger.info(f"⏭️ Credenciais já buscadas hoje para {request.whatsapp}")
            return {
                "success": True,
                "message": "Já buscado hoje",
                "searched": False
            }
        
        # 3. Buscar credenciais do Office
        office_credentials = await db.office_credentials.find(
            {"active": True}
        ).to_list(length=None)
        
        if not office_credentials:
            logger.warning("⚠️ Nenhuma credencial do Office cadastrada")
            return {
                "success": False,
                "message": "Nenhum Office cadastrado",
                "searched": False
            }
        
        # 4. Executar busca em background (não bloquear resposta)
        background_tasks.add_task(
            process_credential_search,
            request.ticket_id,
            request.whatsapp,
            office_credentials,
            db
        )
        
        return {
            "success": True,
            "message": "Busca iniciada em background",
            "searched": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro na busca automática: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_credential_search(
    ticket_id: str,
    whatsapp: str,
    office_credentials: list,
    db
):
    """
    Processa busca de credenciais em background
    """
    try:
        logger.info(f"🔍 Iniciando busca automática para {whatsapp}")
        
        # Buscar credenciais
        result = await credential_auto_search.search_credentials_by_phone(
            whatsapp,
            office_credentials,
            office_service_playwright
        )
        
        # Atualizar ticket com data da busca
        await db.tickets.update_one(
            {"id": ticket_id},
            {"$set": {
                "credentials_last_search": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        if result and result.get("success"):
            logger.info(f"✅ Credenciais encontradas para {whatsapp}")
            
            # Montar texto das credenciais
            usuario = result.get("usuario", "N/A")
            senha = result.get("senha", "N/A")
            vencimento = result.get("vencimento", "N/A")
            status = result.get("status", "N/A")
            
            credentials_text = f"""🔐 **Credenciais do Cliente**

👤 **Usuário:** {usuario}
🔑 **Senha:** {senha}
📅 **Vencimento:** {vencimento}
📊 **Status:** {status}

_Localizado automaticamente via telefone_"""
            
            # Fixar credenciais na conversa
            await db.tickets.update_one(
                {"id": ticket_id},
                {"$set": {
                    "pinned_credentials": credentials_text,
                    "credentials_found": True,
                    "credentials_data": {
                        "usuario": usuario,
                        "senha": senha,
                        "vencimento": vencimento,
                        "status": status,
                        "phone_format_used": result.get("phone_used"),
                        "office_used": result.get("office_used"),
                        "found_at": datetime.now(timezone.utc).isoformat()
                    }
                }}
            )
            
            logger.info(f"📌 Credenciais fixadas no ticket {ticket_id}")
            
        else:
            logger.warning(f"❌ Credenciais não encontradas para {whatsapp}")
            
            await db.tickets.update_one(
                {"id": ticket_id},
                {"$set": {
                    "credentials_found": False
                }}
            )
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar busca de credenciais: {e}")

@router.get("/ticket/{ticket_id}/credentials-status")
async def get_credentials_status(ticket_id: str, db=Depends(get_db)):
    """
    Verifica status da busca de credenciais
    """
    try:
        ticket = await db.tickets.find_one({"id": ticket_id})
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket não encontrado")
        
        return {
            "success": True,
            "credentials_found": ticket.get("credentials_found", False),
            "pinned_credentials": ticket.get("pinned_credentials"),
            "credentials_data": ticket.get("credentials_data"),
            "last_search": ticket.get("credentials_last_search")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao verificar status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
