import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_payment_initiate_validation(client: AsyncClient):
    response = await client.post(
        "/api/v1/payments/paystack/initiate",
        json={"amount": -100, "email": "test@example.com"}
    )
    assert response.status_code == 422