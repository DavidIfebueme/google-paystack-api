from urllib.parse import urlencode

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.models.user import User
from app.features.auth.schemas.auth import GoogleUserInfo
from app.features.wallet.services.wallet_service import WalletService
from app.platform.config.settings import settings


class AuthService:

    @staticmethod
    def get_google_auth_url() -> str:
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent"
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    @staticmethod
    async def exchange_code_for_token(code: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code"
                }
            )

            if response.status_code != 200:
                raise Exception(f"Failed to exchange code for token: {response.text}")

            data = response.json()
            return data["access_token"]

    @staticmethod
    async def get_google_user_info(access_token: str) -> GoogleUserInfo:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v1/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if response.status_code != 200:
                raise Exception(f"Failed to get user info: {response.text}")

            data = response.json()
            return GoogleUserInfo(**data)

    @staticmethod
    async def get_or_create_user(db: AsyncSession, user_info: GoogleUserInfo) -> User:
        result = await db.execute(
            select(User).where(User.google_id == user_info.sub)
        )
        user = result.scalar_one_or_none()

        if user:
            user.email = user_info.email
            user.name = user_info.name
            user.picture = user_info.picture
            await db.commit()
            await db.refresh(user)
            return user

        user = User(
            email=user_info.email,
            name=user_info.name,
            google_id=user_info.sub,
            picture=user_info.picture
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        await WalletService.create_wallet(db, user.id)

        return user

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
