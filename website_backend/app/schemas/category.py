from pydantic import BaseModel
from typing import Optional, List

class CategoryBase(BaseModel):
    category_id: int
    parent_id: Optional[int] = None
    level: int
    title: str
    slug: str

class CategoryResponse(CategoryBase):
    # Dùng để đệ quy danh mục con (nếu có)
    sub_categories: List['CategoryResponse'] = []

    class Config:
        from_attributes = True