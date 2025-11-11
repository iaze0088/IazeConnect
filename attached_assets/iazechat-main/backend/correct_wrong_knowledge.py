"""
Sistema de Base de Conhecimento CERTO | ERRADO
Permite configurar respostas corretas e erradas para perguntas específicas
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import logging
import re

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/vendas-bot/knowledge/correct-wrong", tags=["correct-wrong-knowledge"])

# ==================== MODELOS ====================

class CorrectWrongEntry(BaseModel):
    """Entrada da base de conhecimento CERTO | ERRADO"""
    id: Optional[str] = None
    question: str  # Pergunta (ex: "qual o app para smart tv?")
    correct_options: List[str] = []  # Opções CERTAS
    wrong_options: List[str] = []  # Opções ERRADAS
    correct_template: str = "✅ Use: {options}"  # Template para resposta CERTA
    wrong_template: str = "❌ Evite: {options}"  # Template para resposta ERRADA
    reseller_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class CorrectWrongConfig(BaseModel):
    """Configuração global de templates"""
    default_correct_template: str = "✅ **Opções Corretas:**\n{options}"
    default_wrong_template: str = "⚠️ **Alternativas (usar apenas se as corretas não funcionarem):**\n{options}"
    use_numbered_menu: bool = True
    reseller_id: Optional[str] = None

# ==================== DEPENDÊNCIAS ====================

def get_db():
    """Dependency para obter database"""
    from server import db
    return db

# ==================== ROTAS ====================

@router.get("/config")
async def get_config(db: AsyncIOMotorDatabase = Depends(get_db)):
    """Buscar configuração de templates"""
    try:
        # TODO: Adicionar suporte a reseller_id quando implementar multi-tenant
        config = await db.correct_wrong_config.find_one({}, {"_id": 0})
        
        if not config:
            # Retornar config padrão
            default_config = CorrectWrongConfig()
            return default_config.dict()
        
        return config
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/config")
async def update_config(
    config: CorrectWrongConfig,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Atualizar configuração de templates"""
    try:
        config_dict = config.dict()
        config_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await db.correct_wrong_config.update_one(
            {},
            {"$set": config_dict},
            upsert=True
        )
        
        logger.info("✅ Config de CERTO|ERRADO atualizada")
        return {"ok": True}
        
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("")
async def list_entries(db: AsyncIOMotorDatabase = Depends(get_db)):
    """Listar todas as entradas"""
    try:
        # TODO: Filtrar por reseller_id quando implementar multi-tenant
        entries = await db.correct_wrong_knowledge.find({}, {"_id": 0}).to_list(length=None)
        
        logger.info(f"📋 {len(entries)} entradas CERTO|ERRADO encontradas")
        return entries
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar entradas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("")
async def create_entry(
    entry: CorrectWrongEntry,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Criar nova entrada"""
    try:
        entry_dict = entry.dict()
        entry_dict["id"] = str(uuid.uuid4())
        entry_dict["created_at"] = datetime.now(timezone.utc).isoformat()
        entry_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await db.correct_wrong_knowledge.insert_one(entry_dict)
        
        logger.info(f"✅ Nova entrada criada: {entry.question}")
        return {"ok": True, "id": entry_dict["id"]}
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar entrada: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{entry_id}")
async def update_entry(
    entry_id: str,
    entry: CorrectWrongEntry,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Atualizar entrada existente"""
    try:
        entry_dict = entry.dict()
        entry_dict["id"] = entry_id
        entry_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Remover created_at para não sobrescrever
        entry_dict.pop("created_at", None)
        
        result = await db.correct_wrong_knowledge.update_one(
            {"id": entry_id},
            {"$set": entry_dict}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Entrada não encontrada")
        
        logger.info(f"✅ Entrada atualizada: {entry_id}")
        return {"ok": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar entrada: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{entry_id}")
async def delete_entry(
    entry_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Deletar entrada"""
    try:
        result = await db.correct_wrong_knowledge.delete_one({"id": entry_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Entrada não encontrada")
        
        logger.info(f"✅ Entrada deletada: {entry_id}")
        return {"ok": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao deletar entrada: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_txt_file(
    file: UploadFile = File(...),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Upload de arquivo TXT com formato:
    
    PERGUNTA: qual o app para smart tv?
    CERTO:
    ASSIST PLUS
    XCLOUD
    HD PLAYER
    ERRADO:
    CYBERXC
    SITE PC
    ---
    """
    try:
        # Ler conteúdo do arquivo
        content = await file.read()
        text = content.decode('utf-8')
        
        # Separar por blocos (cada bloco é separado por ---)
        blocks = text.split('---')
        
        entries_created = 0
        
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            
            # Parse do bloco
            lines = [line.strip() for line in block.split('\n') if line.strip()]
            
            if not lines:
                continue
            
            # Primeira linha deve ser a pergunta
            question_line = lines[0]
            if not question_line.upper().startswith('PERGUNTA:'):
                logger.warning(f"⚠️ Bloco ignorado (não começa com PERGUNTA:): {question_line[:50]}")
                continue
            
            question = question_line.replace('PERGUNTA:', '').strip()
            
            # Parse CERTO e ERRADO
            correct_options = []
            wrong_options = []
            current_section = None
            
            for line in lines[1:]:
                line_upper = line.upper()
                
                if line_upper == 'CERTO:':
                    current_section = 'correct'
                    continue
                elif line_upper == 'ERRADO:':
                    current_section = 'wrong'
                    continue
                
                # Adicionar opção à seção atual
                if current_section == 'correct' and line:
                    correct_options.append(line)
                elif current_section == 'wrong' and line:
                    wrong_options.append(line)
            
            # Criar entrada
            if question and (correct_options or wrong_options):
                entry_dict = {
                    "id": str(uuid.uuid4()),
                    "question": question,
                    "correct_options": correct_options,
                    "wrong_options": wrong_options,
                    "correct_template": "✅ **Opções Corretas:**\n{options}",
                    "wrong_template": "⚠️ **Alternativas (usar apenas se as corretas não funcionarem):**\n{options}",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                
                await db.correct_wrong_knowledge.insert_one(entry_dict)
                entries_created += 1
                logger.info(f"✅ Entrada criada do upload: {question}")
        
        logger.info(f"✅ Upload concluído: {entries_created} entradas criadas")
        return {
            "ok": True,
            "entries_created": entries_created,
            "message": f"{entries_created} entradas criadas com sucesso!"
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== SERVIÇO DE BUSCA ====================

class CorrectWrongService:
    """Serviço para buscar e formatar respostas CERTO|ERRADO"""
    
    @staticmethod
    async def search_knowledge(user_message: str, db) -> Optional[dict]:
        """
        Busca na base de conhecimento por match da pergunta
        Retorna dict com correct_options, wrong_options e templates
        """
        try:
            # Buscar todas as entradas
            entries = await db.correct_wrong_knowledge.find({}, {"_id": 0}).to_list(length=None)
            
            user_msg_lower = user_message.lower()
            
            # Buscar match por palavras-chave
            for entry in entries:
                question_lower = entry.get('question', '').lower()
                
                # Extrair palavras-chave da pergunta (>3 chars)
                keywords = [word for word in question_lower.split() if len(word) > 3]
                
                # Se 50%+ das keywords estão na mensagem do usuário, é um match
                matches = sum(1 for keyword in keywords if keyword in user_msg_lower)
                
                if keywords and matches / len(keywords) >= 0.5:
                    logger.info(f"✅ Match encontrado: {entry.get('question')}")
                    return entry
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar conhecimento: {e}")
            return None
    
    @staticmethod
    def format_response(entry: dict, include_wrong: bool = False) -> str:
        """
        Formata resposta usando templates CERTO (e ERRADO se solicitado)
        """
        try:
            correct_options = entry.get('correct_options', [])
            wrong_options = entry.get('wrong_options', [])
            correct_template = entry.get('correct_template', '✅ Use: {options}')
            wrong_template = entry.get('wrong_template', '❌ Evite: {options}')
            
            response_parts = []
            
            # Formatar opções CERTAS
            if correct_options:
                # Criar menu numerado
                options_text = "\n".join([f"{i+1}️⃣ {opt}" for i, opt in enumerate(correct_options)])
                formatted_correct = correct_template.replace('{options}', options_text)
                response_parts.append(formatted_correct)
            
            # Formatar opções ERRADAS (apenas se solicitado)
            if include_wrong and wrong_options:
                options_text = "\n".join([f"• {opt}" for opt in wrong_options])
                formatted_wrong = wrong_template.replace('{options}', options_text)
                response_parts.append(formatted_wrong)
            
            return "\n\n".join(response_parts)
            
        except Exception as e:
            logger.error(f"❌ Erro ao formatar resposta: {e}")
            return ""

# Instância global
correct_wrong_service = CorrectWrongService()
