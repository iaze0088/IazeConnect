"""
Serviço WhatsApp WPPConnect v2 com Fallback
"""
from typing import Dict, Any, Optional
import httpx
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class WPPConnectService:
    def __init__(self):
        self.base_url = "http://localhost:21465"
        self.secret_key = "THISISMYSECURETOKEN"
        self.client: Optional[httpx.AsyncClient] = None
    
    def get_client(self) -> httpx.AsyncClient:
        if self.client is None:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(10.0, connect=5.0),
                follow_redirects=True
            )
        return self.client
    
    async def close(self):
        if self.client:
            await self.client.aclose()
    
    async def create_session(self, session_name: str, webhook_url: Optional[str] = None) -> Dict[str, Any]:
        """Cria nova sessão WPPConnect com webhook"""
        try:
            client = self.get_client()
            # Estrutura correta: /api/:session/:secretkey/generate-token
            url = f"{self.base_url}/api/{session_name}/{self.secret_key}/generate-token"
            
            # Primeiro gerar token
            print(f"🔑 [WPPConnect] Gerando token para: {session_name}", flush=True)
            print(f"🔗 [WPPConnect] URL: {url}", flush=True)
            
            response = await client.post(url)
            
            print(f"📡 [WPPConnect] Status do generate-token: {response.status_code}", flush=True)
            print(f"📊 [WPPConnect] Resposta: {response.text[:200]}", flush=True)
            
            if response.status_code != 201 and response.status_code != 200:
                error_msg = f"Erro ao gerar token: Status {response.status_code}, Resposta: {response.text[:100]}"
                print(f"❌ [WPPConnect] {error_msg}", flush=True)
                return {"success": False, "error": error_msg}
            
            token_data = response.json()
            token = token_data.get("token")
            
            if not token:
                error_msg = f"Token não retornado. Resposta completa: {token_data}"
                print(f"❌ [WPPConnect] {error_msg}", flush=True)
                return {"success": False, "error": error_msg}
            
            print(f"✅ [WPPConnect] Token gerado: {token[:20]}...", flush=True)
            
            # Agora iniciar sessão com webhook
            return await self.start_session(session_name, token, webhook_url)
            
        except Exception as e:
            error_msg = f"Exceção ao criar sessão: {type(e).__name__}: {str(e)}"
            print(f"❌ [WPPConnect] {error_msg}", flush=True)
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    async def start_session(self, session_name: str, token: str, webhook_url: Optional[str] = None) -> Dict[str, Any]:
        """Inicia sessão WPPConnect com webhook"""
        try:
            client = self.get_client()
            url = f"{self.base_url}/api/{session_name}/start-session"
            
            payload = {
                "waitQrCode": True
            }
            
            if webhook_url:
                payload["webhook"] = webhook_url
                print(f"🔗 [WPPConnect] Registrando webhook: {webhook_url}", flush=True)
            
            print(f"🚀 [WPPConnect] Iniciando sessão: {url}", flush=True)
            print(f"📦 [WPPConnect] Payload: {payload}", flush=True)
            
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )
            
            print(f"📡 [WPPConnect] Status do start-session: {response.status_code}", flush=True)
            print(f"📊 [WPPConnect] Resposta start-session: {response.text[:300]}", flush=True)
            
            if response.status_code == 201 or response.status_code == 200:
                data = response.json()
                qr_code = data.get("qrcode") or data.get("qr") or data.get("base64")
                
                if qr_code:
                    print(f"✅ [WPPConnect] QR Code recebido (tamanho: {len(qr_code)})", flush=True)
                else:
                    print(f"⚠️ [WPPConnect] QR Code não encontrado na resposta", flush=True)
                
                return {
                    "success": True,
                    "qr_code": qr_code,
                    "status": data.get("status", "QRCODE"),
                    "session": session_name,
                    "token": token
                }
            else:
                error_msg = f"Status {response.status_code}: {response.text[:200]}"
                print(f"❌ [WPPConnect] {error_msg}", flush=True)
                return {"success": False, "error": error_msg}
            
        except Exception as e:
            error_msg = f"Exceção ao iniciar sessão: {type(e).__name__}: {str(e)}"
            print(f"❌ [WPPConnect] {error_msg}", flush=True)
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    async def get_session_status(self, session_name: str, token: str, last_known_status: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Verifica status da sessão com FALLBACK
        Se API não responder, usa último status conhecido
        """
        try:
            client = self.get_client()
            url = f"{self.base_url}/api/{session_name}/status-session"
            headers = {"Authorization": f"Bearer {token}"}
            
            print(f"🔍 [WPPConnect] Verificando status: {url}", flush=True)
            
            response = await client.get(url, headers=headers, timeout=5.0)
            
            print(f"📡 [WPPConnect] Status Code: {response.status_code}", flush=True)
            
            if response.status_code != 200:
                # Fallback: Usar último status conhecido
                if last_known_status:
                    print("⚠️ [WPPConnect] API indisponível, usando último status conhecido", flush=True)
                    return last_known_status
                
                return {"success": False, "status": "CLOSED", "connected": False}
            
            data = response.json()
            print(f"📊 [WPPConnect] Resposta: {data}", flush=True)
            
            # Verificar múltiplos campos que podem indicar conexão
            is_connected = (
                data.get("state") == "CONNECTED" or
                data.get("status") == "CONNECTED" or
                data.get("connected") or
                str(data.get("state", "")).upper() == "CONNECTED" or
                data.get("state") == "isLogged"
            )
            
            return {
                "success": True,
                "status": data.get("state") or data.get("status", "CLOSED"),
                "connected": is_connected,
                "phone": data.get("phone") or data.get("number")
            }
            
        except httpx.TimeoutException:
            print("⏱️ [WPPConnect] Timeout - API não respondeu", flush=True)
            # Fallback: Usar último status conhecido do banco de dados
            if last_known_status:
                print("💾 [WPPConnect] Usando último status conhecido do banco", flush=True)
                return last_known_status
            return {"success": False, "status": "API_TIMEOUT", "connected": False}
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar status: {e}")
            # Fallback
            if last_known_status:
                return last_known_status
            return {"success": False, "status": "ERROR", "connected": False}
    
    async def close_session(self, session_name: str, token: str) -> Dict[str, Any]:
        """Fecha sessão WPPConnect"""
        try:
            client = self.get_client()
            url = f"{self.base_url}/api/{session_name}/close-session"
            headers = {"Authorization": f"Bearer {token}"}
            
            response = await client.post(url, headers=headers)
            return {"success": response.status_code == 200}
            
        except Exception as e:
            logger.error(f"❌ Erro ao fechar sessão: {e}")
            return {"success": False, "error": str(e)}

# Instância global
wppconnect_service = WPPConnectService()

def get_whatsapp_service() -> WPPConnectService:
    return wppconnect_service
