import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.models.user import User
from app.features.payments.services.paystack_service import PaystackService
from app.features.wallet.schemas.wallet import (
    BalanceResponse,
    DepositRequest,
    DepositResponse,
    TransferRequest,
)
from app.features.wallet.services.transaction_service import WalletTransactionService
from app.features.wallet.services.wallet_service import WalletService
from app.platform.auth.dependencies import require_permission
from app.platform.db import get_db
from app.platform.response.schemas import ErrorCode, error_response, success_response

router = APIRouter()

@router.post("/deposit")
async def deposit_to_wallet(
    request: DepositRequest,
    user_and_auth: tuple[User, str] = Depends(require_permission("deposit")),
    db: AsyncSession = Depends(get_db)
):
    user, auth_type = user_and_auth

    try:
        wallet = await WalletService.get_wallet_by_user_id(db, user.id)

        if not wallet:
            return error_response(
                message="Wallet not found",
                status_code=404,
                error_code=ErrorCode.WALLET_NOT_FOUND
            )

        result = await PaystackService.initialize_transaction(
            amount=request.amount,
            email=user.email
        )

        transaction = await WalletTransactionService.create_deposit_transaction(
            db=db,
            user_id=user.id,
            reference=result["reference"],
            amount=request.amount,
            authorization_url=result["authorization_url"],
            email=user.email
        )

        response = DepositResponse(
            reference=transaction.reference,
            authorization_url=transaction.authorization_url
        )

        return success_response(
            message="Deposit initialized successfully",
            data=response.model_dump(),
            status_code=201
        )

    except ValueError as e:
        return error_response(
            message=str(e),
            status_code=400,
            error_code=ErrorCode.INVALID_AMOUNT
        )
    except Exception as e:
        return error_response(
            message=f"Failed to initialize deposit: {str(e)}",
            status_code=500
        )

@router.get("/deposit/{reference}/status")
async def get_deposit_status(
    reference: str,
    live_verify: bool = False,
    db: AsyncSession = Depends(get_db)
):
    try:
        if live_verify:
            paystack_status = await PaystackService.verify_transaction(reference)
            await WalletTransactionService.update_transaction_status_from_paystack(
                db, reference, paystack_status
            )
        transaction = await WalletTransactionService.get_transaction_by_reference(db, reference)

        if not transaction:
            return error_response(
                message="Transaction not found",
                status_code=404,
                error_code=ErrorCode.TRANSACTION_NOT_FOUND
            )

        return success_response(
            message="Transaction status retrieved successfully",
            data={
                "reference": transaction.reference,
                "status": transaction.status.value,
                "amount": transaction.amount
            },
            status_code=200
        )

    except Exception as e:
        return error_response(
            message=f"Failed to retrieve status: {str(e)}",
            status_code=500
        )

@router.get("/balance")
async def get_wallet_balance(
    user_and_auth: tuple[User, str] = Depends(require_permission("read")),
    db: AsyncSession = Depends(get_db)
):
    user, auth_type = user_and_auth

    try:
        wallet = await WalletService.get_wallet_by_user_id(db, user.id)

        if not wallet:
            return error_response(
                message="Wallet not found",
                status_code=404,
                error_code=ErrorCode.WALLET_NOT_FOUND
            )

        response = BalanceResponse(balance=wallet.balance)

        return success_response(
            message="Balance retrieved successfully",
            data=response.model_dump(),
            status_code=200
        )

    except Exception as e:
        return error_response(
            message=f"Failed to retrieve balance: {str(e)}",
            status_code=500
        )

@router.post("/transfer")
async def transfer_funds(
    request: TransferRequest,
    user_and_auth: tuple[User, str] = Depends(require_permission("transfer")),
    db: AsyncSession = Depends(get_db)
):
    user, auth_type = user_and_auth

    try:
        sender_wallet = await WalletService.get_wallet_by_user_id(db, user.id)

        if not sender_wallet:
            return error_response(
                message="Sender wallet not found",
                status_code=404,
                error_code=ErrorCode.WALLET_NOT_FOUND
            )

        recipient_wallet = await WalletService.get_wallet_by_number(db, request.wallet_number)

        if not recipient_wallet:
            return error_response(
                message="Recipient wallet not found",
                status_code=404,
                error_code=ErrorCode.WALLET_NOT_FOUND
            )

        if sender_wallet.id == recipient_wallet.id:
            return error_response(
                message="Cannot transfer to same wallet",
                status_code=400,
                error_code=ErrorCode.INVALID_WALLET_NUMBER
            )

        if sender_wallet.balance < request.amount:
            return error_response(
                message="Insufficient balance",
                status_code=400,
                error_code=ErrorCode.INSUFFICIENT_BALANCE
            )

        await WalletService.transfer_funds(
            db=db,
            sender_wallet_id=sender_wallet.id,
            recipient_wallet_id=recipient_wallet.id,
            amount=request.amount
        )

        reference = f"TXN_{uuid.uuid4()}"
        transaction = await WalletTransactionService.create_transfer_transaction(
            db=db,
            user_id=user.id,
            sender_wallet_id=sender_wallet.id,
            recipient_wallet_id=recipient_wallet.id,
            amount=request.amount,
            reference=reference
        )

        response_data = {
            "reference": transaction.reference,
            "amount": transaction.amount,
            "recipient_wallet": request.wallet_number,
            "status": "success",
            "timestamp": transaction.created_at.isoformat()
        }

        return success_response(
            message="Transfer completed successfully",
            data=response_data,
            status_code=200
        )

    except ValueError as e:
        error_msg = str(e)
        if "Insufficient balance" in error_msg:
            error_code = ErrorCode.INSUFFICIENT_BALANCE
        elif "Wallet number" in error_msg:
            error_code = ErrorCode.INVALID_WALLET_NUMBER
        elif "Amount" in error_msg:
            error_code = ErrorCode.INVALID_AMOUNT
        else:
            error_code = None

        return error_response(
            message=error_msg,
            status_code=400,
            error_code=error_code
        )
    except Exception as e:
        return error_response(
            message=f"Transfer failed: {str(e)}",
            status_code=500
        )

@router.get("/transactions")
async def get_transaction_history(
    user_and_auth: tuple[User, str] = Depends(require_permission("read")),
    db: AsyncSession = Depends(get_db)
):
    user, auth_type = user_and_auth

    try:
        transactions = await WalletTransactionService.get_user_transactions(db, user.id)

        history = [
            {
                "type": txn.transaction_type.value,
                "amount": txn.amount,
                "status": txn.status.value,
                "created_at": txn.created_at.isoformat(),
                "reference": txn.reference
            }
            for txn in transactions
        ]

        return success_response(
            message="Transaction history retrieved successfully",
            data=history,
            status_code=200
        )

    except Exception as e:
        return error_response(
            message=f"Failed to retrieve transaction history: {str(e)}",
            status_code=500
        )
