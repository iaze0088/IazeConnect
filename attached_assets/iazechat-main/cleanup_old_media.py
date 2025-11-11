"""
Sistema de Limpeza Automática de Mídias Antigas
Remove arquivos de áudio/foto/vídeo após 7 dias para economizar espaço
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
from pathlib import Path
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
# Usar diretório persistente
try:
    UPLOADS_DIR = Path('/data/uploads')
    if not UPLOADS_DIR.exists():
        # Fallback para diretório local
        UPLOADS_DIR = Path('/app/backend/uploads')
        logger.warning(f"⚠️  Usando fallback: {UPLOADS_DIR}")
except Exception as e:
    UPLOADS_DIR = Path('/app/backend/uploads')
    logger.warning(f"⚠️  Erro ao acessar /data/uploads: {e}")

DAYS_TO_KEEP = 7  # Arquivos são mantidos por 7 dias
logger.info(f"📁 Diretório de uploads: {UPLOADS_DIR}")

async def cleanup_old_media():
    """Limpar mídias antigas (áudio, foto, vídeo) após 7 dias"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.support_chat
    
    logger.info("🧹 Iniciando limpeza de mídias antigas...")
    
    # Data limite: 7 dias atrás
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=DAYS_TO_KEEP)
    logger.info(f"📅 Data limite: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Buscar mensagens com mídia antiga
    query = {
        "kind": {"$in": ["audio", "image", "video"]},
        "file_url": {"$exists": True, "$ne": ""},
        "created_at": {"$lt": cutoff_date.isoformat()}
    }
    
    old_messages = await db.messages.find(query).to_list(None)
    logger.info(f"📊 Encontradas {len(old_messages)} mensagens com mídia antiga")
    
    deleted_files_count = 0
    deleted_size = 0
    updated_messages = 0
    errors = 0
    
    for msg in old_messages:
        try:
            file_url = msg.get("file_url", "")
            if not file_url:
                continue
            
            # Extrair nome do arquivo da URL
            # Ex: http://backend/api/uploads/abc123.mp3 -> abc123.mp3
            filename = file_url.split("/")[-1]
            filepath = UPLOADS_DIR / filename
            
            # Verificar se arquivo existe
            if filepath.exists():
                # Obter tamanho antes de deletar
                file_size = filepath.stat().st_size
                
                # Deletar arquivo
                filepath.unlink()
                
                deleted_files_count += 1
                deleted_size += file_size
                
                logger.info(f"🗑️  Deletado: {filename} ({file_size / 1024:.2f} KB)")
            
            # Atualizar mensagem no banco: marcar como "mídia expirada"
            await db.messages.update_one(
                {"id": msg["id"]},
                {
                    "$set": {
                        "media_expired": True,
                        "media_deleted_at": datetime.now(timezone.utc).isoformat(),
                        "original_file_url": file_url  # Backup da URL original
                    },
                    "$unset": {"file_url": ""}  # Remove URL (arquivo não existe mais)
                }
            )
            updated_messages += 1
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar {msg.get('id')}: {str(e)}")
            errors += 1
    
    # Resumo
    logger.info("\n" + "="*60)
    logger.info("📊 RESUMO DA LIMPEZA")
    logger.info("="*60)
    logger.info(f"🗑️  Arquivos deletados: {deleted_files_count}")
    logger.info(f"💾 Espaço liberado: {deleted_size / (1024*1024):.2f} MB")
    logger.info(f"📝 Mensagens atualizadas: {updated_messages}")
    logger.info(f"❌ Erros: {errors}")
    logger.info("="*60 + "\n")
    
    client.close()
    
    return {
        "deleted_files": deleted_files_count,
        "freed_space_mb": deleted_size / (1024*1024),
        "updated_messages": updated_messages,
        "errors": errors
    }

async def cleanup_orphaned_files():
    """Limpar arquivos órfãos (sem referência no banco)"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.support_chat
    
    logger.info("🔍 Procurando arquivos órfãos...")
    
    if not UPLOADS_DIR.exists():
        logger.warning(f"⚠️  Diretório de uploads não existe: {UPLOADS_DIR}")
        client.close()
        return
    
    # Buscar todos os arquivos no disco
    all_files = list(UPLOADS_DIR.glob("*"))
    logger.info(f"📁 Encontrados {len(all_files)} arquivos no disco")
    
    # Buscar todas as URLs de mídia no banco
    messages_with_media = await db.messages.find(
        {"file_url": {"$exists": True, "$ne": ""}},
        {"file_url": 1}
    ).to_list(None)
    
    # Extrair nomes de arquivos das URLs
    referenced_files = set()
    for msg in messages_with_media:
        file_url = msg.get("file_url", "")
        if file_url:
            filename = file_url.split("/")[-1]
            referenced_files.add(filename)
    
    logger.info(f"🔗 {len(referenced_files)} arquivos referenciados no banco")
    
    # Encontrar órfãos
    orphaned_count = 0
    orphaned_size = 0
    
    for filepath in all_files:
        if filepath.is_file() and filepath.name not in referenced_files:
            file_size = filepath.stat().st_size
            
            # Deletar órfão
            filepath.unlink()
            
            orphaned_count += 1
            orphaned_size += file_size
            
            logger.info(f"🗑️  Órfão deletado: {filepath.name} ({file_size / 1024:.2f} KB)")
    
    logger.info(f"\n✅ Órfãos deletados: {orphaned_count} ({orphaned_size / (1024*1024):.2f} MB)\n")
    
    client.close()
    
    return {
        "orphaned_files": orphaned_count,
        "freed_space_mb": orphaned_size / (1024*1024)
    }

async def main():
    """Executar limpeza completa"""
    logger.info("\n🚀 INICIANDO LIMPEZA AUTOMÁTICA DE MÍDIAS\n")
    
    # 1. Limpar mídias antigas (7+ dias)
    result1 = await cleanup_old_media()
    
    # 2. Limpar arquivos órfãos
    result2 = await cleanup_orphaned_files()
    
    # Resumo final
    total_freed = result1["freed_space_mb"] + result2["freed_space_mb"]
    
    logger.info("\n" + "="*60)
    logger.info("🎉 LIMPEZA COMPLETA FINALIZADA")
    logger.info("="*60)
    logger.info(f"💾 Espaço total liberado: {total_freed:.2f} MB")
    logger.info(f"🗑️  Total de arquivos deletados: {result1['deleted_files'] + result2['orphaned_files']}")
    logger.info("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
