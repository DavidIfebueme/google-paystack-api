
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.api_keys.services.api_key_service import APIKeyService
from app.features.auth.models.user import User
from app.platform.auth.jwt_service import JWTService
from app.platform.db import get_db

security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials"
        )

    token = credentials.credentials

    try:
        payload = JWTService.decode_access_token(token)
        user_id: str = payload.get("user_id")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        ) from None

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user

async def get_current_user_or_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    x_api_key: str | None = Header(None),
    db: AsyncSession = Depends(get_db)
) -> tuple[User, str]:
    if x_api_key:
        api_key = await APIKeyService.get_api_key_by_key(db, x_api_key)

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )

        if not api_key.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key is inactive"
            )

        from datetime import datetime
        if datetime.utcnow() > api_key.expires_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has expired"
            )

        result = await db.execute(select(User).where(User.id == api_key.user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        return (user, "api_key")

    if credentials:
        user = await get_current_user(credentials, db)
        return (user, "jwt")

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing authentication credentials"
    )

def require_permission(permission: str):
    async def permission_checker(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        x_api_key: str | None = Header(None),
        db: AsyncSession = Depends(get_db)
    ) -> tuple[User, str]:
        user, auth_type = await get_current_user_or_api_key(credentials, x_api_key, db)

        if auth_type == "api_key":
            api_key = await APIKeyService.get_api_key_by_key(db, x_api_key)

            if not APIKeyService.validate_api_key(api_key, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"API key does not have '{permission}' permission"
                )

        return (user, auth_type)

    return permission_checker
