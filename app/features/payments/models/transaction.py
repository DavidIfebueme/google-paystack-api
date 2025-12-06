from sqlalchemy import String, Integer, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import uuid
import enum
from app.platform.db.base import Base

class TransactionStatus(enum.Enum):
    pending = "pending"
    success = "success"
    failed = "failed"

class Transaction(Base):
    __tablename__ = "transactions"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    reference: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(SQLEnum(TransactionStatus), default=TransactionStatus.pending, nullable=False)
    authorization_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    user: Mapped["User"] = relationship("User", backref="transactions")
    
    __table_args__ = (
        Index("idx_transaction_reference", "reference"),
        Index("idx_transaction_status", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, reference={self.reference}, status={self.status.value}, amount={self.amount})>"