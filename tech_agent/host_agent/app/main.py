from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
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
    Receives user queries and routes to ADVISOR Agent FIRST.
    
    Flow: Host ➡️ Advisor ➡️ Search ➡️ Qdrant ➡️ Advisor (OpenAI) ➡️ Host ➡️ User
    
    Advisor Agent will:
    1. Call Search Agent to fetch product context
    2. Use OpenAI LLM to generate personalized recommendation
    3. Return comprehensive response with both search results and advice
    """
    # Extract data using Pydantic model
    user_message = request_data.message
    session_id = request_data.session_id
    
    logger.info(f"Received message from session {session_id}: {user_message}")
    
    try:
        # Route ALWAYS to Advisor Agent
        logger.info("Routing to Advisor Agent (will internally call Search if needed)...")
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