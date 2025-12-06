from typing import Any
from pydantic import BaseModel

class APIResponse(BaseModel):
    status_code: int
    status: str
    message: str
    data: dict | list | None = None

def success_response(
    message: str,
    data: Any = None,
    status_code: int = 200
) -> APIResponse:
    return APIResponse(
        status_code=status_code,
        status="success",
        message=message,
        data=data
    )

def error_response(
    message: str,
    status_code: int = 400,
    data: Any = None
) -> APIResponse:
    return APIResponse(
        status_code=status_code,
        status="error",
        message=message,
        data=data
    )