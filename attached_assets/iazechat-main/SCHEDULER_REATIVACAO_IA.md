# TAREFA AGENDADA: Reativar IA automaticamente após 1 hora

## Implementar em server.py:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timezone

# Criar scheduler
scheduler = AsyncIOScheduler()

async def reactivate_expired_ai_sessions():
    """
    Reativar IA para sessões onde o tempo de desativação expirou
    """
    try:
        now = datetime.now(timezone.utc)
        
        # Buscar sessões com IA desativada e tempo expirado
        sessions = await db.vendas_sessions.find({
            "ai_active": False,
            "ai_deactivated_until": {"$lte": now.isoformat()}
        }).to_list(length=100)
        
        for session in sessions:
            # Reativar IA
            await db.vendas_sessions.update_one(
                {"session_id": session["session_id"]},
                {
                    "$set": {
                        "ai_active": True,
                        "ai_deactivated_until": None,
                        "ai_reactivated_automatically": True,
                        "ai_reactivated_at": now.isoformat()
                    }
                }
            )
            logger.info(f"✅ IA reativada automaticamente: {session['session_id']}")
        
        if len(sessions) > 0:
            logger.info(f"🔄 {len(sessions)} sessões tiveram IA reativada")
            
    except Exception as e:
        logger.error(f"❌ Erro ao reativar IA: {e}")

# Agendar para rodar a cada 5 minutos
scheduler.add_job(reactivate_expired_ai_sessions, 'interval', minutes=5)
scheduler.start()
```

## Adicionar no @app.on_event("startup"):
```python
@app.on_event("startup")
async def startup_event():
    # ... código existente ...
    
    # Iniciar scheduler de reativação de IA
    scheduler.start()
    logger.info("✅ Scheduler de reativação de IA iniciado")
```
