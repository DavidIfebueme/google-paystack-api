from typing import Optional
from sqlalchemy import UUID, DateTime, String, Integer, ForeignKey, Index, Enum as SQLEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import uuid
import enum
from app.features.auth.models.user import User
from app.platform.db.base import Base

class TransactionStatus(enum.Enum):
    pending = "pending"
    success = "success"
    failed = "failed"

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reference: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[TransactionStatus] = mapped_column(SQLEnum(TransactionStatus), default=TransactionStatus.pending, nullable=False)
    authorization_url: Mapped[str] = mapped_column(Text, nullable=False)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    user: Mapped["User"] = relationship("User", backref="transactions")
    
    __table_args__ = (
        Index("idx_transaction_reference", "reference"),
        Index("idx_transaction_status", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, reference={self.reference}, status={self.status.value}, amount={self.amount})>"