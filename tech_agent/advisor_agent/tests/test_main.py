import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch
from app.main import app

@pytest.mark.asyncio
async def test_health_check():
    """Test advisor agent health endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()

@pytest.mark.asyncio
async def test_chat_without_api_key_returns_500():
    """Test that chat fails safely if API key is missing."""
    with patch("app.main.OPENAI_API_KEY", new=None):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/api/chat", json={
                "message": "tư vấn mua chuột",
                "session_id": "test_1"
            })
            
        assert response.status_code == 500
        assert "chưa được cấu hình" in response.json()["detail"].lower()
