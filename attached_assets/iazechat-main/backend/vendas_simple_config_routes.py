"""
Rotas Simples para WA Site (Vendas com IA)
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid
from datetime import datetime, timezone
import logging
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/vendas-bot", tags=["admin-wa-site"])

class IAInlineConfig(BaseModel):
    name: str = "Vendedor IA"
    personality: str = "Amigável, profissional e focado em vendas"
    instructions: str = ""
    instructions_url: Optional[str] = ""  # URL externa com instruções completas
    instructions_file: Optional[str] = ""  # Nome do arquivo de instruções (upload)
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 500
    api_key: str = ""  # API Key da OpenAI

class AgentProfile(BaseModel):
    name: str = "Assistente Virtual"
    photo: str = ""
    show_verified_badge: bool = True

class SimpleConfig(BaseModel):
    empresa_nome: str
    usa_ia: bool
    api_teste_url: str
    agent_id: Optional[str] = None
    custom_instructions: Optional[str] = None  # Instruções customizadas diretas (legado)
    ia_inline: Optional[IAInlineConfig] = None  # Nova config inline completa
    agent_profile: Optional[AgentProfile] = None  # Perfil do agente IA

def get_db():
    """Dependency para obter database"""
    from server import db
    return db

@router.get("/simple-config")
async def get_simple_config(db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Obter configuração simples do WA Site
    """
    try:
        config = await db.vendas_simple_config.find_one(
            {"is_active": True},
            {"_id": 0}
        )
        
        if not config:
            # Retornar config padrão
            return {
                "config_id": None,
                "empresa_nome": "CyberTV",
                "usa_ia": True,
                "api_teste_url": "https://gesth.io/api/get-teste?hash=TG1OTW5QWHlaTW5Q",
                "agent_id": None,
                "custom_instructions": None,
                "ia_inline": {
                    "name": "Vendedor IA",
                    "personality": "Amigável, profissional e focado em vendas",
                    "instructions": "",
                    "llm_provider": "openai",
                    "llm_model": "gpt-4o-mini",
                    "temperature": 0.7,
                    "max_tokens": 500,
                    "api_key": ""
                },
                "agent_profile": {
                    "name": "Assistente Virtual",
                    "photo": "",
                    "show_verified_badge": True
                },
                "is_active": True
            }
        
        return config
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar config simples: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simple-config")
async def save_simple_config(
    request: SimpleConfig,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Salvar configuração simples do WA Site
    """
    try:
        # Desativar todas as configs existentes
        await db.vendas_simple_config.update_many(
            {},
            {"$set": {"is_active": False}}
        )
        
        # Criar nova config
        config_id = str(uuid.uuid4())
        config_data = {
            "config_id": config_id,
            "empresa_nome": request.empresa_nome,
            "usa_ia": request.usa_ia,
            "api_teste_url": request.api_teste_url,
            "agent_id": request.agent_id,
            "custom_instructions": request.custom_instructions,
            "ia_inline": request.ia_inline.dict() if request.ia_inline else None,
            "agent_profile": request.agent_profile.dict() if request.agent_profile else None,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.vendas_simple_config.insert_one(config_data)
        
        logger.info(f"✅ Config simples salva: {config_id}")
        
        return {"success": True, "config_id": config_id}
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar config simples: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# ========== UPLOAD DE INSTRUÇÕES EM .TXT PARA WA SITE ==========

@router.post("/upload-instructions")
async def upload_wasite_instructions(
    file: UploadFile = File(...),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Upload de arquivo .txt com instruções para o WA Site
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
        
        # Nome do arquivo: wasite.txt
        filename = "wasite.txt"
        filepath = os.path.join(instructions_dir, filename)
        
        # Salvar arquivo
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        logger.info(f"✅ Instruções do WA Site salvas: {len(text_content)} chars")
        
        # Buscar config ativa
        config = await db.vendas_simple_config.find_one({"is_active": True})
        
        if config:
            # Atualizar ia_inline com nome do arquivo
            ia_inline = config.get("ia_inline", {})
            ia_inline["instructions_file"] = filename
            
            await db.vendas_simple_config.update_one(
                {"is_active": True},
                {"$set": {"ia_inline": ia_inline}}
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
        logger.error(f"❌ Erro ao fazer upload de instruções WA Site: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/instructions-file")
async def get_wasite_instructions_file(db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Obter informações sobre o arquivo de instruções do WA Site
    """
    try:
        config = await db.vendas_simple_config.find_one({"is_active": True})
        
        if not config:
            return {
                "has_file": False,
                "filename": None,
                "size": 0
            }
        
        ia_inline = config.get("ia_inline", {})
        filename = ia_inline.get("instructions_file")
        
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
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar arquivo de instruções WA Site: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/instructions-file")
async def delete_wasite_instructions_file(db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Remover arquivo de instruções do WA Site
    """
    try:
        config = await db.vendas_simple_config.find_one({"is_active": True})
        
        if config:
            ia_inline = config.get("ia_inline", {})
            filename = ia_inline.get("instructions_file")
            
            if filename:
                filepath = f"/app/instructions/{filename}"
                if os.path.exists(filepath):
                    os.remove(filepath)
                    logger.info(f"✅ Arquivo WA Site removido: {filepath}")
            
            # Remover referência do banco
            ia_inline["instructions_file"] = None
            await db.vendas_simple_config.update_one(
                {"is_active": True},
                {"$set": {"ia_inline": ia_inline}}
            )
        
        return {
            "success": True,
            "message": "Arquivo de instruções removido"
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao remover arquivo WA Site: {e}")
        raise HTTPException(status_code=500, detail=str(e))
