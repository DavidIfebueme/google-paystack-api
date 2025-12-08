from pydantic import BaseModel, field_validator
from datetime import datetime

class DepositRequest(BaseModel):
    amount: int
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: int) -> int:
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v

class DepositResponse(BaseModel):
    reference: str
    authorization_url: str

class TransferRequest(BaseModel):
    wallet_number: str
    amount: int
    
    @field_validator('wallet_number')
    @classmethod
    def validate_wallet_number(cls, v: str) -> str:
        if len(v) != 13 or not v.isdigit():
            raise ValueError('Wallet number must be exactly 13 digits')
        return v
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: int) -> int:
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v

class TransferResponse(BaseModel):
    status: str
    message: str

class BalanceResponse(BaseModel):
    balance: int

class TransactionHistoryItem(BaseModel):
    type: str
    amount: int
    status: str
    created_at: datetime
    reference: str