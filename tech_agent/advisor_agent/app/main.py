from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import logging
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage

# Load biến môi trường từ file .env
load_dotenv()

from app.core.logging_config import setup_logging
# Configure Logging
logger = setup_logging(__name__)

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

SEARCH_AGENT_URL = os.getenv("SEARCH_AGENT_URL", "http://search_agent:8001/api/search")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "3600"))

# Initialize LangChain LLM
llm = ChatOpenAI(
    openai_api_key=OPENAI_API_KEY,
    model_name="gpt-4o-mini",
    temperature=0.5
)

# ---------------------------------------------------------
# PROMPT TIẾNG VIỆT CHO NHÂN VIÊN TƯ VẤN (RAG + Memory)
# ---------------------------------------------------------
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """Bạn là một Chuyên viên Tư vấn Bán hàng Công nghệ chuyên nghiệp, thân thiện và am hiểu của 'PinkCapy Tech Store'.
Nhiệm vụ của bạn là tư vấn cho khách hàng về các sản phẩm công nghệ DỰA TRÊN ngữ cảnh sản phẩm được cung cấp.
Nếu ngữ cảnh trống hoặc không khớp, hãy lịch sự thông báo và đưa ra lời khuyên chung.
Sử dụng lịch sử hội thoại để hiểu ngữ cảnh, tránh hỏi lại thông tin đã biết.
Luôn xưng hô lịch sự và trả lời hoàn toàn bằng tiếng Việt.

Ngữ cảnh sản phẩm (Dữ liệu truy xuất từ kho hàng):
{context}"""
    ),
    ("placeholder", "{chat_history}"),
    ("human", "{message}"),
])


# ---------------------------------------------------------
# Redis Chat Memory Helper
# ---------------------------------------------------------
def _get_redis_history(session_id: str) -> RedisChatMessageHistory:
    """Return a RedisChatMessageHistory instance for the given session."""
    return RedisChatMessageHistory(
        session_id=f"advisor_agent:{session_id}",
        url=REDIS_URL,
        ttl=SESSION_TTL_SECONDS,
    )


# ---------------------------------------------------------
# Schemas
# ---------------------------------------------------------
class ChatRequest(BaseModel):
    session_id: str
    message: str


# ---------------------------------------------------------
# Search Agent Integration
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# Routes
# ---------------------------------------------------------
@app.get("/health")
async def health_check():
    return {"status": "online", "service": "Advisor Agent (RAG + Memory)"}


@app.post("/api/chat")
async def chat_with_advisor(request: ChatRequest):
    logger.info(f"Advisor received message from {request.session_id}: {request.message}")

    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="Hệ thống chưa được cấu hình API Key OpenAI.")

    try:
        # Step 1: Load chat history from Redis
        history = _get_redis_history(request.session_id)
        chat_history = history.messages
        logger.info(f"[{request.session_id}] Loaded {len(chat_history)} messages from Redis history.")

        # Step 2: Gọi Search Agent lấy dữ liệu thật (RAG)
        logger.info("Fetching context from Search Agent...")
        context = await fetch_context_from_search_agent(request.message)
        logger.info(f"Context retrieved:\n{context}")

        # Step 3: Dùng LLM sinh ra câu trả lời với context + history
        logger.info("Generating response via LLM...")
        chain = prompt | llm
        response_content = await chain.ainvoke({
            "context": context,
            "message": request.message,
            "chat_history": chat_history,
        })

        answer = response_content.content

        # Step 4: Persist the new turn back to Redis
        history.add_message(HumanMessage(content=request.message))
        history.add_message(AIMessage(content=answer))
        logger.info(f"[{request.session_id}] Saved turn to Redis. Total messages: {len(chat_history) + 2}")

        # Step 5: Trả về Frontend
        return {
            "session_id": request.session_id,
            "role": "assistant",
            "content": answer,
            "referenced_products": context,
        }

    except Exception as e:
        logger.error(f"Advisor error: {e}")
        raise HTTPException(status_code=500, detail=str(e))