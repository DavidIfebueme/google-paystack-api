import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import UUID, BigInteger, DateTime, ForeignKey, Index, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.platform.db.base import Base

if TYPE_CHECKING:
    from app.features.auth.models.user import User
    from app.features.wallet.models.wallet import Wallet

class TransactionStatus(enum.Enum):
    pending = "pending"
    success = "success"
    failed = "failed"

class TransactionType(enum.Enum):
    deposit = "deposit"
    transfer = "transfer"

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reference: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[TransactionStatus] = mapped_column(SQLEnum(TransactionStatus), default=TransactionStatus.pending, nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(SQLEnum(TransactionType), nullable=False)
    authorization_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    sender_wallet_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=True)
    recipient_wallet_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="transactions")
    sender_wallet: Mapped[Optional["Wallet"]] = relationship("Wallet", foreign_keys=[sender_wallet_id], backref="sent_transactions")
    recipient_wallet: Mapped[Optional["Wallet"]] = relationship("Wallet", foreign_keys=[recipient_wallet_id], backref="received_transactions")

    __table_args__ = (
        Index("idx_transaction_reference", "reference"),
        Index("idx_transaction_status", "status"),
        Index("idx_transaction_user_id", "user_id"),
        Index("idx_transaction_type", "transaction_type"),
    )

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, reference={self.reference}, type={self.transaction_type.value}, status={self.status.value}, amount={self.amount})>"
