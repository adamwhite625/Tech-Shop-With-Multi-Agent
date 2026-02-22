from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import logging
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

# Load biến môi trường từ file .env
load_dotenv()

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TechStore Advisor Agent", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants & Config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning("CẢNH BÁO: Chưa tìm thấy OPENAI_API_KEY trong file .env!")

SEARCH_AGENT_URL = "http://localhost:8001/api/search"

# Initialize LangChain LLM
llm = ChatOpenAI(
    openai_api_key=OPENAI_API_KEY,
    model_name="gpt-4o-mini",
    temperature=0.5
)

# ---------------------------------------------------------
# PROMPT TIẾNG VIỆT CHO NHÂN VIÊN TƯ VẤN (RAG)
# ---------------------------------------------------------
PROMPT_TEMPLATE = """
Bạn là một Chuyên viên Tư vấn Bán hàng Công nghệ chuyên nghiệp, thân thiện và am hiểu của 'PinkCapy Tech Store'.
Nhiệm vụ của bạn là tư vấn cho khách hàng về các sản phẩm công nghệ CHỈ DỰA TRÊN ngữ cảnh sản phẩm được cung cấp bên dưới.
Nếu ngữ cảnh trống hoặc không khớp với câu hỏi của khách hàng, hãy lịch sự thông báo rằng cửa hàng hiện không có sản phẩm chính xác như yêu cầu, nhưng bạn vẫn có thể đưa ra lời khuyên công nghệ chung để giúp đỡ họ.
Luôn luôn xưng hô lịch sự và trả lời hoàn toàn bằng tiếng Việt.

Ngữ cảnh sản phẩm (Dữ liệu truy xuất từ kho hàng):
{context}

Tin nhắn của khách hàng:
{message}

Lời tư vấn của bạn:
"""
prompt = PromptTemplate(input_variables=["context", "message"], template=PROMPT_TEMPLATE)

class ChatRequest(BaseModel):
    session_id: str
    message: str

async def fetch_context_from_search_agent(query: str) -> str:
    """
    Microservice interaction: Calls the Search Agent to get relevant products for context.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(SEARCH_AGENT_URL, json={"query": query, "limit": 3})
            response.raise_for_status()
            data = response.json()
            
            # Format the context string
            results = data.get("results", [])
            if not results:
                return "Không tìm thấy sản phẩm cụ thể nào phù hợp trong kho hàng."
            
            context_str = ""
            for item in results:
                context_str += f"- Tên: {item.get('title')}\n"
                context_str += f"  Giá: {item.get('price')} VND\n"
                context_str += f"  Đường dẫn: /{item.get('slug')}\n\n"
            return context_str
            
        except Exception as e:
            logger.error(f"Failed to fetch context from Search Agent: {e}")
            return "Lỗi khi lấy thông tin sản phẩm từ kho."

@app.get("/health")
async def health_check():
    return {"status": "online", "service": "Advisor Agent (RAG)"}

@app.post("/api/chat")
async def chat_with_advisor(request: ChatRequest):
    logger.info(f"Advisor received message from {request.session_id}: {request.message}")
    
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="Hệ thống chưa được cấu hình API Key OpenAI.")
    
    try:
        # Step 1: Gọi Search Agent lấy dữ liệu thật
        logger.info("Fetching context from Search Agent...")
        context = await fetch_context_from_search_agent(request.message)
        logger.info(f"Context retrieved: \n{context}")
        
        # Step 2: Dùng LLM sinh ra câu trả lời dựa trên Prompt Tiếng Việt
        logger.info("Generating response via LLM...")
        chain = prompt | llm
        response_content = chain.invoke({"context": context, "message": request.message})
        
        # Step 3: Trả về Frontend
        return {
            "session_id": request.session_id,
            "role": "assistant",
            "content": response_content.content,
            "referenced_products": context 
        }
        
    except Exception as e:
        logger.error(f"Advisor error: {e}")
        raise HTTPException(status_code=500, detail=str(e))