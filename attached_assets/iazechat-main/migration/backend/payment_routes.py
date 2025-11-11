"""
Rotas de Pagamentos e Assinaturas
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from subscription_models import CreatePaymentRequest, PaymentResponse, PlanType
from subscription_service import SubscriptionService, SUBSCRIPTION_PLANS
from bonus_service import BonusService
from mercado_pago_service import get_mercado_pago_service
from server import get_current_user, db
from datetime import datetime, timezone
import uuid
import os

router = APIRouter()

@router.get("/subscription/status")
async def get_subscription_status(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Obter status da assinatura do revendedor"""
    if current_user["user_type"] != "reseller":
        raise HTTPException(status_code=403, detail="Apenas revendedores")
    
    reseller_id = current_user.get("reseller_id")
    
    subscription_service = SubscriptionService(db)
    bonus_service = BonusService(db)
    
    subscription = await subscription_service.get_subscription(reseller_id)
    
    # Se não tem assinatura, criar uma expirada por padrão
    if not subscription:
        # Criar assinatura padrão expirada
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        expired_date = now - timedelta(days=1)
        
        new_subscription = {
            "id": str(uuid.uuid4()),
            "reseller_id": reseller_id,
            "plan_type": "basico",
            "status": "expired",
            "trial_ends_at": expired_date.isoformat(),
            "current_period_start": expired_date.isoformat(),
            "current_period_end": expired_date.isoformat(),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        await db.subscriptions.insert_one(new_subscription)
        subscription = await subscription_service.get_subscription(reseller_id)
    
    # Buscar informações adicionais
    days_left = await subscription_service.get_days_until_expiration(reseller_id)
    bonus_balance = await bonus_service.get_bonus_balance(reseller_id)
    sub_resellers_count = await bonus_service.get_sub_resellers_count(reseller_id)
    sub_resellers_active = await bonus_service.get_sub_resellers_active_count(reseller_id)
    show_warning = await subscription_service.should_show_expiration_warning(reseller_id)
    
    return {
        "subscription": subscription,
        "days_left": days_left,
        "bonus_balance": bonus_balance,
        "sub_resellers_count": sub_resellers_count,
        "sub_resellers_active": sub_resellers_active,
        "show_expiration_warning": show_warning
    }

@router.get("/subscription/plans")
async def get_available_plans():
    """Listar planos disponíveis"""
    return {
        "plans": SUBSCRIPTION_PLANS
    }

@router.post("/payment/create", response_model=PaymentResponse)
async def create_payment(
    data: CreatePaymentRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Criar pagamento PIX para renovação de assinatura
    Permite usar bônus como desconto
    """
    if current_user["user_type"] != "reseller":
        raise HTTPException(status_code=403, detail="Apenas revendedores")
    
    reseller_id = current_user.get("reseller_id")
    
    # Validar plano
    if data.plan_type not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Plano inválido")
    
    plan = SUBSCRIPTION_PLANS[data.plan_type]
    plan_price = plan["price"]
    
    # Buscar serviço Mercado Pago
    mp_service = await get_mercado_pago_service(db)
    if not mp_service:
        raise HTTPException(
            status_code=503,
            detail="Mercado Pago não configurado. Contate o administrador."
        )
    
    bonus_service = BonusService(db)
    subscription_service = SubscriptionService(db)
    
    # Buscar bônus disponível
    bonus_balance = await bonus_service.get_bonus_balance(reseller_id)
    
    # Calcular valor final com desconto de bônus
    bonus_to_use = min(bonus_balance, plan_price)  # Não pode usar mais que o valor do plano
    final_amount = plan_price - bonus_to_use
    
    # Valor mínimo R$ 0,01
    if final_amount < 0.01:
        final_amount = 0.01
    
    # Criar referência única
    external_reference = f"{reseller_id}_{data.plan_type}_{uuid.uuid4().hex[:12]}"
    
    # Buscar dados do revendedor
    reseller = await db.resellers.find_one({"id": reseller_id}, {"_id": 0})
    if not reseller:
        raise HTTPException(status_code=404, detail="Revendedor não encontrado")
    
    # URL do webhook
    backend_url = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
    notification_url = f"{backend_url}/api/webhook/mercado-pago"
    
    # Criar pagamento no Mercado Pago
    result = await mp_service.create_pix_payment(
        amount=final_amount,
        customer_email=data.customer_email,
        customer_name=data.customer_name,
        description=f"Assinatura {plan['name']} - {reseller.get('subdomain', 'Revenda')}",
        external_reference=external_reference,
        notification_url=notification_url
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Salvar informações do pagamento no banco
    payment_record = {
        "id": str(uuid.uuid4()),
        "payment_id": result["payment_id"],
        "reseller_id": reseller_id,
        "plan_type": data.plan_type,
        "plan_price": plan_price,
        "bonus_used": bonus_to_use,
        "final_amount": final_amount,
        "status": "pending",
        "external_reference": external_reference,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.payments.insert_one(payment_record)
    
    # Se usou bônus, registrar uso (mas só deduzir quando pagamento for confirmado)
    if bonus_to_use > 0:
        await db.payments.update_one(
            {"id": payment_record["id"]},
            {"$set": {"bonus_reserved": bonus_to_use}}
        )
    
    return PaymentResponse(
        payment_id=result["payment_id"],
        qr_code=result["qr_code"],
        qr_code_base64=result["qr_code_base64"],
        copy_paste_code=result["copy_paste_code"],
        amount=final_amount,
        plan_type=data.plan_type,
        expires_at=result.get("expires_at"),
        status=result["status"]
    )

@router.get("/payment/{payment_id}/status")
async def get_payment_status(
    payment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Verificar status de um pagamento"""
    if current_user["user_type"] != "reseller":
        raise HTTPException(status_code=403, detail="Apenas revendedores")
    
    # Buscar pagamento no banco
    payment = await db.payments.find_one(
        {"payment_id": payment_id},
        {"_id": 0}
    )
    
    if not payment:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    
    # Verificar se é do revendedor atual
    if payment["reseller_id"] != current_user.get("reseller_id"):
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    return payment

@router.get("/bonus/balance")
async def get_bonus_balance(
    current_user: dict = Depends(get_current_user)
):
    """Obter saldo de bônus do revendedor"""
    if current_user["user_type"] != "reseller":
        raise HTTPException(status_code=403, detail="Apenas revendedores")
    
    bonus_service = BonusService(db)
    balance = await bonus_service.get_bonus_balance(current_user.get("reseller_id"))
    
    return {"bonus_balance": balance}

@router.get("/bonus/history")
async def get_bonus_history(
    current_user: dict = Depends(get_current_user)
):
    """Obter histórico de transações de bônus"""
    if current_user["user_type"] != "reseller":
        raise HTTPException(status_code=403, detail="Apenas revendedores")
    
    bonus_service = BonusService(db)
    history = await bonus_service.get_bonus_history(current_user.get("reseller_id"))
    
    return {"transactions": history}
