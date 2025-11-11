"""
🔍 SISTEMA DE AUDIT LOG - Rastreamento completo de ações críticas
LGPD/GDPR Compliance Ready
"""

from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os
from typing import Optional, Dict, Any
import json

class AuditLogger:
    """
    Sistema de auditoria para compliance e segurança
    
    Registra todas as ações críticas:
    - Login/Logout
    - Criação/Modificação de dados sensíveis
    - Acesso a dados de outras revendas (tentativas de violação)
    - Alterações de configuração
    """
    
    def __init__(self):
        MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        DB_NAME = os.environ.get('DB_NAME', 'support_chat')
        
        self.client = AsyncIOMotorClient(MONGO_URL)
        self.db = self.client[DB_NAME]
        self.audit_collection = self.db.audit_logs
    
    async def log_action(
        self,
        action: str,
        user_id: str,
        user_type: str,
        reseller_id: Optional[str],
        details: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True
    ):
        """
        Registra uma ação no audit log
        
        Args:
            action: Nome da ação (ex: "LOGIN", "CREATE_TICKET", "DELETE_AGENT")
            user_id: ID do usuário que executou
            user_type: Tipo do usuário (admin, reseller, agent, client)
            reseller_id: ID da revenda (None para admin master)
            details: Detalhes adicionais da ação
            ip_address: IP de origem
            user_agent: User agent do navegador
            success: Se a ação foi bem-sucedida
        """
        
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "user_id": user_id,
            "user_type": user_type,
            "reseller_id": reseller_id,
            "details": details,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "success": success
        }
        
        await self.audit_collection.insert_one(log_entry)
    
    async def log_security_violation(
        self,
        user_id: str,
        user_type: str,
        reseller_id: Optional[str],
        attempted_action: str,
        target_reseller_id: str,
        ip_address: Optional[str] = None
    ):
        """
        Registra tentativa de violação de segurança multi-tenant
        
        ALERTA: Este log deve disparar notificações para admins
        """
        
        await self.log_action(
            action="SECURITY_VIOLATION",
            user_id=user_id,
            user_type=user_type,
            reseller_id=reseller_id,
            details={
                "attempted_action": attempted_action,
                "target_reseller_id": target_reseller_id,
                "severity": "HIGH",
                "alert": "Tentativa de acesso a dados de outra revenda"
            },
            ip_address=ip_address,
            success=False
        )
    
    async def log_login(
        self,
        user_id: str,
        user_type: str,
        reseller_id: Optional[str],
        ip_address: Optional[str] = None,
        success: bool = True
    ):
        """Registra tentativa de login"""
        
        await self.log_action(
            action="LOGIN",
            user_id=user_id,
            user_type=user_type,
            reseller_id=reseller_id,
            details={"login_time": datetime.now(timezone.utc).isoformat()},
            ip_address=ip_address,
            success=success
        )
    
    async def log_data_access(
        self,
        user_id: str,
        user_type: str,
        reseller_id: Optional[str],
        resource_type: str,
        resource_id: str,
        action: str = "READ"
    ):
        """Registra acesso a dados sensíveis"""
        
        await self.log_action(
            action=f"DATA_ACCESS_{action}",
            user_id=user_id,
            user_type=user_type,
            reseller_id=reseller_id,
            details={
                "resource_type": resource_type,
                "resource_id": resource_id
            },
            success=True
        )
    
    async def log_config_change(
        self,
        user_id: str,
        user_type: str,
        reseller_id: Optional[str],
        config_type: str,
        old_value: Any,
        new_value: Any
    ):
        """Registra mudanças de configuração"""
        
        await self.log_action(
            action="CONFIG_CHANGE",
            user_id=user_id,
            user_type=user_type,
            reseller_id=reseller_id,
            details={
                "config_type": config_type,
                "old_value": old_value,
                "new_value": new_value
            },
            success=True
        )
    
    async def get_user_activity(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ):
        """Retorna atividade de um usuário específico"""
        
        query = {"user_id": user_id}
        
        if start_date:
            query["timestamp"] = {"$gte": start_date.isoformat()}
        if end_date:
            if "timestamp" in query:
                query["timestamp"]["$lte"] = end_date.isoformat()
            else:
                query["timestamp"] = {"$lte": end_date.isoformat()}
        
        logs = await self.audit_collection.find(query).sort("timestamp", -1).limit(limit).to_list(None)
        return logs
    
    async def get_security_violations(
        self,
        reseller_id: Optional[str] = None,
        days: int = 30,
        limit: int = 100
    ):
        """Retorna violações de segurança recentes"""
        
        from datetime import timedelta
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        query = {
            "action": "SECURITY_VIOLATION",
            "timestamp": {"$gte": start_date.isoformat()}
        }
        
        if reseller_id:
            query["reseller_id"] = reseller_id
        
        violations = await self.audit_collection.find(query).sort("timestamp", -1).limit(limit).to_list(None)
        return violations

# Instância global
audit_logger = AuditLogger()
