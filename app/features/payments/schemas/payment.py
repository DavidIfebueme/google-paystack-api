from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import uuid

class PaymentInitiateRequest(BaseModel):
    amount: int = Field(..., gt=0, description="Amount in kobo (must be positive)")
    email: str
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v

class PaymentInitiateResponse(BaseModel):
    reference: str
    authorization_url: str

class TransactionStatusResponse(BaseModel):
    reference: str
    status: str
    amount: int
    paid_at: datetime | None
    
    class Config:
        from_attributes = True

class PaystackWebhookEvent(BaseModel):
    event: str
    data: dict