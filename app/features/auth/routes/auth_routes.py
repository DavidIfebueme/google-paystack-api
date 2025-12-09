from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.schemas import GoogleAuthURLResponse
from app.features.auth.services.auth_service import AuthService
from app.platform.auth.jwt_service import JWTService
from app.platform.db import get_db
from app.platform.response.schemas import error_response, success_response

router = APIRouter()

@router.get("/google/login", response_model=GoogleAuthURLResponse)
async def google_login():
    auth_url = AuthService.get_google_auth_url()
    return GoogleAuthURLResponse(google_auth_url=auth_url)

@router.get("/google/callback")
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    try:
        access_token = await AuthService.exchange_code_for_token(code)
        user_info = await AuthService.get_google_user_info(access_token)
        user = await AuthService.get_or_create_user(db, user_info)

        jwt_token = JWTService.create_access_token(
            data={"user_id": str(user.id), "email": user.email}
        )

        user_data = {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
            "created_at": user.created_at.isoformat()
        }

        token_data = {
            "access_token": jwt_token,
            "token_type": "bearer",
            "user": user_data
        }

        return success_response(
            message="Login successful",
            data=token_data,
            status_code=200
        )
    except HTTPException as e:
        return error_response(message=str(e.detail), status_code=e.status_code)
    except Exception as e:
        return error_response(message=f"Authentication failed: {str(e)}", status_code=500)

@router.get("/user/{user_id}")
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    try:
        user = await AuthService.get_user_by_id(db, user_id)
        if not user:
            return error_response(message="User not found", status_code=404)

        user_data = {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
            "created_at": user.created_at.isoformat()
        }

        return success_response(
            message="User retrieved successfully",
            data=user_data
        )
    except Exception as e:
        return error_response(message=str(e), status_code=500)
