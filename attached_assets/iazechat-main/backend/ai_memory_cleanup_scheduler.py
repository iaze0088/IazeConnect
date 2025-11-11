"""
Scheduler para limpeza automática de memórias da IA
Executa diariamente às 3:00 AM
"""
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from ai_memory_cleanup_service import ai_memory_cleanup_service

logger = logging.getLogger(__name__)

class AIMemoryCleanupScheduler:
    """
    Scheduler para executar limpeza automática de memórias antigas
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
    
    async def run_cleanup(self):
        """
        Executar limpeza de memórias
        """
        try:
            logger.info("🔄 Iniciando job de limpeza de memórias da IA...")
            await ai_memory_cleanup_service.cleanup_old_conversations()
            logger.info("✅ Job de limpeza de memórias concluído")
        except Exception as e:
            logger.error(f"❌ Erro no job de limpeza de memórias: {e}")
    
    def start(self):
        """
        Iniciar scheduler
        """
        try:
            # Executar diariamente às 3:00 AM
            self.scheduler.add_job(
                self.run_cleanup,
                CronTrigger(hour=3, minute=0),
                id="ai_memory_cleanup",
                name="Limpeza automática de memórias da IA",
                replace_existing=True
            )
            
            self.scheduler.start()
            logger.info("🚀 Scheduler de limpeza de memórias da IA iniciado")
            logger.info("⏰ Próxima execução: Diariamente às 3:00 AM")
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar scheduler de limpeza: {e}")
    
    def stop(self):
        """
        Parar scheduler
        """
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("🛑 Scheduler de limpeza de memórias parado")

# Instância global
ai_memory_cleanup_scheduler = AIMemoryCleanupScheduler()
