"""
Serviço de Gerenciamento de Assinaturas
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid

# Planos disponíveis
SUBSCRIPTION_PLANS = {
    "basico": {
        "name": "Básico",
        "price": 49.00,
        "whatsapp_limit": 1,
        "ai_agents_limit": 2,
        "departments_limit": 2,
        "features": [
            "1 número WhatsApp",
            "2 Agentes de IA",
            "2 Departamentos",
            "Suporte básico"
        ]
    },
    "plus": {
        "name": "Plus",
        "price": 89.00,
        "whatsapp_limit": 2,
        "ai_agents_limit": 4,
        "departments_limit": 4,
        "features": [
            "2 números WhatsApp",
            "4 Agentes de IA",
            "4 Departamentos",
            "Suporte prioritário"
        ]
    },
    "pro": {
        "name": "Pro",
        "price": 129.00,
        "whatsapp_limit": 3,
        "ai_agents_limit": 6,
        "departments_limit": 6,
        "features": [
            "3 números WhatsApp",
            "6 Agentes de IA",
            "6 Departamentos",
            "Suporte prioritário",
            "Relatórios avançados"
        ]
    },
    "premium": {
        "name": "Premium",
        "price": 199.00,
        "whatsapp_limit": 5,
        "ai_agents_limit": 8,
        "departments_limit": 8,
        "features": [
            "5 números WhatsApp",
            "8 Agentes de IA",
            "8 Departamentos",
            "Suporte VIP",
            "Relatórios avançados",
            "API dedicada"
        ]
    },
    "enterprise": {
        "name": "Enterprise",
        "price": 499.00,
        "whatsapp_limit": -1,  # Ilimitado
        "ai_agents_limit": -1,  # Ilimitado
        "departments_limit": -1,  # Ilimitado
        "features": [
            "WhatsApp ilimitado",
            "Agentes de IA ilimitados",
            "Departamentos ilimitados",
            "Suporte VIP 24/7",
            "Todas as features",
            "API dedicada",
            "Gerente de conta"
        ]
    }
}

class SubscriptionService:
    """Gerenciamento de assinaturas de revendedores"""
    
    def __init__(self, db):
        self.db = db
    
    async def create_trial_subscription(self, reseller_id: str, parent_reseller_id: Optional[str] = None) -> dict:
        """
        Criar assinatura trial de 5 dias ao criar revendedor
        
        Args:
            reseller_id: ID do revendedor
            parent_reseller_id: ID da revenda pai (se foi criada por outra revenda)
        """
        now = datetime.now(timezone.utc)
        trial_ends = now + timedelta(days=5)
        
        subscription = {
            "id": str(uuid.uuid4()),
            "reseller_id": reseller_id,
            "parent_reseller_id": parent_reseller_id,  # Armazena quem criou esta revenda
            "plan_type": "basico",  # Trial começa no plano básico
            "status": "trial",
            "trial_ends_at": trial_ends.isoformat(),
            "current_period_start": now.isoformat(),
            "current_period_end": trial_ends.isoformat(),
            "last_payment_date": None,
            "bonus_balance": 0.0,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
        await self.db.subscriptions.insert_one(subscription)
        print(f"✅ Trial subscription created for reseller: {reseller_id} (parent: {parent_reseller_id})")
        return subscription
    
    async def get_subscription(self, reseller_id: str) -> Optional[dict]:
        """Buscar assinatura do revendedor"""
        return await self.db.subscriptions.find_one(
            {"reseller_id": reseller_id},
            {"_id": 0}
        )
    
    async def is_subscription_active(self, reseller_id: str) -> bool:
        """Verificar se assinatura está ativa"""
        subscription = await self.get_subscription(reseller_id)
        
        if not subscription:
            return False
        
        status = subscription.get("status")
        
        # Se está em trial ou active, verificar data
        if status in ["trial", "active"]:
            # ⚡ FIX: Verificar se campo existe antes de usar
            period_end = subscription.get("current_period_end") or subscription.get("end_date")
            
            if not period_end:
                # Se não tem data, considerar ativo (evitar quebrar)
                return True
            
            end_date = datetime.fromisoformat(period_end)
            now = datetime.now(timezone.utc)
            
            if now <= end_date:
                return True
            else:
                # Expirou, atualizar status
                await self.expire_subscription(reseller_id)
                return False
        
        return False
    
    async def expire_subscription(self, reseller_id: str):
        """Marcar assinatura como expirada"""
        await self.db.subscriptions.update_one(
            {"reseller_id": reseller_id},
            {
                "$set": {
                    "status": "expired",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        print(f"⚠️ Subscription expired for reseller: {reseller_id}")
    
    async def renew_subscription(self, reseller_id: str, plan_type: str, payment_id: str):
        """
        Renovar assinatura após pagamento confirmado (30 dias)
        """
        now = datetime.now(timezone.utc)
        period_end = now + timedelta(days=30)
        
        subscription = await self.get_subscription(reseller_id)
        
        if subscription:
            # Atualizar assinatura existente
            await self.db.subscriptions.update_one(
                {"reseller_id": reseller_id},
                {
                    "$set": {
                        "plan_type": plan_type,
                        "status": "active",
                        "current_period_start": now.isoformat(),
                        "current_period_end": period_end.isoformat(),
                        "last_payment_date": now.isoformat(),
                        "updated_at": now.isoformat()
                    }
                }
            )
        else:
            # Criar nova assinatura
            subscription = {
                "id": str(uuid.uuid4()),
                "reseller_id": reseller_id,
                "plan_type": plan_type,
                "status": "active",
                "trial_ends_at": now.isoformat(),
                "current_period_start": now.isoformat(),
                "current_period_end": period_end.isoformat(),
                "last_payment_date": now.isoformat(),
                "created_at": now.isoformat(),
                "updated_at": now.isoformat()
            }
            await self.db.subscriptions.insert_one(subscription)
        
        # Registrar pagamento
        await self.db.payments.insert_one({
            "id": str(uuid.uuid4()),
            "reseller_id": reseller_id,
            "payment_id": payment_id,
            "plan_type": plan_type,
            "amount": SUBSCRIPTION_PLANS[plan_type]["price"],
            "status": "approved",
            "created_at": now.isoformat()
        })
        
        print(f"✅ Subscription renewed for reseller: {reseller_id} - Plan: {plan_type}")
        return subscription
    
    async def get_days_until_expiration(self, reseller_id: str) -> Optional[int]:
        """Calcular quantos dias faltam para expirar"""
        subscription = await self.get_subscription(reseller_id)
        
        if not subscription:
            return None
        
        end_date = datetime.fromisoformat(subscription["current_period_end"])
        now = datetime.now(timezone.utc)
        delta = end_date - now
        
        return max(0, delta.days)
    
    async def should_show_expiration_warning(self, reseller_id: str) -> bool:
        """
        Verificar se deve mostrar popup de aviso (2x ao dia)
        Mostra se faltam 5 dias ou menos
        """
        days_left = await self.get_days_until_expiration(reseller_id)
        
        if days_left is None:
            return False
        
        # Mostrar aviso se faltam 5 dias ou menos
        return days_left <= 5
    
    async def manual_renew_subscription(self, reseller_id: str, plan_type: str, months: int):
        """
        Renovação manual pelo admin (pode ser 1, 3, 6, 12 meses)
        """
        if plan_type not in SUBSCRIPTION_PLANS:
            raise ValueError(f"Plano inválido: {plan_type}")
        
        now = datetime.now(timezone.utc)
        days_to_add = months * 30  # Aproximadamente 30 dias por mês
        
        subscription = await self.get_subscription(reseller_id)
        
        if subscription:
            # Se já tem assinatura, adicionar tempo ao período atual
            current_end = datetime.fromisoformat(subscription["current_period_end"])
            
            # Se já expirou, começa de agora, senão adiciona no final
            if current_end < now:
                new_end = now + timedelta(days=days_to_add)
            else:
                new_end = current_end + timedelta(days=days_to_add)
            
            await self.db.subscriptions.update_one(
                {"reseller_id": reseller_id},
                {
                    "$set": {
                        "plan_type": plan_type,
                        "status": "active",
                        "current_period_end": new_end.isoformat(),
                        "last_payment_date": now.isoformat(),
                        "updated_at": now.isoformat()
                    }
                }
            )
        else:
            # Criar nova assinatura
            period_end = now + timedelta(days=days_to_add)
            subscription = {
                "id": str(uuid.uuid4()),
                "reseller_id": reseller_id,
                "plan_type": plan_type,
                "status": "active",
                "trial_ends_at": now.isoformat(),
                "current_period_start": now.isoformat(),
                "current_period_end": period_end.isoformat(),
                "last_payment_date": now.isoformat(),
                "created_at": now.isoformat(),
                "updated_at": now.isoformat()
            }
            await self.db.subscriptions.insert_one(subscription)
        
        print(f"✅ Manual renewal for reseller: {reseller_id} - Plan: {plan_type} - Months: {months}")
        return await self.get_subscription(reseller_id)
    
    async def update_subscription_end_date(self, reseller_id: str, new_end_date: str):
        """
        Atualizar manualmente a data de vencimento (para correções do admin)
        """
        subscription = await self.get_subscription(reseller_id)
        
        if not subscription:
            raise ValueError("Assinatura não encontrada")
        
        # Validar formato da data
        try:
            datetime.fromisoformat(new_end_date)
        except ValueError:
            raise ValueError("Data inválida. Use formato ISO: YYYY-MM-DDTHH:MM:SS")
        
        await self.db.subscriptions.update_one(
            {"reseller_id": reseller_id},
            {
                "$set": {
                    "current_period_end": new_end_date,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        print(f"✅ Subscription end date updated for reseller: {reseller_id} - New end: {new_end_date}")
        return await self.get_subscription(reseller_id)
    
    async def list_all_subscriptions(self):
        """
        Listar todas as assinaturas (para admin)
        """
        subscriptions = await self.db.subscriptions.find({}, {"_id": 0}).to_list(None)
        return subscriptions
