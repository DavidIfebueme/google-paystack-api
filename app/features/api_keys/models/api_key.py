from typing import TYPE_CHECKING
from sqlalchemy import UUID, DateTime, String, Boolean, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import uuid
from app.platform.db.base import Base
import enum

if TYPE_CHECKING:
    from app.features.auth.models.user import User

class APIKeyPermission(enum.Enum):
    deposit = "deposit"
    transfer = "transfer"
    read = "read"

class APIKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    permissions: Mapped[list] = mapped_column(JSON, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    user: Mapped["User"] = relationship("User", back_populates="api_keys")
    
    __table_args__ = (
        Index("idx_api_key_key", "key"),
        Index("idx_api_key_user_active", "user_id", "is_active"),
    )
    
    def __repr__(self) -> str:
        return f"<APIKey(id={self.id}, name={self.name}, user_id={self.user_id})>"