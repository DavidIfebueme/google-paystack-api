import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.payments.models.transaction import Transaction, TransactionStatus, TransactionType


class WalletTransactionService:

    @staticmethod
    async def create_deposit_transaction(
        db: AsyncSession,
        user_id: uuid.UUID,
        reference: str,
        amount: int,
        authorization_url: str,
        email: str
    ) -> Transaction:
        existing = await WalletTransactionService.get_transaction_by_reference(db, reference)
        if existing:
            return existing

        transaction = Transaction(
            reference=reference,
            user_id=user_id,
            amount=amount,
            email=email,
            status=TransactionStatus.pending,
            transaction_type=TransactionType.deposit,
            authorization_url=authorization_url
        )

        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        return transaction

    @staticmethod
    async def create_transfer_transaction(
        db: AsyncSession,
        user_id: uuid.UUID,
        sender_wallet_id: uuid.UUID,
        recipient_wallet_id: uuid.UUID,
        amount: int,
        reference: str
    ) -> Transaction:
        existing = await WalletTransactionService.get_transaction_by_reference(db, reference)
        if existing:
            raise ValueError("Transfer already processed")

        transaction = Transaction(
            reference=reference,
            user_id=user_id,
            amount=amount,
            status=TransactionStatus.success,
            transaction_type=TransactionType.transfer,
            sender_wallet_id=sender_wallet_id,
            recipient_wallet_id=recipient_wallet_id
        )

        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        return transaction

    @staticmethod
    async def get_user_transactions(db: AsyncSession, user_id: uuid.UUID) -> list[Transaction]:
        result = await db.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_transaction_by_reference(db: AsyncSession, reference: str) -> Transaction | None:
        result = await db.execute(
            select(Transaction).where(Transaction.reference == reference)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_transaction_status_from_paystack(db: AsyncSession, reference: str, paystack_status: dict):
        transaction = await WalletTransactionService.get_transaction_by_reference(db, reference)
        if transaction:
            status_str = paystack_status.get("status", "").lower()
            if status_str == "success":
                transaction.status = TransactionStatus.success
            elif status_str == "failed":
                transaction.status = TransactionStatus.failed
            elif status_str == "abandoned":
                transaction.status = TransactionStatus.failed
            else:
                transaction.status = TransactionStatus.pending
            await db.commit()
            await db.refresh(transaction)
        return transaction
