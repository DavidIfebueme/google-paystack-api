from datetime import datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.payments.models.transaction import Transaction, TransactionStatus
from app.features.payments.schemas.payment import PaymentInitiateRequest as InitializeTransactionRequest
from app.features.payments.schemas.payment import PaymentInitiateResponse as InitializeTransactionResponse
from app.features.payments.services.paystack_service import PaystackService
from app.features.wallet.services.wallet_service import WalletService
from app.platform.db import get_db
from app.platform.response.schemas import ErrorCode, error_response, success_response

router = APIRouter()

@router.post("/initialize")
async def initialize_payment(request: InitializeTransactionRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await PaystackService.initialize_transaction(
            amount=request.amount,
            email=request.email
        )

        response = InitializeTransactionResponse(**result)

        return success_response(
            message="Transaction initialized successfully",
            data=response.model_dump(),
            status_code=201
        )
    except Exception as e:
        return error_response(message=f"Failed to initialize transaction: {str(e)}", status_code=500)

@router.post("/paystack/webhook")
async def paystack_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        body = await request.body()
        signature = request.headers.get("x-paystack-signature", "")

        if not PaystackService.verify_webhook_signature(body, signature):
            return error_response(message="Invalid signature", status_code=400)

        payload = await request.json()
        event = payload.get("event")
        data = payload.get("data", {})

        if event == "charge.success":
            reference = data.get("reference")

            result = await db.execute(
                select(Transaction)
                .where(Transaction.reference == reference)
                .with_for_update()
            )
            transaction = result.scalar_one_or_none()

            if not transaction:
                return error_response(
                    message="Transaction not found",
                    status_code=404,
                    error_code=ErrorCode.TRANSACTION_NOT_FOUND
                )

            if transaction.status == TransactionStatus.success:
                return success_response(
                    message="Transaction already processed",
                    data={"status": True},
                    status_code=200
                )

            wallet = await WalletService.get_wallet_by_user_id(db, transaction.user_id)

            if not wallet:
                return error_response(
                    message="Wallet not found",
                    status_code=404,
                    error_code=ErrorCode.WALLET_NOT_FOUND
                )

            await WalletService.credit_wallet(db, wallet.id, transaction.amount)

            transaction.status = TransactionStatus.success
            transaction.paid_at = datetime.utcnow()
            await db.commit()

            return success_response(
                message="Webhook processed successfully",
                data={"status": True},
                status_code=200
            )

        return success_response(
            message="Event received",
            data={"status": True},
            status_code=200
        )

    except Exception as e:
        await db.rollback()
        return error_response(
            message=f"Webhook processing failed: {str(e)}",
            status_code=500
        )
