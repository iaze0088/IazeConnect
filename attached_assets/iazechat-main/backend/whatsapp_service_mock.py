"""
Mock do WPPConnect para testes quando servidor está offline
"""
from typing import Dict, Any, Optional
import base64
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class WPPConnectMockService:
    """Serviço mock para testes quando WPPConnect está offline"""
    
    def __init__(self):
        self.base_url = "http://95.217.178.51:21465"
        self.secret_key = "THISISMYSECURETOKEN"
        # QR Code fake para testes
        self.fake_qr = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    
    async def create_session(self, session_name: str, webhook_url: Optional[str] = None) -> Dict[str, Any]:
        """Mock: Cria sessão fake para testes"""
        print(f"🧪 [MOCK] Criando sessão fake: {session_name}", flush=True)
        
        if webhook_url:
            print(f"🧪 [MOCK] Webhook registrado: {webhook_url}", flush=True)
        
        # Token fake
        token = f"mock_token_{session_name}_{int(datetime.now().timestamp())}"
        
        return {
            "success": True,
            "qr_code": self.fake_qr,
            "status": "QRCODE",
            "session": session_name,
            "token": token
        }
    
    async def get_session_status(self, session_name: str, token: str, last_known_status: Optional[Dict] = None) -> Dict[str, Any]:
        """Mock: Retorna status fake"""
        print(f"🧪 [MOCK] Consultando status fake: {session_name}", flush=True)
        
        # Retorna último status conhecido se disponível
        if last_known_status:
            return last_known_status
        
        return {
            "success": True,
            "status": "connecting",
            "connected": False,
            "from_cache": True
        }
    
    async def close_session(self, session_name: str, token: str) -> Dict[str, Any]:
        """Mock: Fecha sessão fake"""
        print(f"🧪 [MOCK] Fechando sessão fake: {session_name}", flush=True)
        return {"success": True}
    
    async def close(self):
        """Mock: Nada a fazer"""
        pass

# Instância global mock
mock_service = WPPConnectMockService()

def get_mock_service() -> WPPConnectMockService:
    return mock_service
