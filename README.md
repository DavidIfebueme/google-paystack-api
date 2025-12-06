# google oauth & paystack payment api

backend api implementing google sign-in authentication and paystack payment processing with webhook support.

## overview

this project provides restful endpoints for user authentication via google oauth 2.0 and payment processing through paystack. includes real-time transaction updates via webhooks and proper idempotency handling to prevent duplicate payments.

## architecture

vertical slice architecture organizing features into self-contained modules with their own models, services, schemas, and routes. platform layer handles cross-cutting concerns like database connections and configuration.

```
app/
├── features/
│   ├── auth/           # google oauth implementation
│   └── payments/       # paystack integration
├── platform/
│   ├── config/         # environment settings
│   ├── db/            # database setup
│   └── response/      # standardized api responses
└── api_routers/       # endpoint registration
```

## requirements

- python 3.11+
- postgresql
- google cloud console project with oauth credentials
- paystack account with api keys
- ngrok (for local webhook testing)

## setup

### 1. clone and setup environment

```bash
git clone <repository-url>
cd google-paystack-api
python -m venv .venv
source .venv/bin/activate 
pip install uv
uv sync
```

### 2. configure environment variables

create `.env` file:

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/googlepaystackapi

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback

PAYSTACK_SECRET_KEY=sk_test_your_secret_key
PAYSTACK_PUBLIC_KEY=pk_test_your_public_key
PAYSTACK_WEBHOOK_SECRET=your_secret_key

APP_NAME=Google-Paystack-API
DEBUG=True
FRONTEND_URL=http://localhost:3000
```

### 3. setup database

```bash
createdb googlepaystackapi
alembic upgrade head
```

### 4. run application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

api documentation available at `http://localhost:8000/docs`

## api endpoints

### authentication

**get google auth url**
```
GET /api/v1/auth/google/login
```

returns google oauth consent page url for user authentication.

**google oauth callback**
```
GET /api/v1/auth/google/callback?code={authorization_code}
```

exchanges authorization code for user information and creates/updates user record. redirects to frontend with user_id parameter.

**get user details**
```
GET /api/v1/auth/user/{user_id}
```

retrieves user information by id.

### payments

**initiate payment**
```
POST /api/v1/payments/paystack/initiate
Content-Type: application/json

{
  "amount": 50000,
  "email": "user@example.com"
}
```

initializes paystack transaction and returns checkout url. implements idempotency by checking for duplicate transactions (same email + amount) within 10-minute window.

response:
```json
{
  "status_code": 201,
  "status": "success",
  "message": "Payment initialized successfully",
  "data": {
    "reference": "TXN_abc123...",
    "authorization_url": "https://checkout.paystack.com/..."
  }
}
```

**webhook endpoint**
```
POST /api/v1/payments/paystack/webhook
```

receives transaction status updates from paystack. validates request signature using hmac sha512 before processing events.

**check transaction status**
```
GET /api/v1/payments/{reference}/status?refresh=false
```

returns transaction status from database. set `refresh=true` to fetch latest status from paystack api.

response:
```json
{
  "status_code": 200,
  "status": "success",
  "message": "Transaction status retrieved successfully",
  "data": {
    "reference": "TXN_abc123...",
    "status": "success",
    "amount": 50000,
    "paid_at": "2025-12-06T13:12:22"
  }
}
```

## testing with ngrok

webhooks require publicly accessible url. use ngrok for local development:

```bash
ngrok http 8000
```

update these with your ngrok url:
1. `.env` - `GOOGLE_REDIRECT_URI`
2. google cloud console - oauth redirect uri
3. paystack dashboard - webhook url

## security considerations

- all secrets stored in environment variables
- webhook requests verified using hmac signature
- google oauth state parameter prevents csrf attacks
- payment references used as idempotency keys

## idempotency

duplicate payment initiations (same email + amount within 10 minutes) return existing transaction instead of creating new one. prevents accidental double charges.

## database schema

### users table
- id (uuid, primary key)
- email (unique)
- name
- picture url
- google_id (unique)
- timestamps

### transactions table
- id (uuid, primary key)
- reference (unique, indexed)
- user_id (foreign key, optional)
- email
- amount (integer, kobo/cents)
- status (enum: pending/success/failed)
- authorization_url
- paid_at (nullable)
- timestamps

## error handling

all endpoints return standardized error responses:

```json
{
  "status_code": 400,
  "status": "error",
  "message": "descriptive error message",
  "data": null
}
```

http status codes:
- 200: success
- 201: resource created
- 400: bad request
- 401: unauthorized
- 404: not found
- 500: internal server error


