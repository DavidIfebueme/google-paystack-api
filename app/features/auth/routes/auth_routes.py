from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.platform.db.base import get_db
from app.platform.response.schemas import success_response, error_response
from app.features.auth.services.auth_service import AuthService
from app.features.auth.schemas.auth import GoogleAuthURLResponse, UserResponse
from app.platform.config.settings import get_settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()

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
        
        redirect_url = f"{settings.FRONTEND_URL}/auth/success?user_id={user.id}"
        return RedirectResponse(url=redirect_url)
    except Exception as e:
        response = error_response(
            message=f"Authentication failed: {str(e)}",
            status_code=400
        )
        return JSONResponse(
            status_code=400,
            content=response.model_dump()
        )

@router.get("/user/{user_id}")
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    try:
        user = await AuthService.get_user_by_id(db, user_id)
        if not user:
            response = error_response(
                message="User not found",
                status_code=404
            )
            return JSONResponse(
                status_code=404,
                content=response.model_dump()
            )
        return success_response(
            message="User retrieved successfully",
            data=UserResponse.model_validate(user).model_dump()
        )
    except Exception as e:
        response = error_response(
            message=f"Failed to retrieve user: {str(e)}",
            status_code=500
        )
        return JSONResponse(
            status_code=500,
            content=response.model_dump()
        )