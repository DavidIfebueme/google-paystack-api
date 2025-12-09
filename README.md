
# google oauth & paystack wallet api

backend api for google sign-in authentication, wallet management, paystack payment integration, and api key system.

## overview

restful endpoints for user authentication, wallet creation, deposits, transfers, transaction history, and api key management. all routes protected with jwt or api key permissions. paystack integration for deposits with webhook support and idempotency.

## architecture

vertical slice structure. features are self-contained. platform layer for config, db, and responses.

## requirements

python 3.12+
postgresql
google cloud oauth credentials
paystack api keys
ngrok (for local webhook testing)

## setup

clone repo, setup venv, install dependencies

```bash
git clone <repository-url>
cd google-paystack-api
python3.12 -m venv .venv
source .venv/bin/activate
pip install uv
uv sync
```

create `.env` file with your secrets and config

```env
DATABASE_URL=postgresql+asyncpg://paystack_user:password@localhost:5432/googlepaystackapi
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=https://yourdomain.com/api/v1/auth/google/callback
PAYSTACK_SECRET_KEY=sk_test_your_secret_key
PAYSTACK_PUBLIC_KEY=pk_test_your_public_key
PAYSTACK_WEBHOOK_SECRET=your_webhook_secret
APP_NAME=google-paystack-api
DEBUG=false
FRONTEND_URL=https://yourdomain.com
JWT_SECRET_KEY=your_jwt_secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_HOURS=24
```

setup database

```bash
createdb googlepaystackapi
alembic upgrade head
```

run app

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

api docs at `/docs`

## endpoints

### authentication

get google auth url
```
get /api/v1/auth/google/login
```

google oauth callback
```
get /api/v1/auth/google/callback?code={authorization_code}
```

get user details
```
get /api/v1/auth/user/{user_id}
```

### wallet

get wallet balance
```
get /api/v1/wallet/balance
```

deposit to wallet (paystack)
```
post /api/v1/wallet/deposit
content-type: application/json
{
  "amount": 50000
}
```

paystack webhook
```
post /api/v1/payments/paystack/webhook
```

check deposit status
```
get /api/v1/wallet/deposit/{reference}/status
```

transfer funds
```
post /api/v1/wallet/transfer
content-type: application/json
{
  "wallet_number": "1234567890123",
  "amount": 10000
}
```

get transaction history
```
get /api/v1/wallet/transactions
```

### api keys

create api key
```
post /api/v1/keys/create
content-type: application/json
{
  "name": "my-service",
  "permissions": ["deposit", "transfer", "read"],
  "expiry": "1D"
}
```

rollover api key
```
post /api/v1/keys/rollover
content-type: application/json
{
  "expired_key_id": "uuid-of-expired-key",
  "expiry": "1D"
}
```

## authentication & route protection

all wallet and api key routes require jwt or api key with correct permissions. use `authorization: bearer <token>` or `x-api-key: <key>` header.

## error handling

all endpoints return standardized error responses

```json
{
  "status": "error",
  "message": "descriptive error message",
  "error_code": "ERROR_CODE",
  "data": null
}
```

## idempotency

deposits and webhooks are idempotent. duplicate requests with same reference are ignored.

## database schema

`users: id, email, name, google_id, picture, timestamps`

`wallets: id, user_id, wallet_number, balance, timestamps`

`transactions: id, reference, user_id, amount, status, authorization_url, paid_at, timestamps`

`api_keys: id, user_id, key, name, permissions, expires_at, is_active, timestamps`


