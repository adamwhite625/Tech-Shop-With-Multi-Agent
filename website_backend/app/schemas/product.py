from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class ProductBase(BaseModel):
    product_id: int
    title: str
    slug: str
    thumb: Optional[str] = None
    price: Decimal
    discount: Optional[Decimal] = None
    quantity: int
    status: int

class ProductDetailResponse(ProductBase):
    desc: Optional[str] = None
    summary: Optional[str] = None
    sku: Optional[str] = None
    type: Optional[str] = None
    
    class Config:
        from_attributes = True

class PaginatedProductResponse(BaseModel):
    total: int
    page: int
    size: int
    data: List[ProductBase]