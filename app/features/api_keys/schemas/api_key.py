from pydantic import BaseModel, field_validator
from datetime import datetime

class CreateAPIKeyRequest(BaseModel):
    name: str
    permissions: list[str]
    expiry: str
    
    @field_validator('expiry')
    @classmethod
    def validate_expiry(cls, v: str) -> str:
        allowed = ['1H', '1D', '1M', '1Y']
        if v not in allowed:
            raise ValueError(f'expiry must be one of {allowed}')
        return v
    
    @field_validator('permissions')
    @classmethod
    def validate_permissions(cls, v: list[str]) -> list[str]:
        allowed = ['deposit', 'transfer', 'read']
        for perm in v:
            if perm not in allowed:
                raise ValueError(f'Invalid permission: {perm}. Allowed: {allowed}')
        return v

class CreateAPIKeyResponse(BaseModel):
    api_key: str
    expires_at: datetime

class RolloverAPIKeyRequest(BaseModel):
    expired_key_id: str
    expiry: str
    
    @field_validator('expiry')
    @classmethod
    def validate_expiry(cls, v: str) -> str:
        allowed = ['1H', '1D', '1M', '1Y']
        if v not in allowed:
            raise ValueError(f'expiry must be one of {allowed}')
        return v