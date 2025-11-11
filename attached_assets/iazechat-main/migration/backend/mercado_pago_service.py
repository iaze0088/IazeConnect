"""
Serviço de Integração com Mercado Pago
"""
try:
    import mercadopago
except ImportError:
    print("⚠️ mercadopago not installed. Install: pip install mercadopago")
    mercadopago = None

from typing import Dict, Optional
import logging
import os

logger = logging.getLogger(__name__)

class MercadoPagoService:
    """Integração com Mercado Pago para pagamentos PIX"""
    
    def __init__(self, access_token: str):
        if mercadopago is None:
            raise ImportError("mercadopago library not installed")
        self.sdk = mercadopago.SDK(access_token)
        self.access_token = access_token
    
    async def create_pix_payment(
        self,
        amount: float,
        customer_email: str,
        customer_name: str,
        description: str,
        external_reference: str,
        notification_url: str
    ) -> Dict:
        """
        Criar pagamento PIX e retornar QR Code
        """
        try:
            payment_data = {
                "transaction_amount": float(amount),
                "description": description,
                "payment_method_id": "pix",
                "payer": {
                    "email": customer_email,
                    "first_name": customer_name.split()[0] if customer_name else "Cliente",
                    "last_name": " ".join(customer_name.split()[1:]) if len(customer_name.split()) > 1 else "",
                },
                "notification_url": notification_url,
                "external_reference": external_reference,
            }
            
            logger.info(f"🔍 Creating payment with data: {payment_data}")
            result = self.sdk.payment().create(payment_data)
            logger.info(f"🔍 Payment result: {result}")
            
            if result["status"] in [200, 201]:
                payment = result["response"]
                logger.info(f"✅ Payment created: {payment['id']}")
                
                # Extrair dados do PIX
                pix_data = self._extract_pix_data(payment)
                logger.info(f"🔍 PIX data extracted: qr_code={bool(pix_data['qr_code'])}, qr_code_base64={bool(pix_data['qr_code_base64'])}")
                
                if not pix_data["qr_code"]:
                    logger.error(f"❌ QR Code vazio! Payment response: {payment}")
                
                return {
                    "success": True,
                    "payment_id": str(payment["id"]),
                    "status": payment.get("status", "pending"),
                    "qr_code": pix_data["qr_code"],
                    "qr_code_base64": pix_data["qr_code_base64"],
                    "copy_paste_code": pix_data["qr_code"],
                    "expires_at": payment.get("date_of_expiration")
                }
            else:
                logger.error(f"❌ Payment creation failed: {result}")
                return {
                    "success": False,
                    "error": result.get("response", {}).get("message", "Erro ao criar pagamento")
                }
                
        except Exception as e:
            logger.error(f"❌ Error creating payment: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_pix_data(self, payment: Dict) -> Dict:
        """Extrair dados do QR Code PIX do pagamento"""
        try:
            point_of_interaction = payment.get("point_of_interaction", {})
            transaction_data = point_of_interaction.get("transaction_data", {})
            
            qr_code = transaction_data.get("qr_code", "")
            qr_code_base64 = transaction_data.get("qr_code_base64", "")
            
            return {
                "qr_code": qr_code,
                "qr_code_base64": qr_code_base64
            }
        except Exception as e:
            logger.error(f"Error extracting PIX data: {e}")
            return {
                "qr_code": "",
                "qr_code_base64": ""
            }
    
    async def get_payment_status(self, payment_id: str) -> Dict:
        """Buscar status de um pagamento"""
        try:
            result = self.sdk.payment().get(payment_id)
            
            if result["status"] == 200:
                payment = result["response"]
                return {
                    "success": True,
                    "status": payment.get("status"),
                    "status_detail": payment.get("status_detail"),
                    "external_reference": payment.get("external_reference"),
                    "transaction_amount": payment.get("transaction_amount")
                }
            else:
                return {
                    "success": False,
                    "error": "Payment not found"
                }
        except Exception as e:
            logger.error(f"Error getting payment status: {e}")
            return {
                "success": False,
                "error": str(e)
            }


async def get_mercado_pago_service(db) -> Optional[MercadoPagoService]:
    """
    Buscar configuração do Mercado Pago e criar serviço
    """
    config = await db.mercado_pago_config.find_one({}, {"_id": 0})
    
    if not config or not config.get("enabled"):
        logger.warning("⚠️ Mercado Pago não configurado ou desabilitado")
        return None
    
    access_token = config.get("access_token")
    if not access_token:
        logger.error("❌ Access token não configurado")
        return None
    
    return MercadoPagoService(access_token)
