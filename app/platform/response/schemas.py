from typing import Any, Optional
from pydantic import BaseModel
from fastapi.responses import JSONResponse

class ErrorCode:
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    INVALID_API_KEY = "INVALID_API_KEY"
    EXPIRED_API_KEY = "EXPIRED_API_KEY"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    KEY_LIMIT_EXCEEDED = "KEY_LIMIT_EXCEEDED"
    WALLET_NOT_FOUND = "WALLET_NOT_FOUND"
    TRANSACTION_NOT_FOUND = "TRANSACTION_NOT_FOUND"
    INVALID_AMOUNT = "INVALID_AMOUNT"
    INVALID_WALLET_NUMBER = "INVALID_WALLET_NUMBER"
    DUPLICATE_TRANSACTION = "DUPLICATE_TRANSACTION"

class SuccessResponse(BaseModel):
    status: str = "success"
    message: str
    data: Optional[Any] = None

class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    error_code: Optional[str] = None
    data: Optional[Any] = None

def success_response(message: str, data: Any = None, status_code: int = 200) -> JSONResponse:
    response = SuccessResponse(message=message, data=data)
    return JSONResponse(
        status_code=status_code,
        content=response.model_dump()
    )

def error_response(message: str, status_code: int = 400, error_code: Optional[str] = None, data: Any = None) -> JSONResponse:
    response = ErrorResponse(message=message, error_code=error_code, data=data)
    return JSONResponse(
        status_code=status_code,
        content=response.model_dump()
    )