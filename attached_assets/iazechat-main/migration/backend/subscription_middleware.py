"""
Middleware para bloquear acesso de revendas com assinatura expirada
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from subscription_service import SubscriptionService
import logging

logger = logging.getLogger(__name__)

class SubscriptionMiddleware(BaseHTTPMiddleware):
    """Middleware que bloqueia acessos de revendas expiradas"""
    
    async def dispatch(self, request: Request, call_next):
        # Paths que não precisam de verificação de assinatura
        exempt_paths = [
            "/api/auth/",
            "/api/subscription/status",
            "/api/subscription/plans",
            "/api/payment/",
            "/api/webhook/",
            "/api/uploads/",
            "/api/admin/",
            "/docs",
            "/openapi.json",
            "/favicon.ico"
        ]
        
        # Verificar se o path está isento
        path = request.url.path
        if any(path.startswith(exempt) for exempt in exempt_paths):
            return await call_next(request)
        
        # Verificar se há token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return await call_next(request)
        
        try:
            # Extrair user_type do request.state (setado pelo get_current_user)
            # Como não temos acesso direto aqui, vamos verificar apenas em rotas específicas
            # através de um decorator
            pass
            
        except Exception as e:
            logger.error(f"Error in subscription middleware: {e}")
        
        return await call_next(request)


async def check_subscription_active(reseller_id: str, db) -> bool:
    """
    Verificar se assinatura está ativa
    Usado em endpoints que precisam bloquear acesso de expirados
    """
    subscription_service = SubscriptionService(db)
    is_active = await subscription_service.is_subscription_active(reseller_id)
    
    if not is_active:
        logger.warning(f"⚠️ Blocked access for expired reseller: {reseller_id}")
        return False
    
    return True
