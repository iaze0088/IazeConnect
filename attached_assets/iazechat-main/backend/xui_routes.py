"""
Rotas para Integração XUI
Permite consultar dados de clientes IPTV
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
import logging

from xui_service import XUIService
from server import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/xui", tags=["xui"])

# Instanciar serviço
xui_service = XUIService()

# ==================== MODELS ====================

class XUISearchRequest(BaseModel):
    keyword: str

class XUIUserResponse(BaseModel):
    username: str
    password: str
    expiration_date: str
    status: str
    is_active: bool
    max_connections: int
    active_connections: int
    package: Optional[str] = None
    created_at: Optional[str] = None
    notes: Optional[str] = None

# ==================== ROUTES ====================

@router.get("/check-connection")
async def check_xui_connection(
    current_user: dict = Depends(get_current_user)
):
    """
    Verificar se a conexão com XUI está funcionando
    """
    try:
        is_connected = await xui_service.check_connection()
        
        return {
            "success": True,
            "connected": is_connected,
            "xui_url": xui_service.xui_url
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao verificar conexão XUI: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search-user/{username}")
async def search_user_by_username(
    username: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Buscar usuário IPTV no XUI pelo nome de usuário exato
    """
    try:
        logger.info(f"🔍 Buscando usuário XUI: {username}")
        
        user_data = await xui_service.search_user_by_username(username)
        
        if not user_data:
            return {
                "success": False,
                "message": f"Usuário '{username}' não encontrado no XUI"
            }
        
        return {
            "success": True,
            "user": user_data
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar usuário XUI: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search-users")
async def search_users_by_keyword(
    request: XUISearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Buscar múltiplos usuários IPTV no XUI por palavra-chave
    Útil para buscar por nome, telefone, etc.
    """
    try:
        logger.info(f"🔍 Buscando usuários XUI com keyword: {request.keyword}")
        
        users = await xui_service.search_users_by_keyword(request.keyword)
        
        return {
            "success": True,
            "count": len(users),
            "users": users
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar usuários XUI: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-details/{username}")
async def get_user_details(
    username: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Obter detalhes completos de um usuário IPTV
    Retorna em formato formatado para exibição no chat
    """
    try:
        logger.info(f"📊 Obtendo detalhes do usuário XUI: {username}")
        
        user_data = await xui_service.search_user_by_username(username)
        
        if not user_data:
            return {
                "success": False,
                "message": f"Usuário '{username}' não encontrado",
                "formatted_message": f"❌ Usuário '{username}' não encontrado no sistema IPTV."
            }
        
        # Formatar mensagem para envio no chat
        formatted_message = f"""
📺 **Dados IPTV - {user_data['username']}**

👤 **Usuário:** {user_data['username']}
🔑 **Senha:** {user_data['password']}
📅 **Vencimento:** {user_data['expiration_date']}
🟢 **Status:** {user_data['status']}
📡 **Conexões:** {user_data['active_connections']}/{user_data['max_connections']}
"""
        
        if user_data.get('package'):
            formatted_message += f"📦 **Pacote:** {user_data['package']}\n"
        
        if user_data.get('notes'):
            formatted_message += f"📝 **Observações:** {user_data['notes']}\n"
        
        return {
            "success": True,
            "user": user_data,
            "formatted_message": formatted_message.strip()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter detalhes do usuário: {e}")
        raise HTTPException(status_code=500, detail=str(e))
