from fastapi import APIRouter
from fastapi.responses import FileResponse, Response
import os

router = APIRouter()

@router.get("/api/download-prompt")
async def download_prompt():
    """Download do prompt otimizado"""
    file_path = "/app/PROMPT_IA_FINAL_UTF8.txt"
    
    if os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            filename="PROMPT_IA_OPTIMIZED.txt",
            media_type="text/plain; charset=utf-8"
        )
    else:
        return Response(content="Arquivo não encontrado", status_code=404)

@router.get("/api/view-prompt")
async def view_prompt():
    """Visualizar conteúdo do prompt"""
    file_path = "/app/PROMPT_IA_FINAL_UTF8.txt"
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return Response(content=content, media_type="text/plain; charset=utf-8")
    else:
        return Response(content="Arquivo não encontrado", status_code=404)
