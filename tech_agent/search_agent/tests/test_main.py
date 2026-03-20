import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app, app_state

@pytest.mark.asyncio
async def test_health_check_not_ready():
    """Test health check when models aren't loaded yet."""
    app_state.is_ready = False
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
        
    assert response.status_code == 200
    assert response.json()["models_loaded"] is False

@pytest.mark.asyncio
async def test_search_not_ready_returns_503():
    """Test that searching before semantic models/Qdrant are loaded returns 503 instead of crashing."""
    app_state.is_ready = False
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/search", json={"query": "laptop"})
        
    assert response.status_code == 503
    assert "chưa tải xong" in response.json()["detail"].lower()
