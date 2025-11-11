"""
Scheduler para sincronização automática dos clientes Office
Roda a cada 6 horas automaticamente
"""
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class OfficeSyncScheduler:
    """Agendador de sincronização automática"""
    
    def __init__(self, sync_service):
        self.sync_service = sync_service
        self.scheduler = AsyncIOScheduler()
    
    def start(self):
        """Iniciar agendador"""
        
        # Sincronizar a cada 6 horas
        self.scheduler.add_job(
            self._run_sync,
            CronTrigger(hour="*/6"),  # 00:00, 06:00, 12:00, 18:00
            id="office_sync_6h",
            name="Sincronização Office a cada 6 horas",
            replace_existing=True
        )
        
        # Também executar ao iniciar (opcional - comentar se não quiser)
        self.scheduler.add_job(
            self._run_sync,
            'date',
            run_date=datetime.now(timezone.utc),
            id="office_sync_startup",
            name="Sincronização inicial ao iniciar",
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("✅ Office Sync Scheduler iniciado (sincronização a cada 6 horas)")
    
    async def _run_sync(self):
        """Executar sincronização"""
        try:
            logger.info("⏰ Iniciando sincronização agendada...")
            result = await self.sync_service.sync_all_clients()
            logger.info(f"✅ Sincronização agendada concluída: {result['summary']}")
        except Exception as e:
            logger.error(f"❌ Erro na sincronização agendada: {e}")
    
    def stop(self):
        """Parar agendador"""
        self.scheduler.shutdown()
        logger.info("🛑 Office Sync Scheduler parado")
