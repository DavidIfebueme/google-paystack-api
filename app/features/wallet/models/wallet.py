import secrets
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import UUID, BigInteger, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.platform.db.base import Base

if TYPE_CHECKING:
    from app.features.auth.models.user import User

class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    wallet_number: Mapped[str] = mapped_column(String(13), unique=True, index=True, nullable=False)
    balance: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="wallet")

    __table_args__ = (
        Index("idx_wallet_number", "wallet_number"),
        Index("idx_wallet_user_id", "user_id"),
    )

    @staticmethod
    def generate_wallet_number() -> str:
        return ''.join([str(secrets.randbelow(10)) for _ in range(13)])

    def __repr__(self) -> str:
        return f"<Wallet(id={self.id}, wallet_number={self.wallet_number}, balance={self.balance})>"
