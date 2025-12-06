from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime

from app.features.payments.models.transaction import Transaction, TransactionStatus

class TransactionService:
    @staticmethod
    async def create_transaction(
        db: AsyncSession,
        reference: str,
        amount: int,
        authorization_url: str,
        user_id: Optional[str] = None
    ) -> Transaction:
        transaction = Transaction(
            reference=reference,
            amount=amount,
            authorization_url=authorization_url,
            user_id=user_id,
            status=TransactionStatus.pending
        )
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        return transaction
    
    @staticmethod
    async def get_transaction_by_reference(db: AsyncSession, reference: str) -> Optional[Transaction]:
        result = await db.execute(
            select(Transaction).where(Transaction.reference == reference)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_transaction_status(
        db: AsyncSession,
        reference: str,
        status: TransactionStatus,
        paid_at: Optional[datetime] = None
    ) -> Optional[Transaction]:
        transaction = await TransactionService.get_transaction_by_reference(db, reference)
        if transaction:
            transaction.status = status
            if paid_at:
                transaction.paid_at = paid_at
            await db.commit()
            await db.refresh(transaction)
        return transaction
    
    @staticmethod
    async def check_duplicate_transaction(db: AsyncSession, reference: str) -> bool:
        transaction = await TransactionService.get_transaction_by_reference(db, reference)
        return transaction is not None