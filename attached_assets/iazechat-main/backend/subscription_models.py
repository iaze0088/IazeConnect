"""
Modelos para Sistema de Assinaturas e Pagamentos
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Literal
from datetime import datetime

# Tipos de planos disponíveis
PlanType = Literal["basico", "plus", "pro", "premium", "enterprise"]

class SubscriptionPlan(BaseModel):
    """Plano de assinatura"""
    plan_type: PlanType
    name: str
    price: float
    whatsapp_limit: int  # -1 para ilimitado
    features: list[str]

class ResellerSubscription(BaseModel):
    """Assinatura do revendedor"""
    id: str
    reseller_id: str
    parent_reseller_id: Optional[str] = None  # ID da revenda pai (se foi criada por outra revenda)
    plan_type: PlanType
    status: Literal["trial", "active", "expired", "cancelled"]
    trial_ends_at: str  # ISO format
    current_period_start: str
    current_period_end: str
    last_payment_date: Optional[str] = None
    bonus_balance: float = 0.0  # Saldo de bônus acumulado em R$
    created_at: str
    updated_at: str

class BonusTransaction(BaseModel):
    """Transação de bônus (crédito ou uso)"""
    id: str
    reseller_id: str  # Quem recebeu/usou o bônus
    amount: float
    transaction_type: Literal["credit", "debit"]  # credit=ganhou, debit=usou
    source_payment_id: Optional[str] = None  # ID do pagamento que gerou o bônus
    source_reseller_id: Optional[str] = None  # ID da sub-revenda que pagou
    description: str
    created_at: str

class CreatePaymentRequest(BaseModel):
    """Request para criar pagamento PIX"""
    plan_type: PlanType
    reseller_id: str
    customer_name: str
    customer_email: EmailStr

class PaymentResponse(BaseModel):
    """Response com dados do pagamento PIX"""
    payment_id: str
    qr_code: str
    qr_code_base64: str
    copy_paste_code: str
    amount: float
    plan_type: PlanType
    expires_at: Optional[str] = None
    status: str = "pending"

class MercadoPagoConfig(BaseModel):
    """Configuração do Mercado Pago (Admin)"""
    access_token: str
    public_key: str
    webhook_secret: str
    enabled: bool = True
