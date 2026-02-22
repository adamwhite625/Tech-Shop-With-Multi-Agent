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

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TechStore Order Agent", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cấu hình Database & LLM
DB_URL = os.getenv("DB_URL", "mysql+pymysql://root:root@localhost:3306/tech_store_db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

engine = create_engine(DB_URL)

@tool
def check_order_status(order_id: int) -> str:
    """Sử dụng công cụ này để tra cứu trạng thái và thông tin của một đơn hàng dựa vào mã đơn hàng (order_id)."""
    try:
        with engine.connect() as conn:
            query = text("SELECT status, grand_total, first_name, created_at FROM orders WHERE order_id = :oid")
            result = conn.execute(query, {"oid": order_id}).fetchone()
            
            if result:
                status_map = {1: "Đang chờ xử lý (Pending)", 2: "Đã thanh toán (Paid)", 3: "Đang giao hàng", 8: "Đã bị hủy (Cancelled)"}
                status_text = status_map.get(result[0], "Không xác định")
                return f"Đơn hàng #{order_id} của khách hàng {result[2]} đặt ngày {result[3]}. Tổng tiền: {result[1]:,.0f} VND. Trạng thái hiện tại: {status_text}."
            return f"Không tìm thấy đơn hàng số #{order_id} trong hệ thống."
    except Exception as e:
        return f"Lỗi hệ thống khi tra cứu: {str(e)}"

@tool
def cancel_order(order_id: int) -> str:
    """Sử dụng công cụ này ĐỂ HỦY đơn hàng nếu khách hàng yêu cầu hủy. Chỉ hủy được khi trạng thái đang là 1 (Pending)."""
    try:
        with engine.connect() as conn:
            # Kiểm tra trạng thái trước
            query_check = text("SELECT status FROM orders WHERE order_id = :oid")
            result = conn.execute(query_check, {"oid": order_id}).fetchone()
            
            if not result:
                return f"Không tìm thấy đơn hàng số #{order_id} để hủy."
            
            if result[0] != 1:
                return f"Đơn hàng #{order_id} đã được xử lý hoặc đã hủy trước đó nên không thể hủy thêm."
            
            # Thực hiện cập nhật trạng thái thành 8 (Cancelled)
            query_update = text("UPDATE orders SET status = 8 WHERE order_id = :oid")
            conn.execute(query_update, {"oid": order_id})
            conn.commit()
            return f"Đã hủy thành công đơn hàng #{order_id} theo yêu cầu."
    except Exception as e:
        return f"Lỗi hệ thống khi hủy đơn: {str(e)}"

# Danh sách Tools cung cấp cho AI
tools = [check_order_status, cancel_order]

# Khởi tạo LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Viết Prompt cho AI
prompt = ChatPromptTemplate.from_messages([
    ("system", "Bạn là trợ lý AI quản lý đơn hàng của Tech Store. Bạn có thể tra cứu và hủy đơn hàng giúp khách. Hãy luôn trả lời bằng tiếng Việt, lịch sự và ngắn gọn. Khi gọi tool trả về kết quả, hãy diễn đạt lại cho tự nhiên."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

# Khởi tạo Agent
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

class ChatRequest(BaseModel):
    session_id: str
    message: str

@app.get("/health")
def health_check():
    return {"status": "online"}

@app.post("/api/chat")
async def process_order_request(request: ChatRequest):
    logger.info(f"Order Agent received: {request.message}")
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="Chưa cấu hình API Key.")
    
    try:
        response = agent_executor.invoke({"input": request.message})
        return {
            "session_id": request.session_id,
            "role": "assistant",
            "content": response["output"]
        }
    except Exception as e:
        logger.error(f"Order Agent Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))