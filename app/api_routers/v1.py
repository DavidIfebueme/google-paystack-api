from fastapi import APIRouter
from app.features.auth.routes.auth_routes import router as auth_router
from app.features.payments.routes.paystack import router as payment_router
from app.features.wallet.routes.wallet_routes import router as wallet_router
from app.features.api_keys.routes.api_key_routes import router as api_key_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(payment_router, prefix="/payments", tags=["Payments"])
api_router.include_router(wallet_router, prefix="/wallet", tags=["Wallet"])
api_router.include_router(api_key_router, prefix="/keys", tags=["API Keys"])