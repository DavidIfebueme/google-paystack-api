import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_google_login_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/auth/google/login")
    assert response.status_code == 200
    data = response.json()
    assert "google_auth_url" in data
    assert "accounts.google.com" in data["google_auth_url"]
