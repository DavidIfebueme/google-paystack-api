import secrets
import string
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.features.api_keys.models.api_key import APIKey, APIKeyPermission

class APIKeyService:
    
    @staticmethod
    def generate_api_key() -> str:
        random_part = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        return f"sk_live_{random_part}"
    
    @staticmethod
    def parse_expiry(expiry_str: str) -> datetime:
        now = datetime.utcnow()
        
        if expiry_str == '1H':
            return now + timedelta(hours=1)
        elif expiry_str == '1D':
            return now + timedelta(days=1)
        elif expiry_str == '1M':
            return now + timedelta(days=30)
        elif expiry_str == '1Y':
            return now + timedelta(days=365)
        else:
            raise ValueError(f"Invalid expiry format: {expiry_str}")
    
    @staticmethod
    async def count_active_keys(db: AsyncSession, user_id: uuid.UUID) -> int:
        now = datetime.utcnow()
        result = await db.execute(
            select(APIKey).where(
                and_(
                    APIKey.user_id == user_id,
                    APIKey.is_active == True,
                    APIKey.expires_at > now
                )
            )
        )
        keys = result.scalars().all()
        return len(keys)
    
    @staticmethod
    async def create_api_key(
        db: AsyncSession,
        user_id: uuid.UUID,
        name: str,
        permissions: list[str],
        expires_at: datetime
    ) -> APIKey:
        active_count = await APIKeyService.count_active_keys(db, user_id)
        if active_count >= 5:
            raise ValueError("Maximum of 5 active API keys allowed")
        
        api_key = APIKey(
            user_id=user_id,
            key=APIKeyService.generate_api_key(),
            name=name,
            permissions=permissions,
            expires_at=expires_at,
            is_active=True
        )
        
        db.add(api_key)
        await db.commit()
        await db.refresh(api_key)
        return api_key
    
    @staticmethod
    async def get_api_key_by_key(db: AsyncSession, key: str) -> APIKey | None:
        result = await db.execute(
            select(APIKey).where(APIKey.key == key)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    def validate_api_key(api_key: APIKey, required_permission: str) -> bool:
        if not api_key.is_active:
            return False
        
        if datetime.utcnow() > api_key.expires_at:
            return False
        
        if required_permission not in api_key.permissions:
            return False
        
        return True
    
    @staticmethod
    async def rollover_api_key(
        db: AsyncSession,
        user_id: uuid.UUID,
        expired_key_id: str,
        new_expiry: str
    ) -> APIKey:
        result = await db.execute(
            select(APIKey).where(
                and_(
                    APIKey.id == expired_key_id,
                    APIKey.user_id == user_id
                )
            )
        )
        expired_key = result.scalar_one_or_none()
        
        if not expired_key:
            raise ValueError("API key not found")
        
        if datetime.utcnow() < expired_key.expires_at:
            raise ValueError("Cannot rollover a key that is not expired")
        
        expires_at = APIKeyService.parse_expiry(new_expiry)
        
        new_key = await APIKeyService.create_api_key(
            db=db,
            user_id=user_id,
            name=expired_key.name,
            permissions=expired_key.permissions,
            expires_at=expires_at
        )
        
        return new_key