"""
Serviço de Processamento Multimodal
Áudio, Imagem e Vídeo → Texto
"""
import os
import logging
import io
import base64
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime, timezone
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
from openai import OpenAI

logger = logging.getLogger(__name__)

class MediaService:
    """Serviço para processar áudio, imagem e vídeo"""
    
    def __init__(self):
        """Inicializa o serviço"""
        self.api_key = os.getenv("EMERGENT_LLM_KEY")
        if not self.api_key:
            raise ValueError("EMERGENT_LLM_KEY não encontrada nas variáveis de ambiente")
        
        # Cliente OpenAI para Whisper (áudio)
        self.openai_client = OpenAI(api_key=self.api_key)
        
        logger.info("MediaService inicializado com sucesso")
    
    async def transcribe_audio(
        self, 
        audio_data: bytes,
        filename: str,
        language: str = "pt"
    ) -> dict:
        """
        Transcreve áudio para texto usando OpenAI Whisper
        
        Args:
            audio_data: Dados binários do áudio
            filename: Nome do arquivo
            language: Idioma (default: pt - português)
            
        Returns:
            dict com texto transcrito e metadados
        """
        try:
            logger.info(f"Iniciando transcrição de áudio: {filename}")
            
            # Criar arquivo temporário
            with tempfile.NamedTemporaryFile(
                delete=False, 
                suffix=Path(filename).suffix
            ) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Transcrever usando Whisper
                with open(temp_file_path, 'rb') as audio_file:
                    transcript = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language=language,
                        response_format="verbose_json"
                    )
                
                result = {
                    "text": transcript.text,
                    "language": transcript.language if hasattr(transcript, 'language') else language,
                    "duration": transcript.duration if hasattr(transcript, 'duration') else None,
                    "type": "audio_transcription",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                logger.info(f"Transcrição concluída: {len(result['text'])} caracteres")
                return result
                
            finally:
                # Limpar arquivo temporário
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"Erro ao transcrever áudio: {str(e)}")
            raise ValueError(f"Falha na transcrição: {str(e)}")
    
    async def analyze_image(
        self,
        image_data: bytes,
        prompt: str = "Descreva esta imagem em detalhes. Se houver texto, transcreva-o."
    ) -> dict:
        """
        Analisa imagem usando GPT-4o Vision
        
        Args:
            image_data: Dados binários da imagem
            prompt: Pergunta sobre a imagem
            
        Returns:
            dict com análise da imagem
        """
        try:
            logger.info(f"Iniciando análise de imagem")
            
            # Converter imagem para base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Criar chat com GPT-4o Vision
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"image_analysis_{datetime.now().timestamp()}",
                system_message="Você é um assistente especializado em análise de imagens. Descreva tudo que vê em português, incluindo textos, objetos, pessoas e contexto."
            ).with_model("openai", "gpt-4o")
            
            # Criar mensagem com imagem
            image_content = ImageContent(image_base64=image_base64)
            message = UserMessage(
                text=prompt,
                file_contents=[image_content]
            )
            
            # Enviar e obter resposta
            response = await chat.send_message(message)
            
            result = {
                "text": response,
                "type": "image_analysis",
                "prompt": prompt,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Análise de imagem concluída: {len(response)} caracteres")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao analisar imagem: {str(e)}")
            raise ValueError(f"Falha na análise de imagem: {str(e)}")
    
    async def process_video(
        self,
        video_data: bytes,
        filename: str,
        extract_audio: bool = True,
        analyze_frames: bool = False,  # Desabilitado por padrão para velocidade
        frame_interval: int = 60  # Apenas 1 frame por minuto
    ) -> dict:
        """
        Placeholder function
        """
        return {"success": False, "error": "Not implemented"}


async def save_media_file(file_content: bytes, filename: str, content_type: str) -> str:
    """
    Salva arquivo de mídia localmente
    
    Args:
        file_content: Conteúdo do arquivo em bytes
        filename: Nome do arquivo
        content_type: Tipo MIME (image/jpeg, video/mp4, etc)
    
    Returns:
        URL do arquivo salvo
    """
    try:
        # Criar diretório de uploads se não existir
        uploads_dir = "/app/uploads"
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Gerar nome único
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(uploads_dir, safe_filename)
        
        # Salvar arquivo
        with open(filepath, 'wb') as f:
            f.write(file_content)
        
        # Retornar URL (assumindo que /app/uploads é servido em /api/uploads/)
        media_url = f"/api/uploads/{safe_filename}"
        
        logger.info(f"✅ Mídia salva: {media_url} ({len(file_content)} bytes)")
        return media_url
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar mídia: {e}")
        raise

        Processa vídeo: extrai áudio e analisa frames (OTIMIZADO)
        
        Args:
            video_data: Dados binários do vídeo
            filename: Nome do arquivo
            extract_audio: Se deve extrair e transcrever áudio
            analyze_frames: Se deve analisar frames (desabilitado por padrão)
            frame_interval: Intervalo entre frames (segundos)
            
        Returns:
            dict com transcrição do áudio e análise dos frames
        """
        try:
            logger.info(f"Iniciando processamento RÁPIDO de vídeo: {filename}")
            
            # Criar arquivo temporário para o vídeo
            with tempfile.NamedTemporaryFile(
                delete=False, 
                suffix=Path(filename).suffix
            ) as temp_video:
                temp_video.write(video_data)
                video_path = temp_video.name
            
            result = {
                "type": "video_processing",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            try:
                # 1. Extrair e transcrever áudio (OTIMIZADO)
                if extract_audio:
                    audio_path = video_path + "_audio.mp3"
                    
                    # Extrair áudio com FFmpeg OTIMIZADO (baixa qualidade, mais rápido)
                    subprocess.run([
                        'ffmpeg', '-i', video_path,
                        '-vn',  # Sem vídeo
                        '-acodec', 'libmp3lame',
                        '-ab', '64k',  # Qualidade reduzida (era 128k)
                        '-ar', '16000',  # Taxa de amostragem reduzida (era 44100)
                        '-ac', '1',  # Mono (era estéreo)
                        '-y',  # Sobrescrever
                        audio_path
                    ], check=True, capture_output=True, timeout=30)  # Timeout de 30s
                    
                    # Transcrever áudio
                    with open(audio_path, 'rb') as audio_file:
                        audio_data = audio_file.read()
                        transcription = await self.transcribe_audio(
                            audio_data,
                            "video_audio.mp3"
                        )
                    
                    result['audio_transcription'] = transcription['text']
                    result['audio_language'] = transcription['language']
                    
                    # Limpar arquivo de áudio
                    os.unlink(audio_path)
                
                # 2. Extrair e analisar frames
                if analyze_frames:
                    frames_dir = tempfile.mkdtemp()
                    frame_pattern = os.path.join(frames_dir, 'frame_%04d.jpg')
                    
                    # Extrair frames com FFmpeg
                    subprocess.run([
                        'ffmpeg', '-i', video_path,
                        '-vf', f'fps=1/{frame_interval}',  # 1 frame a cada N segundos
                        '-q:v', '2',  # Qualidade alta
                        '-y',
                        frame_pattern
                    ], check=True, capture_output=True)
                    
                    # Analisar frames (máximo 5 para não sobrecarregar)
                    frame_files = sorted(Path(frames_dir).glob('frame_*.jpg'))[:5]
                    frame_analyses = []
                    
                    for i, frame_path in enumerate(frame_files):
                        with open(frame_path, 'rb') as f:
                            frame_data = f.read()
                            analysis = await self.analyze_image(
                                frame_data,
                                f"Descreva o que está acontecendo neste frame do vídeo (frame {i+1})."
                            )
                            frame_analyses.append({
                                "frame_number": i + 1,
                                "analysis": analysis['text']
                            })
                    
                    result['frames_analysis'] = frame_analyses
                    
                    # Limpar frames
                    for frame_file in Path(frames_dir).glob('*'):
                        frame_file.unlink()
                    os.rmdir(frames_dir)
                
                # 3. Gerar resumo combinado
                if extract_audio or analyze_frames:
                    summary_parts = []
                    
                    if extract_audio and 'audio_transcription' in result:
                        summary_parts.append(f"ÁUDIO: {result['audio_transcription']}")
                    
                    if analyze_frames and 'frames_analysis' in result:
                        for frame in result['frames_analysis']:
                            summary_parts.append(f"FRAME {frame['frame_number']}: {frame['analysis']}")
                    
                    result['combined_summary'] = "\n\n".join(summary_parts)
                
                logger.info(f"Processamento de vídeo concluído")
                return result
                
            finally:
                # Limpar arquivo de vídeo
                if os.path.exists(video_path):
                    os.unlink(video_path)
                    
        except Exception as e:
            logger.error(f"Erro ao processar vídeo: {str(e)}")
            raise ValueError(f"Falha no processamento de vídeo: {str(e)}")
    
    async def save_training_knowledge(
        self,
        db,
        content: str,
        media_type: str,
        category: str = "treinamento_audio",
        agent_id: str = None
    ) -> str:
        """
        Salva conhecimento extraído de mídia na base de dados da IA
        
        Args:
            db: Conexão com MongoDB
            content: Conteúdo extraído (texto)
            media_type: Tipo de mídia (audio, image, video)
            category: Categoria do conhecimento
            agent_id: ID do agente (opcional, para conhecimento individual)
            
        Returns:
            ID do conhecimento salvo
        """
        try:
            knowledge = {
                "content": content,
                "media_type": media_type,
                "category": category,
                "agent_id": agent_id,
                "created_at": datetime.now(timezone.utc),
                "active": True
            }
            
            result = await db.ai_knowledge_base.insert_one(knowledge)
            logger.info(f"Conhecimento salvo: {result.inserted_id}")
            
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Erro ao salvar conhecimento: {str(e)}")
            raise ValueError(f"Falha ao salvar conhecimento: {str(e)}")


# Instância global do serviço
media_service = MediaService()
