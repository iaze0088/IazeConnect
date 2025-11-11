"""
Serviço de Limpeza Automática de Memória da IA
Limpa conversas antigas baseado na configuração de cada departamento
"""
import logging
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class AIMemoryCleanupService:
    """
    Serviço para limpar memórias antigas da IA baseado em configuração de departamento
    """
    
    def __init__(self, mongo_url: str = None):
        if mongo_url is None:
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        
        self.client = AsyncIOMotorClient(mongo_url)
        self.db = self.client.support_chat
    
    async def cleanup_old_conversations(self):
        """
        Limpar conversas antigas baseado na configuração de cada departamento
        """
        try:
            logger.info("🧹 Iniciando limpeza de memórias antigas da IA...")
            
            # Buscar todos os departamentos com IA ativada
            departments = await self.db.departments.find({"ai_enabled": True}).to_list(length=None)
            
            if not departments:
                logger.info("📭 Nenhum departamento com IA ativada encontrado")
                return
            
            total_cleaned = 0
            
            for dept in departments:
                dept_id = dept.get("id")
                dept_name = dept.get("name", "Unknown")
                ai_config = dept.get("ai_config", {})
                
                # Pegar configuração de limpeza (em dias)
                cleanup_days = ai_config.get("ai_memory_cleanup_days", None)
                
                if cleanup_days is None or cleanup_days == 0:
                    logger.debug(f"⏭️ Departamento '{dept_name}' configurado para nunca limpar memória")
                    continue
                
                # Calcular data de corte
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=cleanup_days)
                
                # Limpar conversas antigas deste departamento
                result = await self.db.ai_conversation_memory.delete_many({
                    "department_id": dept_id,
                    "created_at": {"$lt": cutoff_date.isoformat()}
                })
                
                deleted_count = result.deleted_count
                total_cleaned += deleted_count
                
                if deleted_count > 0:
                    logger.info(f"✅ Departamento '{dept_name}': {deleted_count} conversas limpas (> {cleanup_days} dias)")
            
            logger.info(f"🎉 Limpeza concluída! Total: {total_cleaned} conversas removidas")
            
        except Exception as e:
            logger.error(f"❌ Erro na limpeza de memórias: {e}")
    
    async def cleanup_by_session_id(self, session_id: str):
        """
        Limpar conversas de uma sessão específica
        """
        try:
            result = await self.db.ai_conversation_memory.delete_one({"session_id": session_id})
            
            if result.deleted_count > 0:
                logger.info(f"✅ Conversa {session_id} removida")
                return True
            else:
                logger.warning(f"⚠️ Conversa {session_id} não encontrada")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao limpar conversa {session_id}: {e}")
            return False
    
    async def get_memory_stats(self):
        """
        Obter estatísticas de uso de memória
        """
        try:
            # Total de conversas
            total_conversations = await self.db.ai_conversation_memory.count_documents({})
            
            # Total de mensagens
            pipeline = [
                {"$project": {"messages_count": {"$size": "$messages"}}},
                {"$group": {"_id": None, "total": {"$sum": "$messages_count"}}}
            ]
            result = await self.db.ai_conversation_memory.aggregate(pipeline).to_list(length=1)
            total_messages = result[0]["total"] if result else 0
            
            # Conversas por departamento
            pipeline_dept = [
                {"$group": {"_id": "$department_id", "count": {"$sum": 1}}}
            ]
            dept_stats = await self.db.ai_conversation_memory.aggregate(pipeline_dept).to_list(length=None)
            
            return {
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "by_department": dept_stats
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas: {e}")
            return None

# Instância global
ai_memory_cleanup_service = AIMemoryCleanupService()
