from sqlalchemy import select
from typing import Optional
import httpx
from urllib.parse import urlencode
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.auth.models.user import User
from app.features.auth.schemas.auth import GoogleUserInfo
from app.platform.config.settings import get_settings

settings = get_settings()

class AuthService:
    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
    
    @staticmethod
    def get_google_auth_url(state: str = "random_state") -> str:
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "state": state,
        }
        return f"{AuthService.GOOGLE_AUTH_URL}?{urlencode(params)}"
    
    @staticmethod
    async def exchange_code_for_token(code: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                AuthService.GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                }
            )
            response.raise_for_status()
            return response.json()["access_token"]
    
    @staticmethod
    async def get_google_user_info(access_token: str) -> GoogleUserInfo:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                AuthService.GOOGLE_USER_INFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return GoogleUserInfo(**response.json())
    
    @staticmethod
    async def get_or_create_user(db: AsyncSession, user_info: GoogleUserInfo) -> User:
        result = await db.execute(
            select(User).where(User.google_id == user_info.sub)
        )
        user = result.scalar_one_or_none()
        
        if user:
            user.name = user_info.name
            user.picture = user_info.picture
            await db.commit()
            await db.refresh(user)
            return user
        
        new_user = User(
            email=user_info.email,
            name=user_info.name,
            google_id=user_info.sub,
            picture=user_info.picture
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()