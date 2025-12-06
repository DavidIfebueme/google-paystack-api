from fastapi import APIRouter
from app.features.auth.routes.auth_routes import router as auth_router
from app.features.payments.routes.paystack import router as payment_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router, tags=["Authentication"])
api_router.include_router(payment_router, tags=["Payments"])