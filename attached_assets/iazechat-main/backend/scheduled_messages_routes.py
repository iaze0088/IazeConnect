"""
Rotas para Agendamento de Mensagens
"""
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from scheduled_messages_models import ScheduleMessageRequest, ScheduledMessage
from datetime import datetime, timezone, timedelta
import uuid
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency para obter db
async def get_db(request: Request):
    return request.app.state.db

@router.post("/schedule-message")
async def schedule_message(
    request: ScheduleMessageRequest,
    db=Depends(get_db)
):
    """
    Agenda uma mensagem para ser enviada posteriormente
    """
    try:
        # Calcular datetime de envio
        if request.schedule_type == "datetime":
            if not request.datetime:
                raise HTTPException(status_code=400, detail="datetime é obrigatório")
            
            scheduled_datetime = datetime.fromisoformat(request.datetime.replace('Z', '+00:00'))
            
        elif request.schedule_type == "relative":
            if not request.hours and not request.minutes:
                raise HTTPException(status_code=400, detail="hours ou minutes é obrigatório")
            
            delta = timedelta(
                hours=request.hours or 0,
                minutes=request.minutes or 0
            )
            scheduled_datetime = datetime.now(timezone.utc) + delta
        else:
            raise HTTPException(status_code=400, detail="schedule_type inválido")
        
        # Verificar se a data é no futuro
        if scheduled_datetime <= datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Data deve ser no futuro")
        
        # Buscar ticket para obter informações
        ticket = await db.tickets.find_one({"id": request.ticket_id})
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket não encontrado")
        
        # Determinar canal baseado no ticket
        channel = "iaze_internal"  # default
        if ticket.get("whatsapp_id"):
            channel = "whatsapp_evolution"
        elif ticket.get("source") == "wa_suporte_pwa":
            channel = "wa_suporte_pwa"
        
        # Criar mensagem agendada
        scheduled_msg = {
            "id": str(uuid.uuid4()),
            "ticket_id": request.ticket_id,
            "agent_id": ticket.get("agent_id"),
            "message": request.message,
            "scheduled_datetime": scheduled_datetime.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending",
            "channel": channel,
            "client_name": ticket.get("client_name"),
            "whatsapp": ticket.get("whatsapp")
        }
        
        await db.scheduled_messages.insert_one(scheduled_msg)
        
        logger.info(f"✅ Mensagem agendada: {scheduled_msg['id']} para {scheduled_datetime}")
        
        return {
            "success": True,
            "scheduled_id": scheduled_msg["id"],
            "scheduled_for": scheduled_datetime.isoformat(),
            "message": "Mensagem agendada com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao agendar mensagem: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scheduled-messages")
async def list_scheduled_messages(
    ticket_id: str = None,
    status: str = None,
    db=Depends(get_db)
):
    """
    Lista mensagens agendadas
    """
    try:
        query = {}
        
        if ticket_id:
            query["ticket_id"] = ticket_id
        
        if status:
            query["status"] = status
        
        messages = await db.scheduled_messages.find(query).sort(
            "scheduled_datetime", 1
        ).to_list(length=100)
        
        for msg in messages:
            msg.pop("_id", None)
        
        return {
            "success": True,
            "messages": messages
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar mensagens agendadas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/scheduled-message/{message_id}")
async def cancel_scheduled_message(message_id: str, db=Depends(get_db)):
    """
    Cancela uma mensagem agendada
    """
    try:
        result = await db.scheduled_messages.update_one(
            {"id": message_id, "status": "pending"},
            {"$set": {"status": "cancelled"}}
        )
        
        if result.modified_count > 0:
            return {
                "success": True,
                "message": "Mensagem cancelada com sucesso"
            }
        else:
            raise HTTPException(status_code=404, detail="Mensagem não encontrada ou já foi enviada")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao cancelar mensagem: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-scheduled-messages")
async def process_scheduled_messages(db=Depends(get_db)):
    """
    Processa e envia mensagens agendadas que já passaram do horário
    (Chamado por cron/scheduler a cada minuto)
    """
    try:
        now = datetime.now(timezone.utc)
        
        # Buscar mensagens pendentes que já passaram do horário
        messages = await db.scheduled_messages.find({
            "status": "pending",
            "scheduled_datetime": {"$lte": now.isoformat()}
        }).to_list(length=50)
        
        sent_count = 0
        
        for msg in messages:
            try:
                # Buscar ticket
                ticket = await db.tickets.find_one({"id": msg["ticket_id"]})
                
                if not ticket:
                    logger.warning(f"⚠️ Ticket {msg['ticket_id']} não encontrado")
                    await db.scheduled_messages.update_one(
                        {"id": msg["id"]},
                        {"$set": {"status": "failed", "error": "Ticket não encontrado"}}
                    )
                    continue
                
                # Criar mensagem no ticket
                message_doc = {
                    "message_id": str(uuid.uuid4()),
                    "ticket_id": msg["ticket_id"],
                    "from_type": "agent",
                    "from_name": "Sistema (Agendado)",
                    "text": msg["message"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "is_scheduled": True
                }
                
                await db.messages.insert_one(message_doc)
                
                # Atualizar status da mensagem agendada
                await db.scheduled_messages.update_one(
                    {"id": msg["id"]},
                    {"$set": {
                        "status": "sent",
                        "sent_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                
                sent_count += 1
                logger.info(f"✅ Mensagem agendada enviada: {msg['id']}")
                
                # TODO: Integrar com WhatsApp Evolution ou WA Suporte PWA se necessário
                # Por enquanto, apenas cria a mensagem no IAZE
                
            except Exception as e:
                logger.error(f"❌ Erro ao enviar mensagem agendada {msg['id']}: {e}")
                await db.scheduled_messages.update_one(
                    {"id": msg["id"]},
                    {"$set": {"status": "failed", "error": str(e)}}
                )
        
        return {
            "success": True,
            "processed": len(messages),
            "sent": sent_count
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar mensagens agendadas: {e}")
        raise HTTPException(status_code=500, detail=str(e))
