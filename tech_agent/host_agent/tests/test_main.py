import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app, classify_intent, _keyword_fallback, IntentResult

@pytest.mark.asyncio
async def test_keyword_fallback():
    """Test the robust regex/keyword fallback logic when LLM fails."""
    assert _keyword_fallback("tôi muốn kiểm tra tình trạng đơn hàng") == "order"
    assert _keyword_fallback("có nên mua macbook air m3 để code không?") == "advisor"
    assert _keyword_fallback("tìm mua con chuột logitech") == "search"
    assert _keyword_fallback("xin chào tech store") == "default"

@pytest.mark.asyncio
async def test_classify_intent_success():
    """Test LLM classification (mocked) to ensure parsing works."""
    with patch("app.main._llm_classifier.ainvoke", new_callable=AsyncMock) as mock_ainvoke:
        # Mock LLM response
        mock_ainvoke.return_value = IntentResult(intent="search")
        
        intent = await classify_intent("Tìm laptop gaming dưới 20 triệu")
        
        assert intent == "search"
        mock_ainvoke.assert_called_once()

@pytest.mark.asyncio
async def test_health_check():
    """Test basic routing health endpoint"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    
    assert response.status_code == 200
    assert response.json()["status"] == "online"

@pytest.mark.asyncio
async def test_orchestrate_rate_limit():
    """Test slowapi rate limiter prevents abuse."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Giới hạn 20 request/phút. Gửi >20 request để trigger 429.
        # Lưu ý: Trong test suite có thể phải xử lý IP context cho slowapi, 
        # tuỳ cấu hình test_client. Ở đây giả lập đơn giản.
        for _ in range(21):
            response = await ac.post("/api/orchestrate", json={
                "message": "hello",
                "session_id": "test_burst"
            })
            
    assert response.status_code == 429 # Rate Limit Exceeded
