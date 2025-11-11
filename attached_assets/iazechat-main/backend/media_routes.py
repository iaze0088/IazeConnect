"""
Rotas da API para Processamento de Mídia
Áudio, Imagem e Vídeo
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
from typing import Optional
import logging
from datetime import datetime, timezone

from media_service import media_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/media", tags=["media"])

# Formatos suportados
AUDIO_FORMATS = ['mp3', 'wav', 'm4a', 'ogg', 'webm', 'mpeg', 'mpga']
IMAGE_FORMATS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']
VIDEO_FORMATS = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv']

def get_file_extension(filename: str) -> str:
    """Extrai extensão do arquivo"""
    return filename.lower().split('.')[-1] if '.' in filename else ''

def get_db(request: Request):
    """Dependency injection para obter conexão do banco"""
    return request.app.state.db

@router.post("/transcribe-audio")
async def transcribe_audio_endpoint(
    file: UploadFile = File(...),
    language: str = Form("pt"),
    save_as_training: bool = Form(False),
    agent_id: str = Form(None),
    request: Request = None
):
    """
    Transcreve áudio para texto
    
    - **file**: Arquivo de áudio (mp3, wav, m4a, etc.)
    - **language**: Idioma do áudio (pt, en, es, etc.)
    - **save_as_training**: Se True, salva como conhecimento da IA
    - **agent_id**: ID do agente (opcional, para conhecimento individual)
    """
    try:
        # Validar formato
        ext = get_file_extension(file.filename)
        if ext not in AUDIO_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Formato não suportado. Use: {', '.join(AUDIO_FORMATS)}"
            )
        
        # Ler dados do arquivo
        audio_data = await file.read()
        
        # Validar tamanho (máximo 25MB para Whisper)
        if len(audio_data) > 25 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="Arquivo muito grande. Máximo: 25MB"
            )
        
        # Transcrever
        result = await media_service.transcribe_audio(
            audio_data=audio_data,
            filename=file.filename,
            language=language
        )
        
        # Salvar como conhecimento da IA se solicitado
        if save_as_training and request:
            db = request.app.state.db if hasattr(request.app.state, 'db') else None
            if db:
                knowledge_id = await media_service.save_training_knowledge(
                    db=db,
                    content=result['text'],
                    media_type="audio",
                    category="treinamento_audio",
                    agent_id=agent_id
                )
                result['knowledge_id'] = knowledge_id
                result['saved_as_training'] = True
        
        return {
            "success": True,
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao transcrever áudio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-image")
async def analyze_image_endpoint(
    file: UploadFile = File(...),
    prompt: str = Form("Descreva esta imagem em detalhes. Se houver texto, transcreva-o.")
):
    """
    Analisa imagem usando GPT-4o Vision
    
    - **file**: Arquivo de imagem (jpg, png, etc.)
    - **prompt**: Pergunta sobre a imagem
    """
    try:
        # Validar formato
        ext = get_file_extension(file.filename)
        if ext not in IMAGE_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Formato não suportado. Use: {', '.join(IMAGE_FORMATS)}"
            )
        
        # Ler dados do arquivo
        image_data = await file.read()
        
        # Validar tamanho (máximo 20MB)
        if len(image_data) > 20 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="Imagem muito grande. Máximo: 20MB"
            )
        
        # Analisar imagem
        result = await media_service.analyze_image(
            image_data=image_data,
            prompt=prompt
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao analisar imagem: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-video")
async def process_video_endpoint(
    file: UploadFile = File(...),
    extract_audio: bool = Form(True),
    analyze_frames: bool = Form(True)
):
    """
    Processa vídeo: extrai áudio e analisa frames
    
    - **file**: Arquivo de vídeo (mp4, avi, etc.)
    - **extract_audio**: Se deve extrair e transcrever áudio
    - **analyze_frames**: Se deve analisar frames do vídeo
    """
    try:
        # Validar formato
        ext = get_file_extension(file.filename)
        if ext not in VIDEO_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Formato não suportado. Use: {', '.join(VIDEO_FORMATS)}"
            )
        
        # Ler dados do arquivo
        video_data = await file.read()
        
        # Validar tamanho (máximo 50MB)
        if len(video_data) > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="Vídeo muito grande. Máximo: 50MB"
            )
        
        # Processar vídeo
        result = await media_service.process_video(
            video_data=video_data,
            filename=file.filename,
            extract_audio=extract_audio,
            analyze_frames=analyze_frames
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar vídeo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/training-knowledge")
async def list_training_knowledge(
    skip: int = 0,
    limit: int = 50,
    agent_id: str = None,
    request: Request = None
):
    """
    Lista conhecimentos de treinamento salvos
    """
    try:
        db = request.app.state.db if request and hasattr(request.app.state, 'db') else None
        if not db:
            raise HTTPException(status_code=500, detail="Banco de dados não disponível")
        
        # Filtro por agente se fornecido
        filter_query = {"category": "treinamento_audio", "active": True}
        if agent_id:
            filter_query["agent_id"] = agent_id
        
        knowledge_list = await db.ai_knowledge_base.find(
            filter_query
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
        
        # Converter ObjectId para string
        for item in knowledge_list:
            item['_id'] = str(item['_id'])
            if 'created_at' in item:
                item['created_at'] = item['created_at'].isoformat()
        
        total = await db.ai_knowledge_base.count_documents(filter_query)
        
        return {
            "success": True,
            "data": {
                "items": knowledge_list,
                "total": total,
                "skip": skip,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao listar conhecimentos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/training-knowledge/{knowledge_id}")
async def delete_training_knowledge(knowledge_id: str, request: Request = None):
    """
    Desativa um conhecimento de treinamento
    """
    try:
        db = request.app.state.db if request and hasattr(request.app.state, 'db') else None
        if not db:
            raise HTTPException(status_code=500, detail="Banco de dados não disponível")
        
        result = await db.ai_knowledge_base.update_one(
            {"_id": knowledge_id},
            {"$set": {"active": False}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Conhecimento não encontrado")
        
        return {
            "success": True,
            "message": "Conhecimento desativado com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar conhecimento: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/supported-formats")
async def get_supported_formats():
    """Retorna formatos de mídia suportados"""
    return {
        "audio": AUDIO_FORMATS,
        "image": IMAGE_FORMATS,
        "video": VIDEO_FORMATS
    }
