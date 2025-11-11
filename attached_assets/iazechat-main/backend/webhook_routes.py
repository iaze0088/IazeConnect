"""
Webhook do Mercado Pago para confirmação de pagamentos
"""
from fastapi import APIRouter, Request, HTTPException
from subscription_service import SubscriptionService
from bonus_service import BonusService
from mercado_pago_service import get_mercado_pago_service
from server import db
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/webhook/mercado-pago")
async def mercado_pago_webhook(request: Request):
    """
    Receber notificações de pagamento do Mercado Pago
    
    Quando pagamento é aprovado:
    1. Renova assinatura por 30 dias
    2. Deduz bônus usado (se houver)
    3. Credita 10% de bônus para revenda pai (se houver)
    """
    try:
        # Obter body
        body = await request.body()
        webhook_data = json.loads(body)
        
        logger.info(f"📥 Webhook received: {webhook_data}")
        
        # Extrair tipo de notificação
        notification_type = webhook_data.get("type")
        
        # Processar apenas notificações de pagamento
        if notification_type != "payment":
            logger.info(f"⚠️ Ignoring notification type: {notification_type}")
            return {"status": "ignored"}
        
        # Obter ID do pagamento
        data = webhook_data.get("data", {})
        payment_id = data.get("id")
        
        if not payment_id:
            logger.error("❌ No payment ID in webhook")
            return {"status": "error", "message": "No payment ID"}
        
        logger.info(f"💳 Processing payment: {payment_id}")
        
        # Buscar serviço Mercado Pago
        mp_service = await get_mercado_pago_service(db)
        if not mp_service:
            logger.error("❌ Mercado Pago not configured")
            return {"status": "error", "message": "MP not configured"}
        
        # Buscar status do pagamento na API do Mercado Pago
        payment_status_result = await mp_service.get_payment_status(str(payment_id))
        
        if not payment_status_result["success"]:
            logger.error(f"❌ Failed to get payment status: {payment_id}")
            return {"status": "error", "message": "Failed to get payment"}
        
        payment_status = payment_status_result["status"]
        external_reference = payment_status_result.get("external_reference")
        
        logger.info(f"💳 Payment {payment_id} status: {payment_status}")
        
        # Buscar pagamento no banco
        payment_record = await db.payments.find_one(
            {"payment_id": str(payment_id)},
            {"_id": 0}
        )
        
        if not payment_record:
            logger.warning(f"⚠️ Payment not found in database: {payment_id}")
            # Buscar por external_reference
            if external_reference:
                payment_record = await db.payments.find_one(
                    {"external_reference": external_reference},
                    {"_id": 0}
                )
        
        if not payment_record:
            logger.error(f"❌ Payment record not found: {payment_id}")
            return {"status": "error", "message": "Payment not found"}
        
        # Verificar se já foi processado
        if payment_record.get("status") == "approved":
            logger.info(f"✅ Payment already processed: {payment_id}")
            return {"status": "already_processed"}
        
        # Processar pagamento aprovado
        if payment_status == "approved":
            logger.info(f"🎉 Payment APPROVED: {payment_id}")
            
            reseller_id = payment_record["reseller_id"]
            plan_type = payment_record["plan_type"]
            bonus_used = payment_record.get("bonus_used", 0.0)
            bonus_reserved = payment_record.get("bonus_reserved", 0.0)
            
            # Inicializar serviços
            subscription_service = SubscriptionService(db)
            bonus_service = BonusService(db)
            
            # 1. Renovar assinatura por 30 dias
            await subscription_service.renew_subscription(
                reseller_id=reseller_id,
                plan_type=plan_type,
                payment_id=str(payment_id)
            )
            logger.info(f"✅ Subscription renewed for reseller: {reseller_id}")
            
            # 2. Deduzir bônus usado (se houver)
            if bonus_used > 0 or bonus_reserved > 0:
                bonus_amount = max(bonus_used, bonus_reserved)
                await bonus_service.use_bonus_on_payment(
                    reseller_id=reseller_id,
                    bonus_to_use=bonus_amount,
                    payment_id=str(payment_id)
                )
                logger.info(f"💰 Bonus used: R$ {bonus_amount:.2f}")
            
            # 3. Creditar 10% de bônus para revenda pai (se houver)
            final_amount = payment_record.get("final_amount", 0.0)
            plan_price = payment_record.get("plan_price", final_amount)
            
            bonus_transaction = await bonus_service.credit_bonus_to_parent(
                payment_amount=plan_price,  # Bônus sobre o valor cheio, não o descontado
                sub_reseller_id=reseller_id,
                payment_id=str(payment_id)
            )
            
            if bonus_transaction:
                logger.info(f"🎁 Bonus credited to parent reseller")
            
            # 4. Atualizar status do pagamento no banco
            await db.payments.update_one(
                {"payment_id": str(payment_id)},
                {
                    "$set": {
                        "status": "approved",
                        "approved_at": webhook_data.get("date_approved")
                    }
                }
            )
            
            logger.info(f"✅ Payment processing complete: {payment_id}")
            
        elif payment_status in ["rejected", "cancelled"]:
            # Pagamento rejeitado/cancelado
            await db.payments.update_one(
                {"payment_id": str(payment_id)},
                {"$set": {"status": payment_status}}
            )
            logger.info(f"❌ Payment {payment_status}: {payment_id}")
        
        return {"status": "processed"}
        
    except json.JSONDecodeError:
        logger.error("❌ Invalid JSON in webhook")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        logger.error(f"❌ Error processing webhook: {str(e)}")
        import traceback
        traceback.print_exc()
        # Retornar 200 mesmo com erro para não fazer Mercado Pago retentar
        return {"status": "error", "message": str(e)}
