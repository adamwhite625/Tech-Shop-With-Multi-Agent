from pydantic import BaseModel, EmailStr
from typing import Optional

class CheckoutRequest(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: EmailStr
    line1: str  # Địa chỉ cụ thể (Số nhà, đường)
    city: str
    province: str
    note: Optional[str] = None
    payment_method: int = 1  # 1: Thanh toán khi nhận hàng (COD), 2: VNPay/Momo