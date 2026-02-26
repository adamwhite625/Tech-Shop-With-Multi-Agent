from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Order, User
from app.core.security import get_current_user

router = APIRouter()

@router.get("/me", response_model=list[dict])
def get_my_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy danh sách đơn hàng của user đang đăng nhập"""
    orders = db.query(Order).filter(Order.user_id == current_user.user_id).order_by(Order.order_id.desc()).all()
    
    result = []
    for order in orders:
        result.append({
            "order_id": order.order_id,
            "grand_total": float(order.grand_total),
            "status": order.status,
            "created_at": order.created_at.isoformat() if order.created_at else None,
        })
    
    return result
