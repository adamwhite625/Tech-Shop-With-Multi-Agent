from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from app.database import get_db
from app.models import Product, Category
from app.schemas.product import PaginatedProductResponse, ProductDetailResponse

router = APIRouter()

@router.get("/", response_model=PaginatedProductResponse)
def get_products(
    page: int = Query(1, ge=1, description="Số trang hiện tại"),
    size: int = Query(12, ge=1, le=100, description="Số sản phẩm trên mỗi trang"),
    category_id: Optional[int] = Query(None, description="Lọc theo ID danh mục"),
    search: Optional[str] = Query(None, description="Tìm kiếm theo tên"),
    db: Session = Depends(get_db)
):
    # 1. Base query: Chỉ lấy sản phẩm Active (status = 1)
    query = db.query(Product).filter(Product.status == 1)

    # 2. Lọc theo Category nếu có
    if category_id:
        query = query.filter(Product.categories.any(Category.category_id == category_id))

    # 3. Tìm kiếm theo tên (Text search cơ bản)
    if search:
        query = query.filter(Product.title.ilike(f"%{search}%"))

    # 4. Đếm tổng số sản phẩm thỏa mãn điều kiện (TRƯỚC distinct)
    total = query.distinct().count()

    # 5. Phân trang (Pagination) - Thêm .distinct() để tránh lặp dữ liệu
    skip = (page - 1) * size
    products = query.order_by(Product.created_at.desc()).offset(skip).limit(size).distinct().all()

    return {
        "total": total,
        "page": page,
        "size": size,
        "data": products
    }

@router.get("/{slug}", response_model=ProductDetailResponse)
def get_product_detail(slug: str, db: Session = Depends(get_db)):
    # Lấy chi tiết sản phẩm theo Slug (Ví dụ: /api/products/iphone-15-pro-max)
    product = db.query(Product).filter(Product.slug == slug, Product.status == 1).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")
        
    return product