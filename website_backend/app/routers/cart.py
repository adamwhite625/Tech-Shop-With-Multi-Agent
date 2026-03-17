from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Cart, CartItem, Product, User
from app.schemas.cart import CartResponse, CartItemAdd, CartItemUpdate, CartItemResponse, ProductInCart
from app.core.security import get_current_user

router = APIRouter()

def get_or_create_active_cart(db: Session, user_id: int) -> Cart:
    # Tìm giỏ hàng đang active (status = 1) của user này
    cart = db.query(Cart).filter(Cart.user_id == user_id, Cart.status == 1).first()
    if not cart:
        # Nếu chưa có, tạo giỏ hàng mới
        cart = Cart(user_id=user_id, status=1)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    
    # Force load items and products
    db.refresh(cart, ["items"])
    for item in cart.items:
        db.refresh(item, ["product"])
    
    return cart

def serialize_cart(cart: Cart) -> CartResponse:
    """Convert SQLAlchemy Cart model to Pydantic CartResponse"""
    items = []
    for item in cart.items:
        cart_item_resp = CartItemResponse(
            cart_item_id=item.cart_item_id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=float(item.price),
            product=ProductInCart(
                title=item.product.title,
                thumb=item.product.thumb,
                slug=item.product.slug
            ) if item.product else None
        )
        items.append(cart_item_resp)
    
    return CartResponse(
        cart_id=cart.cart_id,
        user_id=cart.user_id,
        status=cart.status,
        items=items
    )

@router.get("/")
def get_my_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Lấy thông tin giỏ hàng hiện tại của User đang đăng nhập"""
    cart = get_or_create_active_cart(db, current_user.user_id)
    return serialize_cart(cart)

@router.post("/items")
def add_to_cart(
    item_data: CartItemAdd, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Thêm sản phẩm vào giỏ hàng"""
    cart = get_or_create_active_cart(db, current_user.user_id)
    
    # Kiểm tra sản phẩm có tồn tại và đang active không
    product = db.query(Product).filter(Product.product_id == item_data.product_id, Product.status == 1).first()
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại hoặc ngừng kinh doanh.")
        
    if product.quantity < item_data.quantity:
        raise HTTPException(status_code=400, detail="Số lượng tồn kho không đủ.")

    # Kiểm tra xem sản phẩm đã có trong giỏ chưa
    existing_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.cart_id, 
        CartItem.product_id == item_data.product_id
    ).first()

    if existing_item:
        existing_item.quantity += item_data.quantity
    else:
        new_item = CartItem(
            cart_id=cart.cart_id,
            product_id=product.product_id,
            quantity=item_data.quantity,
            price=product.price # Lưu giá tại thời điểm thêm vào giỏ
        )
        db.add(new_item)

    db.commit()
    # Fetch lại cart với eager load products
    cart = get_or_create_active_cart(db, current_user.user_id)
    return serialize_cart(cart)

@router.put("/items/{cart_item_id}")
def update_cart_item_quantity(
    cart_item_id: int,
    item_data: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cập nhật số lượng sản phẩm trong giỏ hàng"""
    cart = get_or_create_active_cart(db, current_user.user_id)
    item = db.query(CartItem).filter(CartItem.cart_item_id == cart_item_id, CartItem.cart_id == cart.cart_id).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Sản phẩm không có trong giỏ.")
    
    # Validate quantity
    if item_data.quantity < 1:
        raise HTTPException(status_code=400, detail="Số lượng phải >= 1")
    
    # Check stock
    product = db.query(Product).filter(Product.product_id == item.product_id).first()
    if product.quantity < item_data.quantity:
        raise HTTPException(status_code=400, detail=f"Chỉ còn {product.quantity} sản phẩm trong kho")
    
    # Update quantity
    item.quantity = item_data.quantity
    db.commit()
    
    # Return updated cart
    cart = get_or_create_active_cart(db, current_user.user_id)
    return serialize_cart(cart)

@router.delete("/items/{cart_item_id}")
def remove_from_cart(
    cart_item_id: int, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Xóa một sản phẩm khỏi giỏ hàng"""
    cart = get_or_create_active_cart(db, current_user.user_id)
    item = db.query(CartItem).filter(CartItem.cart_item_id == cart_item_id, CartItem.cart_id == cart.cart_id).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Sản phẩm không có trong giỏ.")
        
    db.delete(item)
    db.commit()
    # Return updated cart with products
    cart = get_or_create_active_cart(db, current_user.user_id)
    return serialize_cart(cart)