import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.wallet.models.wallet import Wallet


class WalletService:

    @staticmethod
    async def create_wallet(db: AsyncSession, user_id: uuid.UUID) -> Wallet:
        wallet_number = Wallet.generate_wallet_number()

        existing = await db.execute(
            select(Wallet).where(Wallet.wallet_number == wallet_number)
        )
        while existing.scalar_one_or_none() is not None:
            wallet_number = Wallet.generate_wallet_number()
            existing = await db.execute(
                select(Wallet).where(Wallet.wallet_number == wallet_number)
            )

        wallet = Wallet(
            user_id=user_id,
            wallet_number=wallet_number,
            balance=0
        )

        db.add(wallet)
        await db.commit()
        await db.refresh(wallet)
        return wallet

    @staticmethod
    async def get_wallet_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> Wallet | None:
        result = await db.execute(
            select(Wallet).where(Wallet.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_wallet_by_number(db: AsyncSession, wallet_number: str) -> Wallet | None:
        if len(wallet_number) != 13 or not wallet_number.isdigit():
            raise ValueError("Wallet number must be exactly 13 digits")

        result = await db.execute(
            select(Wallet).where(Wallet.wallet_number == wallet_number)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def credit_wallet(db: AsyncSession, wallet_id: uuid.UUID, amount: int) -> Wallet:
        if amount <= 0:
            raise ValueError("Amount must be greater than 0")

        result = await db.execute(
            select(Wallet).where(Wallet.id == wallet_id).with_for_update()
        )
        wallet = result.scalar_one_or_none()

        if not wallet:
            raise ValueError("Wallet not found")

        wallet.balance += amount
        await db.commit()
        await db.refresh(wallet)
        return wallet

    @staticmethod
    async def debit_wallet(db: AsyncSession, wallet_id: uuid.UUID, amount: int) -> Wallet:
        if amount <= 0:
            raise ValueError("Amount must be greater than 0")

        result = await db.execute(
            select(Wallet).where(Wallet.id == wallet_id).with_for_update()
        )
        wallet = result.scalar_one_or_none()

        if not wallet:
            raise ValueError("Wallet not found")

        if wallet.balance < amount:
            raise ValueError("Insufficient balance")

        wallet.balance -= amount
        await db.commit()
        await db.refresh(wallet)
        return wallet

    @staticmethod
    async def transfer_funds(
        db: AsyncSession,
        sender_wallet_id: uuid.UUID,
        recipient_wallet_id: uuid.UUID,
        amount: int
    ) -> tuple[Wallet, Wallet]:
        if amount <= 0:
            raise ValueError("Amount must be greater than 0")

        if sender_wallet_id == recipient_wallet_id:
            raise ValueError("Cannot transfer to same wallet")

        sender_result = await db.execute(
            select(Wallet).where(Wallet.id == sender_wallet_id).with_for_update()
        )
        sender_wallet = sender_result.scalar_one_or_none()

        if not sender_wallet:
            raise ValueError("Sender wallet not found")

        if sender_wallet.balance < amount:
            raise ValueError("Insufficient balance")

        recipient_result = await db.execute(
            select(Wallet).where(Wallet.id == recipient_wallet_id).with_for_update()
        )
        recipient_wallet = recipient_result.scalar_one_or_none()

        if not recipient_wallet:
            raise ValueError("Recipient wallet not found")

        sender_wallet.balance -= amount
        recipient_wallet.balance += amount

        await db.commit()
        await db.refresh(sender_wallet)
        await db.refresh(recipient_wallet)

        return (sender_wallet, recipient_wallet)
