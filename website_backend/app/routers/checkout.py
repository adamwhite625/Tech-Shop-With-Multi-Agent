from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Cart, Order, OrderItem, Product, Transaction
from app.schemas.order import CheckoutRequest
from app.core.security import get_current_user

router = APIRouter()

@router.post("/", response_model=dict)
def process_checkout(
    checkout_data: CheckoutRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Lấy giỏ hàng đang hoạt động của User
    cart = db.query(Cart).filter(Cart.user_id == current_user.user_id, Cart.status == 1).first()
    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Giỏ hàng trống. Không thể đặt hàng.")

    # 2. Tính tổng tiền & Kiểm tra tồn kho nghiêm ngặt
    subtotal = 0
    for item in cart.items:
        # Dùng with_for_update() để khóa row (Lock), tránh lỗi 2 người mua cùng 1 sản phẩm ở cùng 1 thời điểm
        product = db.query(Product).filter(Product.product_id == item.product_id).with_for_update().first()
        if not product or product.quantity < item.quantity:
            raise HTTPException(status_code=400, detail=f"Sản phẩm ID {item.product_id} đã hết hàng hoặc không đủ số lượng.")
        subtotal += float(item.price) * item.quantity

    shipping_fee = 30000.0  # Giả sử phí ship đồng giá 30k
    grand_total = subtotal + shipping_fee

    # 3. Lưu Đơn Hàng (Order)
    new_order = Order(
        user_id=current_user.user_id,
        subtotal=subtotal,
        shipping=shipping_fee,
        total=grand_total,
        grand_total=grand_total,
        first_name=checkout_data.first_name,
        last_name=checkout_data.last_name,
        phone=checkout_data.phone,
        email=checkout_data.email,
        line1=checkout_data.line1,
        city=checkout_data.city,
        province=checkout_data.province,
        status=1,  # 1: Pending (Chờ xác nhận)
        note=checkout_data.note
    )
    db.add(new_order)
    db.flush()  # Đẩy tạm vào CSDL để lấy được new_order.order_id

    # 4. Lưu Chi tiết Đơn Hàng & Trừ Tồn Kho
    for item in cart.items:
        order_item = OrderItem(
            order_id=new_order.order_id,
            product_id=item.product_id,
            sku=item.product.sku if item.product else "",
            price=item.price,
            quantity=item.quantity
        )
        db.add(order_item)
        
        # Trừ tồn kho thực tế
        product = db.query(Product).filter(Product.product_id == item.product_id).first()
        product.quantity -= item.quantity

    # 5. Lưu Giao dịch (Transaction)
    transaction = Transaction(
        order_id=new_order.order_id,
        amount=grand_total,
        mode="COD" if checkout_data.payment_method == 1 else "ONLINE",
        status=2 if checkout_data.payment_method == 1 else 1  # 2: Chờ thanh toán COD
    )
    db.add(transaction)

    # 6. Đóng Giỏ Hàng
    cart.status = 3  # 3: Checked out (Đã lên đơn)

    # 7. Lưu tất cả thay đổi vào Database
    db.commit()

    return {
        "message": "Đặt hàng thành công!",
        "order_id": new_order.order_id,
        "grand_total": grand_total,
        "status": "Pending"
    }