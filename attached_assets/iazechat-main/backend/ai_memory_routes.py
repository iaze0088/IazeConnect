"""
Rotas para gerenciamento de memória da IA
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Optional
from pydantic import BaseModel
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from ai_memory_cleanup_service import ai_memory_cleanup_service

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter()

# Database connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'support_chat')]

class AIMemoryCleanupConfig(BaseModel):
    ai_memory_cleanup_days: Optional[int] = None  # None ou 0 = nunca limpar, valores: 7, 15, 30, 60, 90

@router.get("/api/departments/{department_id}/ai-memory-config")
async def get_ai_memory_config(department_id: str):
    """
    Obter configuração de limpeza de memória da IA para um departamento
    """
    try:
        department = await db.departments.find_one({"id": department_id})
        
        if not department:
            raise HTTPException(status_code=404, detail="Departamento não encontrado")
        
        ai_config = department.get("ai_config", {})
        cleanup_days = ai_config.get("ai_memory_cleanup_days", None)
        
        return {
            "department_id": department_id,
            "department_name": department.get("name"),
            "ai_memory_cleanup_days": cleanup_days
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao buscar configuração de memória: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/departments/{department_id}/ai-memory-config")
async def update_ai_memory_config(department_id: str, config: AIMemoryCleanupConfig):
    """
    Atualizar configuração de limpeza de memória da IA para um departamento
    """
    try:
        department = await db.departments.find_one({"id": department_id})
        
        if not department:
            raise HTTPException(status_code=404, detail="Departamento não encontrado")
        
        # Atualizar ai_config com novo valor
        ai_config = department.get("ai_config", {})
        ai_config["ai_memory_cleanup_days"] = config.ai_memory_cleanup_days
        
        result = await db.departments.update_one(
            {"id": department_id},
            {"$set": {"ai_config": ai_config}}
        )
        
        if result.modified_count > 0:
            logger.info(f"✅ Configuração de memória atualizada para departamento: {department_id}")
            return {
                "success": True,
                "message": "Configuração atualizada com sucesso",
                "ai_memory_cleanup_days": config.ai_memory_cleanup_days
            }
        else:
            return {
                "success": False,
                "message": "Nenhuma alteração realizada"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar configuração de memória: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/ai-memory/stats")
async def get_memory_stats():
    """
    Obter estatísticas de uso de memória da IA
    """
    try:
        stats = await ai_memory_cleanup_service.get_memory_stats()
        
        if stats is None:
            raise HTTPException(status_code=500, detail="Erro ao obter estatísticas")
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas de memória: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/ai-memory/cleanup-now")
async def trigger_cleanup_now():
    """
    Forçar limpeza imediata de memórias antigas (admin)
    """
    try:
        await ai_memory_cleanup_service.cleanup_old_conversations()
        
        return {
            "success": True,
            "message": "Limpeza executada com sucesso"
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao executar limpeza manual: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/ai-memory/session/{session_id}")
async def delete_session_memory(session_id: str):
    """
    Limpar memória de uma sessão específica
    """
    try:
        success = await ai_memory_cleanup_service.cleanup_by_session_id(session_id)
        
        if success:
            return {
                "success": True,
                "message": "Memória da sessão removida com sucesso"
            }
        else:
            return {
                "success": False,
                "message": "Sessão não encontrada"
            }
        
    except Exception as e:
        logger.error(f"❌ Erro ao remover memória da sessão: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# ========== UPLOAD DE INSTRUÇÕES EM .TXT ==========

@router.post("/api/departments/{department_id}/upload-instructions")
async def upload_department_instructions(
    department_id: str,
    file: UploadFile = File(...)
):
    """
    Upload de arquivo .txt com instruções para um departamento
    """
    try:
        # Validar extensão do arquivo
        if not file.filename.endswith('.txt'):
            raise HTTPException(status_code=400, detail="Apenas arquivos .txt são permitidos")
        
        # Ler conteúdo do arquivo
        content = await file.read()
        text_content = content.decode('utf-8')
        
        # Validar tamanho mínimo
        if len(text_content.strip()) < 10:
            raise HTTPException(status_code=400, detail="Arquivo muito pequeno (mínimo 10 caracteres)")
        
        # Criar diretório se não existir
        instructions_dir = "/app/instructions"
        os.makedirs(instructions_dir, exist_ok=True)
        
        # Nome do arquivo: department_{id}.txt
        filename = f"department_{department_id}.txt"
        filepath = os.path.join(instructions_dir, filename)
        
        # Salvar arquivo
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        logger.info(f"✅ Instruções salvas para departamento {department_id}: {len(text_content)} chars")
        
        # Atualizar departamento com nome do arquivo
        department = await db.departments.find_one({"id": department_id})
        if not department:
            raise HTTPException(status_code=404, detail="Departamento não encontrado")
        
        ai_config = department.get("ai_config", {})
        ai_config["instructions_file"] = filename
        
        await db.departments.update_one(
            {"id": department_id},
            {"$set": {"ai_config": ai_config}}
        )
        
        return {
            "success": True,
            "message": "Instruções carregadas com sucesso!",
            "filename": filename,
            "size": len(text_content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao fazer upload de instruções: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/departments/{department_id}/instructions-file")
async def get_department_instructions_file(department_id: str):
    """
    Obter informações sobre o arquivo de instruções de um departamento
    """
    try:
        department = await db.departments.find_one({"id": department_id})
        if not department:
            raise HTTPException(status_code=404, detail="Departamento não encontrado")
        
        ai_config = department.get("ai_config", {})
        filename = ai_config.get("instructions_file")
        
        if not filename:
            return {
                "has_file": False,
                "filename": None,
                "size": 0
            }
        
        filepath = f"/app/instructions/{filename}"
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "has_file": True,
                "filename": filename,
                "size": len(content),
                "preview": content[:200] + "..." if len(content) > 200 else content
            }
        else:
            return {
                "has_file": False,
                "filename": filename,
                "size": 0,
                "error": "Arquivo não encontrado no servidor"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao buscar arquivo de instruções: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/departments/{department_id}/instructions-file")
async def delete_department_instructions_file(department_id: str):
    """
    Remover arquivo de instruções de um departamento
    """
    try:
        department = await db.departments.find_one({"id": department_id})
        if not department:
            raise HTTPException(status_code=404, detail="Departamento não encontrado")
        
        ai_config = department.get("ai_config", {})
        filename = ai_config.get("instructions_file")
        
        if filename:
            filepath = f"/app/instructions/{filename}"
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"✅ Arquivo removido: {filepath}")
        
        # Remover referência do banco
        ai_config["instructions_file"] = None
        await db.departments.update_one(
            {"id": department_id},
            {"$set": {"ai_config": ai_config}}
        )
        
        return {
            "success": True,
            "message": "Arquivo de instruções removido"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao remover arquivo: {e}")
        raise HTTPException(status_code=500, detail=str(e))
