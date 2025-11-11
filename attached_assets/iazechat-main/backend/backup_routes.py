"""
Sistema de Backup e Restauração Completo
Salva todas as collections do MongoDB
Mantém limite de 5 backups
"""

from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import os
from bson import json_util
import json
import uuid

router = APIRouter()
logger = logging.getLogger(__name__)

# Conexão MongoDB
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://mongodb:27017')
DB_NAME = os.environ.get('DB_NAME', 'support_chat')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Collection para armazenar backups
backups_collection = db.system_backups
backup_config_collection = db.backup_config


class BackupResponse(BaseModel):
    backup_id: str
    created_at: str
    size_mb: float
    collections_count: int
    total_documents: int
    is_automatic: bool


class BackupConfigModel(BaseModel):
    auto_backup_enabled: bool


async def get_current_admin(token: str = None):
    """Verificação de admin - placeholder"""
    # TODO: Implementar verificação real de admin
    return {"user_id": "admin", "role": "admin"}


async def create_backup_data() -> Dict[str, Any]:
    """Cria um backup completo de todas as collections"""
    try:
        backup_data = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "collections": {}
        }
        
        # Listar todas as collections (exceto system_backups e backup_config)
        collection_names = await db.list_collection_names()
        excluded = ["system_backups", "backup_config"]
        collections_to_backup = [c for c in collection_names if c not in excluded]
        
        total_docs = 0
        
        # Backup de cada collection
        for collection_name in collections_to_backup:
            collection = db[collection_name]
            documents = await collection.find().to_list(length=None)
            
            # Converter ObjectId e outros tipos BSON para JSON
            json_docs = json.loads(json_util.dumps(documents))
            
            backup_data["collections"][collection_name] = json_docs
            total_docs += len(json_docs)
            
            logger.info(f"✅ Backup collection '{collection_name}': {len(json_docs)} documentos")
        
        backup_data["metadata"] = {
            "total_collections": len(collections_to_backup),
            "total_documents": total_docs
        }
        
        return backup_data
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar backup: {str(e)}")
        raise


async def cleanup_old_backups():
    """Mantém apenas os 5 backups mais recentes"""
    try:
        # Contar backups
        count = await backups_collection.count_documents({})
        
        if count > 5:
            # Buscar todos ordenados por data (mais antigo primeiro)
            old_backups = await backups_collection.find().sort("created_at", 1).to_list(length=count - 5)
            
            # Deletar os mais antigos
            for backup in old_backups:
                await backups_collection.delete_one({"_id": backup["_id"]})
                logger.info(f"🗑️ Backup antigo removido: {backup['backup_id']}")
                
    except Exception as e:
        logger.error(f"❌ Erro ao limpar backups antigos: {str(e)}")


@router.post("/backups/create", response_model=BackupResponse)
async def create_backup(is_automatic: bool = False):
    """Cria um novo backup completo do sistema"""
    import gzip
    try:
        logger.info("📦 Iniciando criação de backup completo...")
        
        # Criar backup
        backup_data = await create_backup_data()
        
        # Gerar ID único
        backup_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        
        # Calcular tamanho aproximado (em MB)
        backup_json = json_util.dumps(backup_data)
        size_mb = len(backup_json) / (1024 * 1024)
        
        # Criar diretório de backups se não existir
        backup_dir = "/var/www/iaze/backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        # Salvar backup comprimido em arquivo
        backup_file_path = f"{backup_dir}/backup_{backup_id}.json.gz"
        with gzip.open(backup_file_path, 'wt', encoding='utf-8') as f:
            f.write(backup_json)
        
        # Calcular tamanho do arquivo comprimido
        compressed_size = os.path.getsize(backup_file_path) / (1024 * 1024)
        
        # Salvar apenas metadados no banco
        backup_record = {
            "backup_id": backup_id,
            "created_at": backup_data["created_at"],
            "file_path": backup_file_path,
            "size_mb": round(compressed_size, 2),
            "original_size_mb": round(size_mb, 2),
            "collections_count": backup_data["metadata"]["total_collections"],
            "total_documents": backup_data["metadata"]["total_documents"],
            "is_automatic": is_automatic
        }
        
        await backups_collection.insert_one(backup_record)
        
        # Limpar backups antigos
        await cleanup_old_backups()
        
        logger.info(f"✅ Backup criado com sucesso: {backup_id} ({compressed_size:.2f} MB comprimido)")
        
        return BackupResponse(
            backup_id=backup_id,
            created_at=backup_data["created_at"],
            size_mb=round(compressed_size, 2),
            collections_count=backup_data["metadata"]["total_collections"],
            total_documents=backup_data["metadata"]["total_documents"],
            is_automatic=is_automatic
        )
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar backup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao criar backup: {str(e)}")


@router.get("/backups", response_model=List[BackupResponse])
async def list_backups():
    """Lista todos os backups disponíveis"""
    try:
        backups = await backups_collection.find({}, {
            "data": 0  # Não retornar os dados completos na listagem
        }).sort("created_at", -1).to_list(length=None)
        
        return [
            BackupResponse(
                backup_id=b["backup_id"],
                created_at=b["created_at"],
                size_mb=b["size_mb"],
                collections_count=b["collections_count"],
                total_documents=b["total_documents"],
                is_automatic=b.get("is_automatic", False)
            )
            for b in backups
        ]
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar backups: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar backups: {str(e)}")


@router.post("/backups/restore/{backup_id}")
async def restore_backup(backup_id: str):
    """Restaura um backup específico"""
    try:
        logger.info(f"🔄 Iniciando restauração do backup: {backup_id}")
        
        # Buscar backup
        backup = await backups_collection.find_one({"backup_id": backup_id})
        
        if not backup:
            raise HTTPException(status_code=404, detail="Backup não encontrado")
        
        backup_data = backup["data"]
        restored_collections = []
        
        # Restaurar cada collection
        for collection_name, documents in backup_data["collections"].items():
            try:
                collection = db[collection_name]
                
                # Limpar collection atual
                await collection.delete_many({})
                
                if documents:
                    # Converter de volta para BSON
                    bson_docs = json.loads(json_util.dumps(documents))
                    
                    # Inserir documentos
                    await collection.insert_many(bson_docs)
                
                restored_collections.append(collection_name)
                logger.info(f"✅ Collection '{collection_name}' restaurada: {len(documents)} documentos")
                
            except Exception as e:
                logger.error(f"❌ Erro ao restaurar collection '{collection_name}': {str(e)}")
                raise
        
        logger.info(f"✅ Backup restaurado com sucesso: {len(restored_collections)} collections")
        
        return {
            "message": "Backup restaurado com sucesso",
            "backup_id": backup_id,
            "restored_collections": restored_collections,
            "total_documents": backup_data["metadata"]["total_documents"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao restaurar backup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao restaurar backup: {str(e)}")


@router.delete("/admin/backup/delete/{backup_id}")
async def delete_backup(backup_id: str):
    """Deleta um backup específico"""
    try:
        result = await backups_collection.delete_one({"backup_id": backup_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Backup não encontrado")
        
        logger.info(f"🗑️ Backup deletado: {backup_id}")
        
        return {"message": "Backup deletado com sucesso", "backup_id": backup_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao deletar backup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao deletar backup: {str(e)}")


@router.get("/admin/backup/config")
async def get_backup_config():
    """Retorna configuração de backup automático"""
    try:
        config = await backup_config_collection.find_one({"_id": "auto_backup"})
        
        if not config:
            # Config padrão
            return {"auto_backup_enabled": False}
        
        return {"auto_backup_enabled": config.get("enabled", False)}
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar configuração: {str(e)}")


@router.post("/admin/backup/config")
async def update_backup_config(config: BackupConfigModel):
    """Atualiza configuração de backup automático"""
    try:
        await backup_config_collection.update_one(
            {"_id": "auto_backup"},
            {"$set": {"enabled": config.auto_backup_enabled}},
            upsert=True
        )
        
        logger.info(f"⚙️ Backup automático {'ativado' if config.auto_backup_enabled else 'desativado'}")
        
        return {"message": "Configuração atualizada", "auto_backup_enabled": config.auto_backup_enabled}
        
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar configuração: {str(e)}")


@router.get("/admin/backup/download/{backup_id}")
async def download_backup(backup_id: str):
    """Download de um backup específico"""
    from fastapi.responses import FileResponse
    import gzip
    
    try:
        # Buscar backup
        backup = await backups_collection.find_one({"backup_id": backup_id})
        
        if not backup:
            raise HTTPException(status_code=404, detail="Backup não encontrado")
        
        file_path = backup.get("file_path")
        
        # Se tem caminho de arquivo (backups novos)
        if file_path and os.path.exists(file_path):
            logger.info(f"📥 Download do backup (arquivo): {backup_id}")
            
            # Descomprimir para enviar
            temp_file = f"/tmp/backup_{backup_id}.json"
            with gzip.open(file_path, 'rt', encoding='utf-8') as f_in:
                with open(temp_file, 'w', encoding='utf-8') as f_out:
                    f_out.write(f_in.read())
            
            return FileResponse(
                path=temp_file,
                media_type="application/json",
                filename=f"backup_{backup_id}.json",
                headers={"Content-Disposition": f'attachment; filename="backup_{backup_id}.json"'}
            )
        
        # Backups antigos (salvos no banco)
        elif "data" in backup:
            from fastapi.responses import Response
            backup_json = json.dumps(backup, default=json_util.default, indent=2)
            
            logger.info(f"📥 Download do backup (banco): {backup_id}")
            
            return Response(
                content=backup_json,
                media_type="application/json",
                headers={
                    "Content-Disposition": f'attachment; filename="backup_{backup_id}.json"'
                }
            )
        else:
            raise HTTPException(status_code=404, detail="Arquivo de backup não encontrado")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao fazer download: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao fazer download: {str(e)}")


@router.post("/admin/backup/upload")
async def upload_backup(file: UploadFile = File(...)):
    """Upload de um backup para restauração futura"""
    from fastapi import File, UploadFile
    import uuid
    
    try:
        # Receber arquivo
        contents = await file.read()
        
        # Validar JSON
        try:
            backup_data = json.loads(contents)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Arquivo não é um JSON válido")
        
        # Verificar se tem estrutura de backup
        if "backup_id" not in backup_data or "data" not in backup_data:
            raise HTTPException(status_code=400, detail="Arquivo não é um backup válido")
        
        # Gerar novo backup_id para evitar conflitos
        new_backup_id = str(uuid.uuid4())
        backup_data["backup_id"] = new_backup_id
        backup_data["created_at"] = datetime.now(timezone.utc).isoformat()
        backup_data["is_automatic"] = False
        backup_data["is_uploaded"] = True  # Marcar como upload
        
        # Salvar no banco
        await backups_collection.insert_one(backup_data)
        
        # Limitar a 10 backups
        total_backups = await backups_collection.count_documents({})
        if total_backups > 10:
            oldest = await backups_collection.find_one(
                {},
                sort=[("created_at", 1)]
            )
            if oldest:
                await backups_collection.delete_one({"_id": oldest["_id"]})
                logger.info(f"🗑️ Backup mais antigo deletado automaticamente")
        
        logger.info(f"📤 Backup enviado com sucesso: {new_backup_id}")
        
        return {
            "message": "Backup enviado com sucesso",
            "backup_id": new_backup_id,
            "size_mb": len(contents) / (1024 * 1024)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao fazer upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao fazer upload: {str(e)}")

