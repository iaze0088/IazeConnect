"""
Rotas para Sistema de Lembretes de Vencimento
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from reminder_models import AddClientEmailRequest, ReminderConfigUpdate, ClientEmail
from reminder_service import reminder_service
from office_service_playwright import office_service_playwright
from datetime import datetime, timezone, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency para obter db
async def get_db(request: Request):
    return request.app.state.db

# ===== GERENCIAMENTO DE EMAILS =====

@router.post("/client-email")
async def add_client_email(
    request: AddClientEmailRequest,
    db=Depends(get_db)
):
    """Adiciona email de um cliente"""
    try:
        # Verificar se já existe
        existing = await db.client_emails.find_one({
            "usuario": request.usuario,
            "active": True
        })
        
        if existing:
            # Atualizar
            await db.client_emails.update_one(
                {"usuario": request.usuario},
                {"$set": {
                    "email": request.email,
                    "nome": request.nome,
                    "office_credential_id": request.office_credential_id
                }}
            )
            message = "Email atualizado"
        else:
            # Criar novo
            client_email = {
                "id": str(uuid.uuid4()),
                "usuario": request.usuario,
                "email": request.email,
                "nome": request.nome,
                "office_credential_id": request.office_credential_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "active": True
            }
            await db.client_emails.insert_one(client_email)
            message = "Email cadastrado"
        
        return {
            "success": True,
            "message": message
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao adicionar email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/client-emails")
async def list_client_emails(
    db=Depends(get_db)
):
    """Lista todos os emails cadastrados"""
    try:
        emails = await db.client_emails.find(
            {"active": True}
        ).to_list(length=None)
        
        for email in emails:
            email.pop("_id", None)
        
        return {
            "success": True,
            "emails": emails
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/client-email/{usuario}")
async def delete_client_email(usuario: str, db=Depends(get_db)):
    """Remove email de um cliente"""
    try:
        result = await db.client_emails.update_one(
            {"usuario": usuario},
            {"$set": {"active": False}}
        )
        
        if result.modified_count > 0:
            return {"success": True, "message": "Email removido"}
        else:
            raise HTTPException(status_code=404, detail="Email não encontrado")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao deletar email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== CONFIGURAÇÃO DE LEMBRETES =====

@router.get("/reminder-config")
async def get_reminder_config(db=Depends(get_db)):
    """Obtém configuração de lembretes"""
    try:
        config = await db.reminder_config.find_one({"id": "reminder_config"})
        
        if not config:
            # Criar configuração padrão
            default_config = {
                "id": "reminder_config",
                "enabled": False,
                "days_before": [3, 2, 1],
                "send_expired": True,
                "send_time": "09:00",
                "smtp_host": "",
                "smtp_port": 587,
                "smtp_user": "",
                "smtp_password": "",
                "from_email": "",
                "from_name": "Atendimento"
            }
            await db.reminder_config.insert_one(default_config)
            config = default_config
        
        config.pop("_id", None)
        
        return {
            "success": True,
            "config": config
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/reminder-config")
async def update_reminder_config(
    update: ReminderConfigUpdate,
    db=Depends(get_db)
):
    """Atualiza configuração de lembretes"""
    try:
        update_data = {k: v for k, v in update.dict().items() if v is not None}
        
        await db.reminder_config.update_one(
            {"id": "reminder_config"},
            {"$set": update_data},
            upsert=True
        )
        
        return {
            "success": True,
            "message": "Configuração atualizada"
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== PROCESSAMENTO DE LEMBRETES =====

@router.post("/process-reminders")
async def process_reminders(db=Depends(get_db)):
    """
    Processa lembretes de vencimento
    (Chamado pelo scheduler)
    """
    try:
        # Verificar se está habilitado
        config = await db.reminder_config.find_one({"id": "reminder_config"})
        
        if not config or not config.get("enabled", False):
            return {
                "success": True,
                "message": "Lembretes desabilitados",
                "sent": 0
            }
        
        # Verificar se tem SMTP configurado
        if not config.get("smtp_host") or not config.get("smtp_user"):
            logger.warning("⚠️ SMTP não configurado")
            return {
                "success": False,
                "error": "SMTP não configurado",
                "sent": 0
            }
        
        # Pegar todos os clientes com email
        client_emails = await db.client_emails.find(
            {"active": True}
        ).to_list(length=None)
        
        if not client_emails:
            return {
                "success": True,
                "message": "Nenhum cliente com email cadastrado",
                "sent": 0
            }
        
        # Pegar credenciais do Office
        office_credentials = await db.office_credentials.find(
            {"active": True}
        ).to_list(length=None)
        
        sent_count = 0
        errors = []
        
        # Para cada cliente com email
        for client_email in client_emails:
            try:
                usuario = client_email["usuario"]
                
                # Buscar dados no Office
                client_data = None
                for cred in office_credentials:
                    result = await office_service_playwright.buscar_cliente(
                        {
                            "username": cred["username"],
                            "password": cred["password"]
                        },
                        usuario
                    )
                    
                    if result and result.get("success"):
                        client_data = result
                        break
                
                if not client_data:
                    logger.warning(f"⚠️ Cliente {usuario} não encontrado no Office")
                    continue
                
                # Verificar vencimento
                vencimento_str = client_data.get("vencimento")
                
                if not vencimento_str or vencimento_str in ["NUNCA", "ILIMITADO"]:
                    continue  # Cliente ilimitado
                
                # Parsear data de vencimento
                try:
                    vencimento = datetime.fromisoformat(vencimento_str.replace(' ', 'T'))
                except:
                    # Tentar outros formatos
                    try:
                        vencimento = datetime.strptime(vencimento_str, "%Y-%m-%d %H:%M:%S")
                    except:
                        logger.warning(f"⚠️ Data inválida para {usuario}: {vencimento_str}")
                        continue
                
                # Calcular dias até vencimento
                days_until = (vencimento.date() - datetime.now(timezone.utc).date()).days
                
                # Verificar se deve enviar
                should_send = False
                
                if days_until in config.get("days_before", [3, 2, 1]):
                    should_send = True
                elif days_until < 0 and config.get("send_expired", True):
                    should_send = True
                
                if should_send:
                    # Gerar email
                    client_data_with_name = {
                        **client_data,
                        "nome": client_email.get("nome", "Cliente")
                    }
                    
                    html = reminder_service.generate_reminder_email(
                        client_data_with_name,
                        days_until
                    )
                    
                    # Definir assunto
                    if days_until > 0:
                        subject = f"⚠️ Sua assinatura vence em {days_until} dia(s)"
                    elif days_until == 0:
                        subject = "🚨 Sua assinatura vence HOJE!"
                    else:
                        subject = f"❌ Sua assinatura venceu há {abs(days_until)} dia(s)"
                    
                    # Enviar email
                    smtp_config = {
                        "smtp_host": config["smtp_host"],
                        "smtp_port": config["smtp_port"],
                        "smtp_user": config["smtp_user"],
                        "smtp_password": config["smtp_password"],
                        "from_email": config["from_email"],
                        "from_name": config["from_name"]
                    }
                    
                    success = reminder_service.send_email(
                        smtp_config,
                        client_email["email"],
                        subject,
                        html
                    )
                    
                    if success:
                        sent_count += 1
                        
                        # Salvar log
                        await db.reminder_logs.insert_one({
                            "id": str(uuid.uuid4()),
                            "usuario": usuario,
                            "email": client_email["email"],
                            "days_until": days_until,
                            "sent_at": datetime.now(timezone.utc).isoformat(),
                            "status": "sent"
                        })
                    else:
                        errors.append(f"Falha ao enviar para {usuario}")
                
            except Exception as e:
                logger.error(f"❌ Erro ao processar {client_email.get('usuario')}: {e}")
                errors.append(str(e))
        
        return {
            "success": True,
            "sent": sent_count,
            "processed": len(client_emails),
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar lembretes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reminder-logs")
async def get_reminder_logs(
    limit: int = 50,
    db=Depends(get_db)
):
    """Lista logs de envios de lembretes"""
    try:
        logs = await db.reminder_logs.find().sort(
            "sent_at", -1
        ).limit(limit).to_list(length=limit)
        
        for log in logs:
            log.pop("_id", None)
        
        return {
            "success": True,
            "logs": logs
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-reminder-email")
async def test_reminder_email(
    test_email: str,
    db=Depends(get_db)
):
    """Envia email de teste"""
    try:
        config = await db.reminder_config.find_one({"id": "reminder_config"})
        
        if not config or not config.get("smtp_host"):
            raise HTTPException(status_code=400, detail="SMTP não configurado")
        
        # Gerar email de teste
        test_data = {
            "usuario": "teste123",
            "senha": "teste456",
            "vencimento": "2025-11-05 10:00:00",
            "nome": "Cliente Teste"
        }
        
        html = reminder_service.generate_reminder_email(test_data, 2)
        
        smtp_config = {
            "smtp_host": config["smtp_host"],
            "smtp_port": config["smtp_port"],
            "smtp_user": config["smtp_user"],
            "smtp_password": config["smtp_password"],
            "from_email": config["from_email"],
            "from_name": config["from_name"]
        }
        
        success = reminder_service.send_email(
            smtp_config,
            test_email,
            "🧪 Email de Teste - Lembrete de Vencimento",
            html
        )
        
        if success:
            return {
                "success": True,
                "message": f"Email de teste enviado para {test_email}"
            }
        else:
            raise HTTPException(status_code=500, detail="Falha ao enviar email")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao enviar email de teste: {e}")
        raise HTTPException(status_code=500, detail=str(e))
