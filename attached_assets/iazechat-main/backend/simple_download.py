from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, FileResponse
import os

router = APIRouter()

@router.get("/prompt-txt")
async def get_prompt_txt():
    """Retorna o prompt como texto simples"""
    file_path = "/app/PROMPT_IA_FINAL_UTF8.txt"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return Response(
            content=content,
            media_type="text/plain; charset=utf-8",
            headers={
                "Content-Disposition": "attachment; filename=PROMPT_IA_OPTIMIZED.txt",
                "Access-Control-Allow-Origin": "*"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler arquivo: {str(e)}")
