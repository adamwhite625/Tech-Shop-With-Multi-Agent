import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import SessionLocal
from app.models import Product, Category, product_categories, ProductMeta

def clean_nan(val):
    """Hàm xử lý các giá trị rỗng (NaN) từ file CSV chuyển thành None cho MySQL"""
    if pd.isna(val):
        return None
    return val

def seed_data():
    db = SessionLocal()
    
    try:
        print("Đang đọc dữ liệu từ file CSV...")
        df_categories = pd.read_csv("data/categories.csv")
        df_products = pd.read_csv("data/products_valid.csv")
        df_product_categories = pd.read_csv("data/product_categories.csv")
        df_product_metas = pd.read_csv("data/product_metas.csv")

        # 0. Clear dữ liệu cũ trước khi seed
        print("0. Đang xóa dữ liệu cũ...")
        db.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        db.execute(text("TRUNCATE TABLE product_metas"))
        db.execute(text("TRUNCATE TABLE product_categories"))
        db.execute(text("TRUNCATE TABLE products"))
        db.execute(text("TRUNCATE TABLE categories"))
        db.execute(text("SET FOREIGN_KEY_CHECKS=1"))
        db.commit()
        print("   Xóa dữ liệu cũ xong!")

        # 1. Nạp dữ liệu Bảng Categories
        print("1. Đang nạp Categories...")
        for _, row in df_categories.iterrows():
            cat = db.query(Category).filter(Category.category_id == row['category_id']).first()
            if not cat:
                new_cat = Category(
                    category_id=row['category_id'],
                    parent_id=clean_nan(row.get('parent_id')),
                    level=clean_nan(row.get('level')),
                    title=clean_nan(row.get('title')),
                    slug=clean_nan(row.get('slug'))
                )
                db.add(new_cat)
        db.commit()

        # 2. Nạp dữ liệu Bảng Products
        print("2. Đang nạp Products...")
        for _, row in df_products.iterrows():
            prod = db.query(Product).filter(Product.product_id == row['product_id']).first()
            if not prod:
                new_prod = Product(
                    product_id=row['product_id'],
                    title=clean_nan(row.get('title')),
                    slug=clean_nan(row.get('slug')),
                    thumb=clean_nan(row.get('thumb')),
                    desc=clean_nan(row.get('desc')),
                    summary=clean_nan(row.get('summary')),
                    price=clean_nan(row.get('price')),
                    quantity=clean_nan(row.get('quantity')) or 100, # Nếu CSV ko có số lượng, mặc định 100
                    status=clean_nan(row.get('status')) or 1,
                    discount=clean_nan(row.get('discount'))
                )
                db.add(new_prod)
        db.commit()

        # 3. Nạp dữ liệu Bảng trung gian Product_Categories (N-N)
        print("3. Đang nạp Product_Categories...")
        for _, row in df_product_categories.iterrows():
            try:
                # Dùng raw SQL execute cho bảng trung gian Table()
                db.execute(product_categories.insert().values(
                    product_id=row['product_id'],
                    category_id=row['category_id']
                ))
            except Exception:
                pass # Bỏ qua nếu đã tồn tại hoặc lỗi khóa ngoại
        db.commit()
        
        # 4. Nạp dữ liệu Bảng Product Metas
        print("4. Đang nạp Product Metas...")
        for _, row in df_product_metas.iterrows():
            try:
                new_meta = ProductMeta(
                    product_id=row['product_id'],
                    key=clean_nan(row.get('key')),
                    content=clean_nan(row.get('content'))
                )
                db.add(new_meta)
            except Exception:
                pass
        db.commit()

        print("✅ Nạp dữ liệu vào MySQL THÀNH CÔNG!")
        
        # In ra một mã sản phẩm để bạn tiện test
        sample_product = db.query(Product).first()
        if sample_product:
            print(f"👉 Hãy dùng product_id: {sample_product.product_id} để test API Giỏ Hàng nhé!")

    except FileNotFoundError as e:
        print(f"❌ Lỗi: Không tìm thấy file CSV. Vui lòng kiểm tra lại thư mục data/. Chi tiết: {e}")
    except Exception as e:
        print(f"❌ Có lỗi xảy ra trong quá trình nạp: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()