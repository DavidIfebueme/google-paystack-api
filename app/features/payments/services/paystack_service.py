import httpx
import hmac
import hashlib
from typing import Dict, Any
import uuid

from app.platform.config.settings import get_settings

settings = get_settings()

class PaystackService:
    BASE_URL = "https://api.paystack.co"
    
    @staticmethod
    def _get_headers() -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
    
    @staticmethod
    async def initialize_transaction(amount: int, email: str) -> Dict[str, Any]:
        reference = f"TXN_{uuid.uuid4().hex}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PaystackService.BASE_URL}/transaction/initialize",
                headers=PaystackService._get_headers(),
                json={
                    "email": email,
                    "amount": amount,
                    "reference": reference
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "reference": reference,
                "authorization_url": data["data"]["authorization_url"]
            }
    
    @staticmethod
    async def verify_transaction(reference: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PaystackService.BASE_URL}/transaction/verify/{reference}",
                headers=PaystackService._get_headers()
            )
            response.raise_for_status()
            return response.json()["data"]
    
    @staticmethod
    def verify_webhook_signature(payload: bytes, signature: str) -> bool:
        computed_signature = hmac.new(
            settings.PAYSTACK_WEBHOOK_SECRET.encode('utf-8'),
            payload,
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(computed_signature, signature)