from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Numeric, SmallInteger, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# =========================
# BẢNG TRUNG GIAN (N-N)
# =========================
user_roles = Table(
    'user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.user_id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.role_id'), primary_key=True)
)

product_categories = Table(
    'product_categories', Base.metadata,
    Column('product_id', Integer, ForeignKey('products.product_id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.category_id'), primary_key=True)
)

product_tags = Table(
    'product_tags', Base.metadata,
    Column('product_id', Integer, ForeignKey('products.product_id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.tag_id'), primary_key=True)
)

# =========================
# 1. USER & PROFILE
# =========================
class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20))
    password = Column(String(255), nullable=False)
    salt = Column(String(255))
    is_admin = Column(Boolean, default=False)
    status = Column(SmallInteger, default=1) # 1: active, 2: inactive, 3: suspend, 4: banned
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)

    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    carts = relationship("Cart", back_populates="user")
    orders = relationship("Order", back_populates="user")

class UserProfile(Base):
    __tablename__ = "user_profiles"
    user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    first_name = Column(String(150))
    middle_name = Column(String(150))
    last_name = Column(String(150))
    avatar = Column(String(255))
    profile = Column(Text)
    registered_at = Column(DateTime, default=func.now())
    last_login = Column(DateTime)

    user = relationship("User", back_populates="profile")

class Role(Base):
    __tablename__ = "roles"
    role_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False)
    desc = Column(Text)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(Integer)
    updated_by = Column(Integer)

    users = relationship("User", secondary=user_roles, back_populates="roles")

# =========================
# 2. BLOG & CATEGORY
# =========================
class Category(Base):
    __tablename__ = "categories"
    category_id = Column(Integer, primary_key=True, autoincrement=True)
    parent_id = Column(Integer, ForeignKey('categories.category_id'), nullable=True)
    level = Column(Integer, default=1)
    title = Column(String(150))
    meta_title = Column(String(150))
    slug = Column(String(150))
    desc = Column(Text)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(Integer)
    updated_by = Column(Integer)

    products = relationship("Product", secondary=product_categories, back_populates="categories")
    sub_categories = relationship("Category") # Cho phép lấy danh mục con

# =========================
# 3. PRODUCT & META & TAG
# =========================
class Product(Base):
    __tablename__ = "products"
    product_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(150))
    meta_title = Column(String(150))
    slug = Column(String(150))
    thumb = Column(String(255))
    desc = Column(Text)
    summary = Column(Text)
    type = Column(String(150))
    sku = Column(String(150))
    price = Column(Numeric(12, 2))
    quantity = Column(Integer)
    published_at = Column(DateTime)
    status = Column(SmallInteger, default=1) # 1:active, 2:out_of_stock...
    discount = Column(Numeric(12, 2))
    starts_at = Column(DateTime)
    ends_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(Integer)
    updated_by = Column(Integer)

    categories = relationship("Category", secondary=product_categories, back_populates="products")
    tags = relationship("Tag", secondary=product_tags, back_populates="products")
    metas = relationship("ProductMeta", back_populates="product")
    cart_items = relationship("CartItem", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")

class ProductMeta(Base):
    __tablename__ = "product_metas"
    meta_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.product_id'))
    key = Column(String(150))
    content = Column(Text)

    product = relationship("Product", back_populates="metas")

class Tag(Base):
    __tablename__ = "tags"
    tag_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(150))
    meta_title = Column(String(150))
    slug = Column(String(150))
    desc = Column(Text)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(Integer)
    updated_by = Column(Integer)

    products = relationship("Product", secondary=product_tags, back_populates="tags")

# =========================
# 4. CART & ORDER
# =========================
class Cart(Base):
    __tablename__ = "carts"
    cart_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    first_name = Column(String(150))
    middle_name = Column(String(150))
    last_name = Column(String(150))
    phone = Column(String(20))
    email = Column(String(100))
    line1 = Column(String(255))
    line2 = Column(String(255))
    city = Column(String(255))
    province = Column(String(255))
    country = Column(String(255))
    status = Column(SmallInteger, default=1) # 1:active, 2:checkout_in_progress, 3:checked_out
    note = Column(String(255))
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(Integer)
    updated_by = Column(Integer)

    user = relationship("User", back_populates="carts")
    items = relationship("CartItem", back_populates="cart")

class CartItem(Base):
    __tablename__ = "cart_items"
    cart_item_id = Column(Integer, primary_key=True, autoincrement=True)
    cart_id = Column(Integer, ForeignKey('carts.cart_id'))
    product_id = Column(Integer, ForeignKey('products.product_id'))
    sku = Column(String(150))
    is_active = Column(Boolean, default=True)
    price = Column(Numeric(12, 2))
    quantity = Column(Integer)
    discount = Column(Numeric(12, 2))
    note = Column(String(255))

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product", back_populates="cart_items")

class Order(Base):
    __tablename__ = "orders"
    order_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    subtotal = Column(Numeric(12, 2))
    tax = Column(Numeric(12, 2))
    shipping = Column(Numeric(12, 2))
    total = Column(Numeric(12, 2))
    discount_total = Column(Numeric(12, 2))
    promo = Column(String(255))
    discount = Column(Numeric(12, 2))
    grand_total = Column(Numeric(12, 2))
    first_name = Column(String(150))
    middle_name = Column(String(150))
    last_name = Column(String(150))
    phone = Column(String(20))
    email = Column(String(100))
    line1 = Column(String(255))
    line2 = Column(String(255))
    city = Column(String(255))
    province = Column(String(255))
    country = Column(String(255))
    orders_at = Column(DateTime, default=func.now())
    status = Column(SmallInteger, default=1) # 1:pending_payment, 2:paid...
    note = Column(String(255))
    version = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(Integer)
    updated_by = Column(Integer)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    transactions = relationship("Transaction", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    order_item_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('orders.order_id'))
    product_id = Column(Integer, ForeignKey('products.product_id'))
    sku = Column(String(150))
    is_active = Column(Boolean, default=True)
    price = Column(Numeric(12, 2))
    quantity = Column(Integer)
    discount = Column(Numeric(12, 2))
    note = Column(String(255))

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

# =========================
# 5. TRANSACTION & PARAMETER
# =========================
class Transaction(Base):
    __tablename__ = "transactions"
    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('orders.order_id'))
    amount = Column(Numeric(12, 2))
    content = Column(Text)
    code = Column(String(255))
    type = Column(SmallInteger, default=1)
    mode = Column(String(150))
    status = Column(SmallInteger, default=1)
    version = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(Integer)
    updated_by = Column(Integer)

    order = relationship("Order", back_populates="transactions")

class Config(Base):
    __tablename__ = "configs"
    key = Column(String(100), primary_key=True)
    value = Column(String(255))
    type = Column(SmallInteger)
    desc = Column(String(255))
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())