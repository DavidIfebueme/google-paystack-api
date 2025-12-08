from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional
from datetime import datetime, timedelta

from app.features.payments.models.transaction import Transaction, TransactionStatus

class TransactionService:
    @staticmethod
    async def create_transaction(
        db: AsyncSession,
        reference: str,
        amount: int,
        authorization_url: str,
        email: str,
        user_id: Optional[str] = None
    ) -> Transaction:
        transaction = Transaction(
            reference=reference,
            amount=amount,
            email=email,
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
    async def find_recent_transaction(
        db: AsyncSession,
        email: str,
        amount: int,
        minutes: int = 1
    ) -> Optional[Transaction]:
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        result = await db.execute(
            select(Transaction)
            .where(
                and_(
                    Transaction.email == email,
                    Transaction.amount == amount,
                    Transaction.created_at >= cutoff_time,
                    Transaction.status.in_([TransactionStatus.pending, TransactionStatus.success])
                )
            )
            .order_by(Transaction.created_at.desc())
            .limit(1)
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