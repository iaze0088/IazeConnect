"""
Serviço de Gerenciamento de Bônus/Comissões
Sistema de cashback de 10% para revendas pai
"""
from datetime import datetime, timezone
import uuid
from typing import Optional

BONUS_PERCENTAGE = 0.10  # 10% de bônus

class BonusService:
    """Gerenciamento de bônus e comissões"""
    
    def __init__(self, db):
        self.db = db
    
    async def credit_bonus_to_parent(
        self,
        payment_amount: float,
        sub_reseller_id: str,
        payment_id: str
    ) -> Optional[dict]:
        """
        Creditar 10% de bônus para a revenda pai quando sub-revenda paga
        
        Args:
            payment_amount: Valor total pago pela sub-revenda
            sub_reseller_id: ID da sub-revenda que pagou
            payment_id: ID do pagamento
        
        Returns:
            Transação de bônus ou None se não houver revenda pai
        """
        # Buscar assinatura da sub-revenda para encontrar o pai
        sub_subscription = await self.db.subscriptions.find_one(
            {"reseller_id": sub_reseller_id},
            {"_id": 0}
        )
        
        if not sub_subscription or not sub_subscription.get("parent_reseller_id"):
            print(f"⚠️ Sub-revenda {sub_reseller_id} não tem revenda pai")
            return None
        
        parent_reseller_id = sub_subscription["parent_reseller_id"]
        
        # Calcular bônus (10%)
        bonus_amount = round(payment_amount * BONUS_PERCENTAGE, 2)
        
        # Criar transação de bônus
        bonus_transaction = {
            "id": str(uuid.uuid4()),
            "reseller_id": parent_reseller_id,
            "amount": bonus_amount,
            "transaction_type": "credit",
            "source_payment_id": payment_id,
            "source_reseller_id": sub_reseller_id,
            "description": f"Bônus de 10% - Renovação de sub-revenda",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.bonus_transactions.insert_one(bonus_transaction)
        
        # Atualizar saldo de bônus da revenda pai
        await self.db.subscriptions.update_one(
            {"reseller_id": parent_reseller_id},
            {
                "$inc": {"bonus_balance": bonus_amount},
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
            }
        )
        
        # Buscar nome da sub-revenda para notificação
        sub_reseller = await self.db.resellers.find_one(
            {"id": sub_reseller_id},
            {"_id": 0, "subdomain": 1}
        )
        sub_name = sub_reseller.get("subdomain", "Sub-revenda") if sub_reseller else "Sub-revenda"
        
        # Criar notificação para revenda pai
        await self.create_bonus_notification(
            parent_reseller_id,
            bonus_amount,
            sub_name,
            payment_amount
        )
        
        print(f"✅ Bônus creditado: R$ {bonus_amount:.2f} para revenda {parent_reseller_id}")
        return bonus_transaction
    
    async def use_bonus_on_payment(
        self,
        reseller_id: str,
        bonus_to_use: float,
        payment_id: str
    ) -> dict:
        """
        Usar bônus acumulado como desconto no pagamento
        
        Args:
            reseller_id: ID da revenda
            bonus_to_use: Valor de bônus a usar
            payment_id: ID do pagamento
        
        Returns:
            Transação de débito de bônus
        """
        # Verificar saldo disponível
        subscription = await self.db.subscriptions.find_one(
            {"reseller_id": reseller_id},
            {"_id": 0}
        )
        
        if not subscription:
            raise Exception("Assinatura não encontrada")
        
        current_balance = subscription.get("bonus_balance", 0.0)
        
        if bonus_to_use > current_balance:
            raise Exception(f"Saldo insuficiente. Disponível: R$ {current_balance:.2f}")
        
        # Criar transação de débito
        bonus_transaction = {
            "id": str(uuid.uuid4()),
            "reseller_id": reseller_id,
            "amount": bonus_to_use,
            "transaction_type": "debit",
            "source_payment_id": payment_id,
            "source_reseller_id": None,
            "description": f"Desconto aplicado na renovação",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.bonus_transactions.insert_one(bonus_transaction)
        
        # Deduzir do saldo
        await self.db.subscriptions.update_one(
            {"reseller_id": reseller_id},
            {
                "$inc": {"bonus_balance": -bonus_to_use},
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
            }
        )
        
        print(f"✅ Bônus usado: R$ {bonus_to_use:.2f} por revenda {reseller_id}")
        return bonus_transaction
    
    async def get_bonus_balance(self, reseller_id: str) -> float:
        """Obter saldo atual de bônus"""
        subscription = await self.db.subscriptions.find_one(
            {"reseller_id": reseller_id},
            {"_id": 0, "bonus_balance": 1}
        )
        
        if not subscription:
            return 0.0
        
        return subscription.get("bonus_balance", 0.0)
    
    async def get_bonus_history(self, reseller_id: str, limit: int = 50) -> list:
        """Obter histórico de transações de bônus"""
        transactions = await self.db.bonus_transactions.find(
            {"reseller_id": reseller_id},
            {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(length=limit)
        
        return transactions
    
    async def get_sub_resellers_count(self, reseller_id: str) -> int:
        """Contar quantas sub-revendas foram criadas"""
        count = await self.db.subscriptions.count_documents({
            "parent_reseller_id": reseller_id
        })
        return count
    
    async def get_sub_resellers_active_count(self, reseller_id: str) -> int:
        """Contar quantas sub-revendas estão ativas"""
        count = await self.db.subscriptions.count_documents({
            "parent_reseller_id": reseller_id,
            "status": {"$in": ["trial", "active"]}
        })
        return count
    
    async def create_bonus_notification(
        self,
        reseller_id: str,
        bonus_amount: float,
        sub_reseller_name: str,
        payment_amount: float
    ):
        """Criar notificação de bônus recebido"""
        notification = {
            "id": str(uuid.uuid4()),
            "reseller_id": reseller_id,
            "type": "bonus_received",
            "title": "🎉 Você ganhou bônus!",
            "message": f"Sua sub-revenda '{sub_reseller_name}' renovou a assinatura (R$ {payment_amount:.2f}). Você ganhou R$ {bonus_amount:.2f} de bônus!",
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.notifications.insert_one(notification)
        print(f"📬 Notificação de bônus criada para revenda {reseller_id}")
