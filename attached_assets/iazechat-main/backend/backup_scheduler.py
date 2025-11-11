"""
Scheduler para Backup Automático de Hora em Hora
"""

import asyncio
import logging
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os
import httpx

logger = logging.getLogger(__name__)

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://mongodb:27017')
DB_NAME = os.environ.get('DB_NAME', 'support_chat')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]
backup_config_collection = db.backup_config
scheduled_messages_collection = db.scheduled_messages

# URL do backend
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')


async def check_and_run_backup():
    """Verifica se backup automático está ativado e executa"""
    try:
        # Verificar configuração
        config = await backup_config_collection.find_one({"_id": "auto_backup"})
        
        if config and config.get("enabled", False):
            logger.info("⏰ Executando backup automático...")
            
            # Chamar API de backup
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{BACKEND_URL}/api/backups/create?is_automatic=true"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Backup automático criado: {data['backup_id']} ({data['size_mb']} MB)")
                else:
                    logger.error(f"❌ Erro ao criar backup automático: {response.status_code}")
                    
    except Exception as e:
        logger.error(f"❌ Erro no backup automático: {str(e)}")


async def process_scheduled_messages():
    """Processa e envia mensagens agendadas"""
    try:
        # Chamar API para processar mensagens
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{BACKEND_URL}/api/send-scheduled-messages")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("sent", 0) > 0:
                    logger.info(f"✅ {data['sent']} mensagens agendadas enviadas")
            
    except Exception as e:
        logger.error(f"❌ Erro ao processar mensagens agendadas: {str(e)}")


async def process_reminders():
    """Processa e envia lembretes de vencimento"""
    try:
        # Chamar API para processar lembretes
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(f"{BACKEND_URL}/api/process-reminders")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("sent", 0) > 0:
                    logger.info(f"✅ {data['sent']} lembretes de vencimento enviados")
            
    except Exception as e:
        logger.error(f"❌ Erro ao processar lembretes: {str(e)}")


async def backup_scheduler():
    """Loop principal do scheduler - executa a cada hora"""
    logger.info("🚀 Scheduler de backup automático iniciado")
    
    while True:
        try:
            await check_and_run_backup()
            
            # Aguardar 1 hora (3600 segundos)
            await asyncio.sleep(3600)
            
        except Exception as e:
            logger.error(f"❌ Erro no scheduler: {str(e)}")
            await asyncio.sleep(60)  # Aguardar 1 minuto em caso de erro


async def scheduled_messages_scheduler():
    """Loop para processar mensagens agendadas - executa a cada minuto"""
    logger.info("🚀 Scheduler de mensagens agendadas iniciado")
    
    while True:
        try:
            await process_scheduled_messages()
            
            # Aguardar 1 minuto (60 segundos)
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"❌ Erro no scheduler de mensagens: {str(e)}")
            await asyncio.sleep(60)


async def reminders_scheduler():
    """Loop para processar lembretes - executa uma vez por dia no horário configurado"""
    logger.info("🚀 Scheduler de lembretes de vencimento iniciado")
    
    while True:
        try:
            # Verificar horário atual
            now = datetime.now(timezone.utc)
            
            # Executar às 9h UTC (ajustar conforme necessário)
            if now.hour == 9 and now.minute < 5:  # Janela de 5 minutos
                logger.info("⏰ Hora de processar lembretes de vencimento")
                await process_reminders()
                
                # Aguardar 1 hora para não executar várias vezes
                await asyncio.sleep(3600)
            else:
                # Aguardar 5 minutos e verificar novamente
                await asyncio.sleep(300)
            
        except Exception as e:
            logger.error(f"❌ Erro no scheduler de lembretes: {str(e)}")
            await asyncio.sleep(300)


def start_backup_scheduler():
    """Inicia o scheduler em background"""
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(backup_scheduler())
        loop.create_task(scheduled_messages_scheduler())
        loop.create_task(reminders_scheduler())
        logger.info("✅ Scheduler de backup iniciado com sucesso")
        logger.info("✅ Scheduler de mensagens agendadas iniciado com sucesso")
        logger.info("✅ Scheduler de lembretes de vencimento iniciado com sucesso")
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar scheduler: {str(e)}")
