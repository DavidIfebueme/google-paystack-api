from pydantic import BaseModel, EmailStr
from datetime import datetime
import uuid

class GoogleAuthURLResponse(BaseModel):
    google_auth_url: str

class GoogleUserInfo(BaseModel):
    sub: str
    email: EmailStr
    name: str
    picture: str | None = None

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    picture: str | None
    created_at: datetime
    
    class Config:
        from_attributes = True