import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class GoogleAuthURLResponse(BaseModel):
    google_auth_url: str

class GoogleUserInfo(BaseModel):
    sub: str = Field(alias="id")
    email: EmailStr
    name: str
    picture: str | None = None

    class Config:
        populate_by_name = True

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    picture: str | None
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
