"""
🛡️ SISTEMA DE RATE LIMITING
Proteção contra abuso e ataques DDoS

Limites por tipo de usuário:
- Admin: 1000 req/min
- Reseller: 500 req/min  
- Agent: 200 req/min
- Client: 100 req/min
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
import asyncio
from collections import defaultdict

class RateLimiter:
    """
    Rate limiter in-memory com sliding window
    
    Para produção, considere usar Redis para distribuição
    """
    
    def __init__(self):
        # Estrutura: {user_id: [(timestamp, count), ...]}
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = asyncio.Lock()
        
        # Limites por tipo de usuário (requests por minuto)
        self.limits = {
            "admin": 1000,
            "reseller": 500,
            "agent": 200,
            "client": 100
        }
        
        # Limites especiais para ações específicas
        self.action_limits = {
            "login": 10,  # 10 tentativas de login por minuto
            "create_ticket": 30,  # 30 tickets por minuto
            "send_message": 60  # 60 mensagens por minuto
        }
    
    async def check_rate_limit(
        self,
        user_id: str,
        user_type: str,
        action: Optional[str] = None
    ) -> tuple[bool, Optional[int]]:
        """
        Verifica se o usuário está dentro do rate limit
        
        Returns:
            (allowed, retry_after_seconds)
            - allowed: True se pode prosseguir
            - retry_after_seconds: Segundos até poder tentar novamente (se blocked)
        """
        
        async with self.lock:
            now = datetime.now(timezone.utc)
            one_minute_ago = now - timedelta(minutes=1)
            
            # Limpar requisições antigas
            if user_id in self.requests:
                self.requests[user_id] = [
                    (ts, count) for ts, count in self.requests[user_id]
                    if ts > one_minute_ago
                ]
            
            # Contar requisições no último minuto
            request_count = sum(count for ts, count in self.requests[user_id])
            
            # Determinar limite aplicável
            if action and action in self.action_limits:
                limit = self.action_limits[action]
            else:
                limit = self.limits.get(user_type, 100)
            
            # Verificar se excedeu o limite
            if request_count >= limit:
                # Calcular quando poderá tentar novamente
                oldest_request = min(ts for ts, _ in self.requests[user_id])
                retry_after = int((oldest_request + timedelta(minutes=1) - now).total_seconds())
                return False, max(retry_after, 1)
            
            # Adicionar esta requisição
            self.requests[user_id].append((now, 1))
            return True, None
    
    async def get_remaining_requests(
        self,
        user_id: str,
        user_type: str
    ) -> int:
        """Retorna quantas requisições restam no minuto atual"""
        
        async with self.lock:
            now = datetime.now(timezone.utc)
            one_minute_ago = now - timedelta(minutes=1)
            
            # Limpar requisições antigas
            if user_id in self.requests:
                self.requests[user_id] = [
                    (ts, count) for ts, count in self.requests[user_id]
                    if ts > one_minute_ago
                ]
            
            request_count = sum(count for ts, count in self.requests[user_id])
            limit = self.limits.get(user_type, 100)
            
            return max(0, limit - request_count)
    
    async def reset_user_limits(self, user_id: str):
        """Reseta os limites de um usuário específico"""
        async with self.lock:
            if user_id in self.requests:
                del self.requests[user_id]
    
    async def cleanup_old_entries(self):
        """Remove entradas antigas (executar periodicamente)"""
        async with self.lock:
            now = datetime.now(timezone.utc)
            one_hour_ago = now - timedelta(hours=1)
            
            users_to_remove = []
            
            for user_id, requests in self.requests.items():
                # Filtrar requisições antigas
                self.requests[user_id] = [
                    (ts, count) for ts, count in requests
                    if ts > one_hour_ago
                ]
                
                # Marcar para remoção se vazio
                if not self.requests[user_id]:
                    users_to_remove.append(user_id)
            
            # Remover usuários sem requisições recentes
            for user_id in users_to_remove:
                del self.requests[user_id]

# Instância global
rate_limiter = RateLimiter()


# Middleware para FastAPI
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

async def rate_limit_middleware(request: Request, call_next):
    """
    Middleware de rate limiting para FastAPI
    
    Adicione ao app:
    app.middleware("http")(rate_limit_middleware)
    """
    
    # Extrair user info do token (se presente)
    auth_header = request.headers.get("Authorization")
    
    if auth_header and auth_header.startswith("Bearer "):
        try:
            # Verificar token e extrair user_id e user_type
            # (implementação depende do sistema de auth)
            user_id = "extracted_from_token"
            user_type = "extracted_from_token"
            
            # Determinar action baseado no endpoint
            action = None
            if "/auth/" in request.url.path:
                action = "login"
            elif "/tickets" in request.url.path and request.method == "POST":
                action = "create_ticket"
            elif "/messages" in request.url.path and request.method == "POST":
                action = "send_message"
            
            # Verificar rate limit
            allowed, retry_after = await rate_limiter.check_rate_limit(
                user_id=user_id,
                user_type=user_type,
                action=action
            )
            
            if not allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Rate limit exceeded",
                        "retry_after": retry_after
                    },
                    headers={"Retry-After": str(retry_after)}
                )
        
        except Exception:
            # Se houver erro na verificação, permitir request
            pass
    
    # Processar request normalmente
    response = await call_next(request)
    return response
