from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import os
from dotenv import load_dotenv

from sqlalchemy import create_engine, text
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.tools import tool
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage

from app.core.logging_config import setup_logging

load_dotenv()
logger = setup_logging(__name__)

app = FastAPI(title="TechStore Order Agent", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Config
# ---------------------------------------------------------
DB_URL = os.getenv("DB_URL", "mysql+pymysql://root:root@localhost:3306/tech_store_db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "3600"))  # 1 hour default

engine = create_engine(DB_URL)

# ---------------------------------------------------------
# Agent Tools
# ---------------------------------------------------------
@tool
def check_order_status(order_id: int) -> str:
    """Sử dụng công cụ này để tra cứu trạng thái và thông tin của một đơn hàng dựa vào mã đơn hàng (order_id)."""
    try:
        with engine.connect() as conn:
            query = text("SELECT status, grand_total, first_name, created_at FROM orders WHERE order_id = :oid")
            result = conn.execute(query, {"oid": order_id}).fetchone()

            if result:
                status_map = {
                    1: "Đang chờ xử lý (Pending)",
                    2: "Đã thanh toán (Paid)",
                    3: "Đang giao hàng",
                    8: "Đã bị hủy (Cancelled)"
                }
                status_text = status_map.get(result[0], "Không xác định")
                return (
                    f"Đơn hàng #{order_id} của khách hàng {result[2]} "
                    f"đặt ngày {result[3]}. Tổng tiền: {result[1]:,.0f} VND. "
                    f"Trạng thái hiện tại: {status_text}."
                )
            return f"Không tìm thấy đơn hàng số #{order_id} trong hệ thống."
    except Exception as e:
        return f"Lỗi hệ thống khi tra cứu: {str(e)}"

@tool
def cancel_order(order_id: int) -> str:
    """Sử dụng công cụ này ĐỂ HỦY đơn hàng nếu khách hàng yêu cầu hủy. Chỉ hủy được khi trạng thái đang là 1 (Pending)."""
    try:
        with engine.connect() as conn:
            query_check = text("SELECT status FROM orders WHERE order_id = :oid")
            result = conn.execute(query_check, {"oid": order_id}).fetchone()

            if not result:
                return f"Không tìm thấy đơn hàng số #{order_id} để hủy."

            if result[0] != 1:
                return f"Đơn hàng #{order_id} đã được xử lý hoặc đã hủy trước đó nên không thể hủy thêm."

            query_update = text("UPDATE orders SET status = 8 WHERE order_id = :oid")
            conn.execute(query_update, {"oid": order_id})
            conn.commit()
            return f"Đã hủy thành công đơn hàng #{order_id} theo yêu cầu."
    except Exception as e:
        return f"Lỗi hệ thống khi hủy đơn: {str(e)}"

@tool
def get_my_orders(user_id: int) -> str:
    """BẮT BUỘC DÙNG CÔNG CỤ NÀY khi khách hỏi họ có đơn hàng nào không, hoặc muốn xem danh sách các đơn đặt hàng cũ. Tham số truyền vào là user_id (lấy từ system prompt)."""
    try:
        with engine.connect() as conn:
            query = text("SELECT order_id, status, grand_total, created_at FROM orders WHERE user_id = :uid ORDER BY order_id DESC LIMIT 5")
            results = conn.execute(query, {"uid": user_id}).fetchall()
            
            if not results:
                return "Bạn chưa có đơn hàng nào."
            
            status_map = {1: "Pending", 2: "Paid", 3: "Shipping", 8: "Cancelled"}
            res_text = "Các đơn hàng gần đây của bạn:\n"
            for row in results:
                status_text = status_map.get(row[1], "Unknown")
                res_text += f"- Mã #{row[0]}: {row[2]:,.0f} VND - Trạng thái: {status_text} (Đặt {row[3]})\n"
            return res_text
    except Exception as e:
        return f"Lỗi hệ thống khi lấy đơn hàng: {str(e)}"

@tool
def get_my_cart(user_id: int) -> str:
    """BẮT BUỘC DÙNG CÔNG CỤ NÀY khi khách hỏi về nội dung giỏ hàng (cart) của họ. Tham số truyền vào là user_id."""
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT p.title, ci.quantity, ci.price 
                FROM cart_items ci
                JOIN carts c ON ci.cart_id = c.cart_id
                JOIN products p ON ci.product_id = p.product_id
                WHERE c.user_id = :uid AND c.status = 1
            """)
            results = conn.execute(query, {"uid": user_id}).fetchall()
            
            if not results:
                return "Giỏ hàng của bạn đang trống."
                
            res_text = "Giỏ hàng của bạn bao gồm:\n"
            total = 0
            for row in results:
                sub = row[1] * row[2]
                res_text += f"- {row[0]} x {row[1]} cái\n"
                total += sub
            res_text += f"Tổng cộng: {total:,.0f} VNĐ"
            return res_text
    except Exception as e:
        return f"Lỗi hệ thống khi lấy giỏ hàng: {str(e)}"

tools = [check_order_status, cancel_order, get_my_orders, get_my_cart]

# ---------------------------------------------------------
# LLM & Prompt — with chat_history placeholder for memory
# ---------------------------------------------------------
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "Bạn là trợ lý AI quản lý đơn hàng của Tech Store. "
        "Bạn có thể:\n"
        "1. Tra cứu và hủy đơn hàng BẰNG MÃ ĐƠN HÀNG (ID cụ thể).\n"
        "2. Tra cứu danh sách các đơn hàng hiện có CỦA KHÁCH.\n"
        "3. Tra cứu giỏ hàng CỦA KHÁCH.\n"
        "QUAN TRỌNG: Khi khách hỏi về giỏ hàng hoặc danh sách đơn hàng, BẠN BẮT BUỘC PHẢI DÙNG TOOL (get_my_orders, get_my_cart). TUYỆT ĐỐI không được báo lỗi là không có quyền truy cập. Bạn chỉ cần truyền user_id từ hệ thống vào tool.\n"
        "Hãy luôn trả lời bằng tiếng Việt, lịch sự và ngắn gọn. "
        "Khi gọi tool trả về kết quả, hãy diễn đạt lại cho tự nhiên. "
        "Sử dụng lịch sử hội thoại để hiểu ngữ cảnh (ví dụ: 'đơn đó', 'hủy đi'...).\n"
        "{user_context}"
    ),
    ("placeholder", "{chat_history}"),   # ← Redis history injected here
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# ---------------------------------------------------------
# Helper: Load & Save chat history via Redis
# ---------------------------------------------------------
def _get_redis_history(session_id: str) -> RedisChatMessageHistory:
    """Return a RedisChatMessageHistory instance for the given session."""
    return RedisChatMessageHistory(
        session_id=f"order_agent:{session_id}",
        url=REDIS_URL,
        ttl=SESSION_TTL_SECONDS,
    )

# ---------------------------------------------------------
# API
# ---------------------------------------------------------
class ChatRequest(BaseModel):
    session_id: str
    message: str

@app.get("/health")
def health_check():
    return {"status": "online", "service": "Order Agent"}

@app.post("/api/chat")
async def process_order_request(request: ChatRequest):
    logger.info(f"[{request.session_id}] Order Agent received: {request.message}")

    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="Chưa cấu hình API Key.")

    try:
        # 1. Load history from Redis
        history = _get_redis_history(request.session_id)
        chat_history = history.messages  # list[BaseMessage]
        logger.info(f"[{request.session_id}] Loaded {len(chat_history)} messages from Redis history.")

        # Extract user_id from session_id
        user_id = None
        if request.session_id.startswith("user_"):
            try:
                user_id = int(request.session_id.split("_")[1])
            except ValueError:
                pass
        
        user_context = f"Thông tin khách hàng: user_id = {user_id}" if user_id else "Khách hàng chưa đăng nhập, không có thông tin user_id."

        # 2. Run agent with full conversation context
        response = agent_executor.invoke({
            "input": request.message,
            "chat_history": chat_history,
            "user_context": user_context,
        })
        answer = response["output"]

        # 3. Persist the new turn back to Redis
        history.add_message(HumanMessage(content=request.message))
        history.add_message(AIMessage(content=answer))
        logger.info(f"[{request.session_id}] Saved turn to Redis. Total messages: {len(chat_history) + 2}")

        return {
            "session_id": request.session_id,
            "role": "assistant",
            "content": answer,
        }

    except Exception as e:
        logger.error(f"[{request.session_id}] Order Agent Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))