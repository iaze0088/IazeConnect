"""
External Storage Service - Servidor Evolution (80TB)
Gerencia upload e download de arquivos no servidor dedicado
"""
import aiohttp
import os
import logging
import uuid
import aiofiles
from typing import Optional, Dict
from fastapi import UploadFile
from pathlib import Path

logger = logging.getLogger(__name__)

class ExternalStorageService:
    """Serviço para gerenciar arquivos no servidor Evolution (80TB)"""
    
    def __init__(self):
        # Configuração do servidor externo
        self.external_host = os.environ.get('EXTERNAL_STORAGE_HOST', '198.96.94.106')
        self.external_port = os.environ.get('EXTERNAL_STORAGE_PORT', '9000')
        self.upload_endpoint = f"http://{self.external_host}:{self.external_port}/upload"
        self.files_base_url = f"http://{self.external_host}:{self.external_port}/uploads"
        
        # Configuração local (fallback)
        self.use_external = os.environ.get('USE_EXTERNAL_STORAGE', 'false').lower() == 'true'
        
        # Diretório local (fallback)
        try:
            self.local_uploads_dir = Path("/data/uploads")
            self.local_uploads_dir.mkdir(parents=True, exist_ok=True)
            # Testar escrita
            test_file = self.local_uploads_dir / ".test"
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            self.local_uploads_dir = Path("/app/backend/uploads")
            self.local_uploads_dir.mkdir(parents=True, exist_ok=True)
            logger.warning(f"⚠️ Fallback para {self.local_uploads_dir}: {e}")
        
        logger.info(f"📦 ExternalStorageService inicializado")
        logger.info(f"   External: {self.use_external}")
        logger.info(f"   Host: {self.external_host}:{self.external_port}")
        logger.info(f"   Local Dir: {self.local_uploads_dir}")
    
    async def upload_file(self, file: UploadFile) -> Dict[str, any]:
        """
        Upload de arquivo para servidor externo ou local
        
        Returns:
            {
                'success': True,
                'filename': 'abc123.jpg',
                'url': 'http://198.96.94.106:9000/uploads/abc123.jpg',
                'size': 12345
            }
        """
        if self.use_external:
            return await self._upload_to_external(file)
        else:
            return await self._upload_to_local(file)
    
    async def _upload_to_external(self, file: UploadFile) -> Dict[str, any]:
        """Upload para servidor Evolution via HTTP"""
        try:
            # Ler conteúdo do arquivo
            content = await file.read()
            await file.seek(0)  # Reset para ler novamente se necessário
            
            # Preparar multipart form data
            data = aiohttp.FormData()
            data.add_field('file',
                          content,
                          filename=file.filename,
                          content_type=file.content_type or 'application/octet-stream')
            
            # Enviar para servidor externo
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(self.upload_endpoint, data=data) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"✅ Arquivo enviado para servidor externo: {result.get('filename')} ({len(content)} bytes)")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Erro no upload externo: {response.status} - {error_text}")
                        raise Exception(f"External storage error: {response.status}")
        
        except Exception as e:
            logger.error(f"❌ Falha no upload externo: {e}")
            logger.warning("⚠️ Fazendo fallback para storage local...")
            return await self._upload_to_local(file)
    
    async def _upload_to_local(self, file: UploadFile) -> Dict[str, any]:
        """Upload para storage local (fallback)"""
        # Gerar nome único
        extension = Path(file.filename).suffix if file.filename else '.bin'
        filename = f"{uuid.uuid4()}{extension}"
        file_path = self.local_uploads_dir / filename
        
        # Salvar arquivo
        content = await file.read()
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # URL local (será servida pelo backend IAZE)
        backend_url = os.environ.get('REACT_APP_BACKEND_URL', '')
        url = f"{backend_url}/api/uploads/{filename}"
        
        logger.info(f"✅ Arquivo salvo localmente: {filename} ({len(content)} bytes)")
        
        return {
            'success': True,
            'filename': filename,
            'url': url,
            'size': len(content),
            'local': True
        }
    
    def get_file_url(self, filename: str) -> str:
        """Retorna URL completa do arquivo"""
        if self.use_external:
            return f"{self.files_base_url}/{filename}"
        else:
            backend_url = os.environ.get('REACT_APP_BACKEND_URL', '')
            return f"{backend_url}/api/uploads/{filename}"

# Instância global
external_storage = ExternalStorageService()
