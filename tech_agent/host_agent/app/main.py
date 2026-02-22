from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

from app.core.config import settings
from app.services.a2a_client import a2a_client
from fastapi import UploadFile, File

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Orchestrator API Gateway for Multi-Agent Tech E-commerce System"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Define Pydantic Schema for input validation
# This prevents JSONDecodeError on empty requests
# ---------------------------------------------------------
class OrchestrateRequest(BaseModel):
    message: str
    session_id: str = "default_session"

@app.get("/health")
async def health_check():
    """
    Check if the Host Agent is up and running.
    """
    return {"status": "online", "service": settings.app_name}

@app.post("/api/orchestrate")
async def orchestrate_request(request_data: OrchestrateRequest):
    """
    The main brain of the system. 
    Receives user queries and routes to appropriate agent based on Intent Classification.
    
    Flow:
    - USER → HOST (Intent Classification)
      ├─ ORDER keywords → Order Agent (tra cứu/hủy đơn hàng)
      ├─ SEARCH keywords → Search Agent (tìm sản phẩm)
      └─ DEFAULT → Advisor Agent (tư vấn chung)
    """
    # Extract data using Pydantic model
    user_message = request_data.message
    session_id = request_data.session_id
    
    logger.info(f"Received message from session {session_id}: {user_message}")
    
    try:
        # Logic phân loại Intent cải tiến
        message_lower = user_message.lower()
        order_keywords = ["đơn hàng", "order", "hủy đơn", "tình trạng đơn", "kiểm tra đơn"]
        advisor_keywords = ["tư vấn", "nên mua", "gợi ý", "nào tốt", "khoảng", "phân vân", "chọn"]
        search_keywords = ["tìm", "search", "laptop", "pc", "chuột", "bàn phím", "màn hình", "đồng hồ", "điện thoại"]
        
        # 1. Kiểm tra Intent: ĐƠN HÀNG (Tra cứu / Hủy)
        if any(keyword in message_lower for keyword in order_keywords):
            logger.info("Intent detected: ORDER. Routing to Order Agent...")
            response = await a2a_client.forward_to_order(session_id=session_id, message=user_message)
            return JSONResponse(content={"agent": "order", "data": response})

        # 2. Kiểm tra Intent: TƯ VẤN CHUYÊN SÂU (Ưu tiên cao hơn tìm kiếm)
        elif any(keyword in message_lower for keyword in advisor_keywords):
            logger.info("Intent detected: ADVISOR. Routing to Advisor Agent...")
            response = await a2a_client.forward_to_advisor(session_id=session_id, message=user_message)
            return JSONResponse(content={"agent": "advisor", "data": response})

        # 3. Kiểm tra Intent: TÌM KIẾM NHANH (Chỉ cần list sản phẩm)
        elif any(keyword in message_lower for keyword in search_keywords):
            logger.info("Intent detected: SEARCH. Routing to Search Agent...")
            response = await a2a_client.forward_to_search(query=user_message)
            return JSONResponse(content={"agent": "search", "data": response})
            
        # 4. Mặc định: Giao cho Advisor xử lý
        else:
            logger.info("Intent detected: DEFAULT -> ADVISOR. Routing to Advisor Agent...")
            response = await a2a_client.forward_to_advisor(session_id=session_id, message=user_message)
            return JSONResponse(content={"agent": "advisor", "data": response})

    except Exception as e:
        logger.error(f"Routing failed: {str(e)}")
        # If target agents are not up yet, we catch the 503 error gracefully
        return JSONResponse(
            status_code=503, 
            content={"error": str(e), "message": "The requested AI agent is currently offline."}
        )
    
@app.post("/api/orchestrate/image")
async def orchestrate_image_request(file: UploadFile = File(...)):
    """
    Nhận file ảnh từ Frontend và route sang Search Agent (CLIP Image Search).
    """
    logger.info(f"Received image search request: {file.filename}")
    
    try:
        # Đọc file thành bytes
        image_bytes = await file.read()
        
        # Forward sang Search Agent
        response = await a2a_client.forward_image_to_search(
            image_bytes=image_bytes, 
            filename=file.filename,
            content_type=file.content_type
        )
        
        return JSONResponse(content={"agent": "search_image", "data": response})

    except Exception as e:
        logger.error(f"Image Routing failed: {str(e)}")
        return JSONResponse(status_code=503, content={"error": str(e)})