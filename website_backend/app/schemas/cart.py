from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal

# Dữ liệu Frontend gửi lên khi bấm "Thêm vào giỏ"
class CartItemAdd(BaseModel):
    product_id: int
    quantity: int = 1

class CartItemUpdate(BaseModel):
    quantity: int

# Thông tin sản phẩm ngắn gọn để hiển thị trong giỏ hàng
class ProductInCart(BaseModel):
    title: str
    thumb: str
    slug: str
    
    class Config:
        from_attributes = True

# Dữ liệu trả về cho Frontend hiển thị
class CartItemResponse(BaseModel):
    cart_item_id: int
    product_id: int
    quantity: int
    price: float
    product: Optional[ProductInCart] = None
    
    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    cart_id: int
    user_id: Optional[int]
    status: int
    items: List[CartItemResponse] = []
    
    class Config:
        from_attributes = True