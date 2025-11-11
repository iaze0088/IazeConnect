"""
Sistema de Aprendizado da IA
Rotas para feedback, memória e padrões de conhecimento
"""
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid
from datetime import datetime, timezone, timedelta
import logging
from typing import List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai-learning", tags=["ai-learning"])

def get_db():
    """Dependency para obter database"""
    from server import db
    return db

# ==========================================
# MODELS DE REQUEST
# ==========================================

class FeedbackRequest(BaseModel):
    session_id: str
    tipo: str  # "acerto" | "erro"
    categoria: str
    contexto: dict
    resultado: str
    marcado_por: str
    agent_id: Optional[str] = None

class UpdateFeedbackRequest(BaseModel):
    aprovado_admin: bool

# ==========================================
# ROTAS DE MEMÓRIA DE CONVERSA
# ==========================================

@router.get("/conversations/{session_id}")
async def get_conversation_memory(
    session_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Obter memória de conversa específica
    """
    try:
        memory = await db.ai_conversation_memory.find_one(
            {"session_id": session_id},
            {"_id": 0}
        )
        
        if not memory:
            return {"session_id": session_id, "messages": [], "metadata": {}}
        
        return memory
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar memória: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversations/{session_id}/message")
async def save_conversation_message(
    session_id: str,
    message: dict,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Salvar mensagem na memória de conversa
    """
    try:
        # Verificar se já existe memória
        memory = await db.ai_conversation_memory.find_one({"session_id": session_id})
        
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=60)
        
        if memory:
            # Atualizar memória existente
            await db.ai_conversation_memory.update_one(
                {"session_id": session_id},
                {
                    "$push": {"messages": message},
                    "$set": {"expires_at": expires_at.isoformat()}
                }
            )
        else:
            # Criar nova memória
            new_memory = {
                "session_id": session_id,
                "messages": [message],
                "metadata": {},
                "created_at": now.isoformat(),
                "expires_at": expires_at.isoformat()
            }
            await db.ai_conversation_memory.insert_one(new_memory)
        
        logger.info(f"✅ Mensagem salva na memória: {session_id}")
        return {"success": True}
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar mensagem na memória: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/conversations/{session_id}/metadata")
async def update_conversation_metadata(
    session_id: str,
    metadata: dict,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Atualizar metadata da conversa
    """
    try:
        await db.ai_conversation_memory.update_one(
            {"session_id": session_id},
            {"$set": {"metadata": metadata}}
        )
        
        logger.info(f"✅ Metadata atualizada: {session_id}")
        return {"success": True}
        
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# ROTAS DE FEEDBACK (ACERTOS/ERROS)
# ==========================================

@router.post("/feedback")
async def create_feedback(
    request: FeedbackRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Criar novo feedback de aprendizado
    """
    try:
        feedback_id = str(uuid.uuid4())
        
        feedback_data = {
            "id": feedback_id,
            "session_id": request.session_id,
            "tipo": request.tipo,
            "categoria": request.categoria,
            "contexto": request.contexto,
            "resultado": request.resultado,
            "marcado_por": request.marcado_por,
            "aprovado_admin": False,
            "agent_id": request.agent_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.ai_learning_feedback.insert_one(feedback_data)
        
        logger.info(f"✅ Feedback criado: {feedback_id} - Tipo: {request.tipo}")
        
        return {"success": True, "feedback_id": feedback_id}
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/feedback")
async def list_feedback(
    agent_id: Optional[str] = None,
    tipo: Optional[str] = None,
    aprovado: Optional[bool] = None,
    limit: int = 100,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Listar feedbacks com filtros
    """
    try:
        query = {}
        
        if agent_id:
            query["agent_id"] = agent_id
        
        if tipo:
            query["tipo"] = tipo
        
        if aprovado is not None:
            query["aprovado_admin"] = aprovado
        
        feedbacks = await db.ai_learning_feedback.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(length=None)
        
        return {"feedbacks": feedbacks, "total": len(feedbacks)}
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar feedbacks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/feedback/{feedback_id}")
async def update_feedback(
    feedback_id: str,
    request: UpdateFeedbackRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Atualizar feedback (aprovar/reprovar pelo admin)
    """
    try:
        result = await db.ai_learning_feedback.update_one(
            {"id": feedback_id},
            {"$set": {"aprovado_admin": request.aprovado_admin}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Feedback não encontrado")
        
        logger.info(f"✅ Feedback atualizado: {feedback_id}")
        
        return {"success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/feedback/{feedback_id}")
async def delete_feedback(
    feedback_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Deletar feedback específico
    """
    try:
        result = await db.ai_learning_feedback.delete_one({"id": feedback_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Feedback não encontrado")
        
        logger.info(f"✅ Feedback deletado: {feedback_id}")
        
        return {"success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao deletar feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/feedback/agent/{agent_id}/all")
async def delete_all_agent_feedback(
    agent_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Limpar TODOS os feedbacks de um agente específico
    """
    try:
        result = await db.ai_learning_feedback.delete_many({"agent_id": agent_id})
        
        logger.info(f"✅ {result.deleted_count} feedbacks deletados do agente: {agent_id}")
        
        return {"success": True, "deleted_count": result.deleted_count}
        
    except Exception as e:
        logger.error(f"❌ Erro ao deletar feedbacks do agente: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# ROTAS DE ESTATÍSTICAS
# ==========================================

@router.get("/stats/{agent_id}")
async def get_learning_stats(
    agent_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Obter estatísticas de aprendizado do agente
    """
    try:
        # Contar acertos e erros
        total_acertos = await db.ai_learning_feedback.count_documents({
            "agent_id": agent_id,
            "tipo": "acerto"
        })
        
        total_erros = await db.ai_learning_feedback.count_documents({
            "agent_id": agent_id,
            "tipo": "erro"
        })
        
        total_aprovados = await db.ai_learning_feedback.count_documents({
            "agent_id": agent_id,
            "aprovado_admin": True
        })
        
        total = total_acertos + total_erros
        taxa_sucesso = (total_acertos / total * 100) if total > 0 else 0
        
        return {
            "agent_id": agent_id,
            "total_feedbacks": total,
            "total_acertos": total_acertos,
            "total_erros": total_erros,
            "total_aprovados": total_aprovados,
            "taxa_sucesso": round(taxa_sucesso, 2)
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# ROTA DE LIMPEZA (ADMIN)
# ==========================================

@router.delete("/conversations/cleanup")
async def cleanup_expired_conversations(
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Limpar conversas expiradas (> 60 dias)
    Usado pelo script de limpeza automática
    """
    try:
        now = datetime.now(timezone.utc).isoformat()
        
        result = await db.ai_conversation_memory.delete_many({
            "expires_at": {"$lt": now}
        })
        
        logger.info(f"✅ {result.deleted_count} conversas expiradas foram deletadas")
        
        return {
            "success": True,
            "deleted_count": result.deleted_count,
            "cleaned_at": now
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao limpar conversas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# ROTAS PARA SISTEMA DE APRENDIZADO DEPT
# ==========================================

@router.get("/learning/{agent_id}")
async def get_agent_learning_data(
    agent_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Obter dados de aprendizado de um agente específico
    """
    try:
        # Buscar interações com feedback
        learning_data = await db.ai_learning_feedback.find(
            {"agent_id": agent_id},
            {"_id": 0}
        ).sort("created_at", -1).limit(100).to_list(length=None)
        
        return learning_data
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar dados de aprendizado: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/learning/manual")
async def add_manual_learning(
    request: dict,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Adicionar exemplo de aprendizado manualmente (para treinamento)
    """
    try:
        agent_id = request.get("agent_id")
        user_message = request.get("user_message")
        ai_response = request.get("ai_response")
        feedback = request.get("feedback", "correct")
        
        if not agent_id or not user_message or not ai_response:
            raise HTTPException(status_code=400, detail="agent_id, user_message e ai_response são obrigatórios")
        
        # Criar registro de aprendizado manual
        learning_id = str(uuid.uuid4())
        learning_data = {
            "id": learning_id,
            "agent_id": agent_id,
            "user_message": user_message,
            "ai_response": ai_response,
            "feedback": feedback,
            "tipo": "acerto" if feedback == "correct" else "erro",
            "is_manual": True,  # Marcar como exemplo manual
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.ai_learning_feedback.insert_one(learning_data)
        
        logger.info(f"✅ Exemplo manual adicionado: {learning_id}")
        
        return {"success": True, "id": learning_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao adicionar exemplo manual: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/learning/{learning_id}/feedback")
async def save_learning_feedback(
    learning_id: str,
    request: dict,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Salvar feedback (correto/errado) para uma interação
    """
    try:
        is_correct = request.get("is_correct", False)
        feedback_value = "correct" if is_correct else "incorrect"
        
        result = await db.ai_learning_feedback.update_one(
            {"id": learning_id},
            {
                "$set": {
                    "feedback": feedback_value,
                    "tipo": "acerto" if is_correct else "erro",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Registro de aprendizado não encontrado")
        
        logger.info(f"✅ Feedback salvo: {learning_id} - {feedback_value}")
        
        return {"success": True, "feedback": feedback_value}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao salvar feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

