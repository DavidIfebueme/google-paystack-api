from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.api_keys.schemas.api_key import CreateAPIKeyRequest, RolloverAPIKeyRequest
from app.features.api_keys.services.api_key_service import APIKeyService
from app.features.auth.models.user import User
from app.platform.auth.dependencies import get_current_user
from app.platform.db import get_db
from app.platform.response.schemas import ErrorCode, error_response, success_response

router = APIRouter()

@router.post("/create")
async def create_api_key(
    request: CreateAPIKeyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        expires_at = APIKeyService.parse_expiry(request.expiry)

        api_key = await APIKeyService.create_api_key(
            db=db,
            user_id=current_user.id,
            name=request.name,
            permissions=request.permissions,
            expires_at=expires_at
        )

        response_data = {
            "api_key": api_key.raw_key,
            "expires_at": api_key.expires_at.isoformat()
        }

        return success_response(
            message="API key created successfully",
            data=response_data,
            status_code=201
        )

    except ValueError as e:
        error_msg = str(e)
        error_code = ErrorCode.KEY_LIMIT_EXCEEDED if "Maximum" in error_msg else None
        return error_response(
            message=error_msg,
            status_code=400,
            error_code=error_code
        )
    except Exception as e:
        return error_response(
            message=f"Failed to create API key: {str(e)}",
            status_code=500
        )

@router.post("/rollover")
async def rollover_api_key(
    request: RolloverAPIKeyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        new_api_key = await APIKeyService.rollover_api_key(
            db=db,
            user_id=current_user.id,
            expired_key_id=request.expired_key_id,
            new_expiry=request.expiry
        )

        response_data = {
            "api_key": new_api_key.raw_key,
            "expires_at": new_api_key.expires_at.isoformat()
        }

        return success_response(
            message="API key rolled over successfully",
            data=response_data,
            status_code=201
        )

    except ValueError as e:
        return error_response(
            message=str(e),
            status_code=400
        )
    except Exception as e:
        return error_response(
            message=f"Failed to rollover API key: {str(e)}",
            status_code=500
        )
