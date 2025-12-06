from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.platform.db.base import get_db
from app.platform.response.schemas import success_response, error_response
from app.features.payments.services.paystack_service import PaystackService
from app.features.payments.services.transaction_service import TransactionService
from app.features.payments.schemas.payment import (
    PaymentInitiateRequest,
    PaymentInitiateResponse,
    TransactionStatusResponse,
    PaystackWebhookEvent
)
from app.features.payments.models.transaction import TransactionStatus

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/paystack/initiate", status_code=status.HTTP_201_CREATED)
async def initiate_payment(
    payment_request: PaymentInitiateRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await PaystackService.initialize_transaction(
            amount=payment_request.amount,
            email=payment_request.email
        )
        
        duplicate = await TransactionService.check_duplicate_transaction(
            db, result["reference"]
        )
        
        if duplicate:
            existing_transaction = await TransactionService.get_transaction_by_reference(
                db, result["reference"]
            )
            return success_response(
                message="Transaction already exists",
                data={
                    "reference": existing_transaction.reference,
                    "authorization_url": existing_transaction.authorization_url
                },
                status_code=200
            )
        
        transaction = await TransactionService.create_transaction(
            db=db,
            reference=result["reference"],
            amount=payment_request.amount,
            authorization_url=result["authorization_url"]
        )
        
        return success_response(
            message="Payment initialized successfully",
            data={
                "reference": transaction.reference,
                "authorization_url": transaction.authorization_url
            },
            status_code=201
        )
    except Exception as e:
        response = error_response(
            message=f"Payment initialization failed: {str(e)}",
            status_code=500
        )
        return JSONResponse(
            status_code=500,
            content=response.model_dump()
        )

@router.post("/paystack/webhook")
async def paystack_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        body = await request.body()
        signature = request.headers.get("x-paystack-signature", "")
        
        if not PaystackService.verify_webhook_signature(body, signature):
            response = error_response(
                message="Invalid signature",
                status_code=400
            )
            return JSONResponse(
                status_code=400,
                content=response.model_dump()
            )
        
        event = await request.json()
        webhook_event = PaystackWebhookEvent(**event)
        
        if webhook_event.event == "charge.success":
            reference = webhook_event.data.get("reference")
            paid_at_str = webhook_event.data.get("paid_at")
            
            paid_at = datetime.fromisoformat(paid_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
            
            await TransactionService.update_transaction_status(
                db=db,
                reference=reference,
                status=TransactionStatus.success,
                paid_at=paid_at
            )
        elif webhook_event.event == "charge.failed":
            reference = webhook_event.data.get("reference")
            await TransactionService.update_transaction_status(
                db=db,
                reference=reference,
                status=TransactionStatus.failed
            )
        
        return {"status": True}
    except Exception as e:
        response = error_response(
            message=f"Webhook processing failed: {str(e)}",
            status_code=500
        )
        return JSONResponse(
            status_code=500,
            content=response.model_dump()
        )

@router.get("/{reference}/status")
async def get_transaction_status(
    reference: str,
    refresh: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    try:
        transaction = await TransactionService.get_transaction_by_reference(db, reference)
        
        if not transaction:
            response = error_response(
                message="Transaction not found",
                status_code=404
            )
            return JSONResponse(
                status_code=404,
                content=response.model_dump()
            )
        
        if refresh or transaction.status == TransactionStatus.pending:
            try:
                paystack_data = await PaystackService.verify_transaction(reference)
                
                if paystack_data["status"] == "success":
                    paid_at_str = paystack_data["paid_at"]
                    paid_at = datetime.fromisoformat(paid_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
                    
                    transaction = await TransactionService.update_transaction_status(
                        db=db,
                        reference=reference,
                        status=TransactionStatus.success,
                        paid_at=paid_at
                    )
                elif paystack_data["status"] == "failed":
                    transaction = await TransactionService.update_transaction_status(
                        db=db,
                        reference=reference,
                        status=TransactionStatus.failed
                    )
            except Exception:
                pass
        
        return success_response(
            message="Transaction status retrieved successfully",
            data=TransactionStatusResponse.model_validate(transaction).model_dump()
        )
    except Exception as e:
        response = error_response(
            message=f"Failed to retrieve transaction status: {str(e)}",
            status_code=500
        )
        return JSONResponse(
            status_code=500,
            content=response.model_dump()
        )