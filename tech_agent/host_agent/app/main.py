from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.services.a2a_client import a2a_client
from app.core.logging_config import setup_logging

# Configure Structured JSON Logging
logger = setup_logging(__name__)

# Configure Rate Limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Orchestrator API Gateway for Multi-Agent Tech E-commerce System"
)

# Apply Rate Limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Define Pydantic Schema for input validation
# ---------------------------------------------------------
class OrchestrateRequest(BaseModel):
    message: str
    session_id: str = "default_session"

# ---------------------------------------------------------
# Intent Classification — Pydantic schema for structured output
# ---------------------------------------------------------
class IntentResult(BaseModel):
    intent: Literal["order", "advisor", "search", "default"]

INTENT_SYSTEM_PROMPT = """Bạn là bộ phân loại ý định (intent classifier) cho hệ thống mua sắm công nghệ.
Nhiệm vụ: Đọc tin nhắn của người dùng và trả về đúng 1 trong 4 intent sau:

- "order"   : Người dùng hỏi về đơn hàng (tra cứu, kiểm tra, hủy đơn, tình trạng giao hàng...)
- "search"  : Người dùng muốn TÌM hoặc XEM DANH SÁCH sản phẩm (laptop, điện thoại, chuột, bàn phím...)
- "advisor" : Người dùng muốn được TƯ VẤN, SO SÁNH, GỢI Ý sản phẩm phù hợp với nhu cầu
- "default" : Tin nhắn chào hỏi, câu hỏi bất kỳ không thuộc 3 loại trên

Phân biệt rõ "search" vs "advisor":
- "Tìm laptop gaming" → search (chỉ muốn danh sách)
- "Tư vấn mua laptop gaming" / "Nên mua laptop nào khoảng 20 triệu" → advisor (muốn lời khuyên)

Chỉ trả về JSON, không giải thích thêm."""

_llm_classifier = ChatOpenAI(
    openai_api_key=settings.openai_api_key,
    model="gpt-4o-mini",
    temperature=0
).with_structured_output(IntentResult)

# ---------------------------------------------------------
# Keyword-based fallback (used if LLM fails)
# ---------------------------------------------------------
def _keyword_fallback(message: str) -> str:
    msg = message.lower()
    if any(k in msg for k in ["đơn hàng", "order", "hủy đơn", "tình trạng đơn", "kiểm tra đơn"]):
        return "order"
    if any(k in msg for k in ["tư vấn", "nên mua", "gợi ý", "nào tốt", "khoảng", "phân vân", "chọn"]):
        return "advisor"
    if any(k in msg for k in ["tìm", "search", "laptop", "pc", "chuột", "bàn phím", "màn hình", "điện thoại"]):
        return "search"
    return "default"

async def classify_intent(message: str) -> str:
    """
    LLM-based intent classification with keyword fallback.
    Uses structured output (Pydantic) to guarantee valid intent values.
    """
    try:
        result: IntentResult = await _llm_classifier.ainvoke([
            SystemMessage(content=INTENT_SYSTEM_PROMPT),
            HumanMessage(content=message)
        ])
        logger.info(f"LLM classified intent", extra={"intent": result.intent, "message_preview": message[:60]})
        return result.intent
    except Exception as e:
        logger.warning(f"LLM intent classification failed", exc_info=True)
        fallback = _keyword_fallback(message)
        logger.info(f"Keyword fallback intent", extra={"intent": fallback})
        return fallback

# ---------------------------------------------------------
# Routes
# ---------------------------------------------------------
@app.get("/health")
async def health_check():
    return {"status": "online", "service": settings.app_name}

@app.post("/api/orchestrate")
@limiter.limit("20/minute") # Giới hạn 20 request/phút mỗi IP
async def orchestrate_request(request: Request, request_data: OrchestrateRequest):
    """
    Main orchestrator. Classifies user intent via LLM, then routes to the
    appropriate specialist agent.
    """
    user_message = request_data.message
    session_id = request_data.session_id

    logger.info("Received orchestration request", extra={"session_id": session_id, "user_message": user_message})

    try:
        intent = await classify_intent(user_message)

        if intent == "order":
            logger.info("Routing to Order Agent", extra={"session_id": session_id, "intent": intent})
            response = await a2a_client.forward_to_order(session_id=session_id, message=user_message)
            return JSONResponse(content={"agent": "order", "data": response})

        elif intent == "search":
            logger.info("Routing to Search Agent", extra={"session_id": session_id, "intent": intent})
            response = await a2a_client.forward_to_search(query=user_message)
            return JSONResponse(content={"agent": "search", "data": response})

        else:  # "advisor" or "default"
            logger.info("Routing to Advisor Agent", extra={"session_id": session_id, "intent": intent})
            response = await a2a_client.forward_to_advisor(session_id=session_id, message=user_message)
            return JSONResponse(content={"agent": "advisor", "data": response})

    except Exception as e:
        logger.error("Routing failed", extra={"session_id": session_id}, exc_info=True)
        return JSONResponse(
            status_code=503,
            content={"error": str(e), "message": "The requested AI agent is currently offline or experiencing issues."}
        )

@app.post("/api/orchestrate/image")
@limiter.limit("5/minute") # Giới hạn 5 ảnh/phút mỗi IP vì xử lý ảnh nặng hơn
async def orchestrate_image_request(request: Request, file: UploadFile = File(...)):
    """
    Nhận file ảnh từ Frontend và route sang Search Agent (CLIP Image Search).
    """
    logger.info("Received image search request", extra={"filename": file.filename})

    try:
        image_bytes = await file.read()
        
        # Thêm validation cơ bản cho kích thước file (ví dụ: tối đa 5MB)
        if len(image_bytes) > 5 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large (max 5MB)")

        response = await a2a_client.forward_image_to_search(
            image_bytes=image_bytes,
            filename=file.filename,
            content_type=file.content_type
        )
        return JSONResponse(content={"agent": "search_image", "data": response})

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Image Routing failed", exc_info=True)
        return JSONResponse(status_code=503, content={"error": str(e)})