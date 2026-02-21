"""
Script để tạo người dùng Admin và Regular User cho hệ thống
Run: python create_users.py
"""

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User, UserProfile, Role
from app.core.security import get_password_hash
from datetime import datetime


def create_users():
    """Tạo 1 admin user và 1 regular user"""
    db = SessionLocal()
    
    try:
        # Định nghĩa passwords (bcrypt yêu cầu < 72 bytes)
        admin_password = "Admin@123"  # 9 bytes
        user_password = "User@123"    # 8 bytes
        
        # ========== TẠO ADMIN USER ==========
        admin_email = "admin@techshop.com"
        admin_user = db.query(User).filter(User.email == admin_email).first()
        
        if not admin_user:
            print(f"Tạo Admin User: {admin_email}")
            admin_hashed_pass = get_password_hash(admin_password)
            admin_user = User(
                email=admin_email,
                phone="0123456789",
                password=admin_hashed_pass,
                is_admin=True,
                status=1  # active
            )
            db.add(admin_user)
            db.flush()  # Để lấy user_id vừa được generate
            
            # Tạo profile cho admin
            admin_profile = UserProfile(
                user_id=admin_user.user_id,
                first_name="Admin",
                last_name="System",
                avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=admin@techshop.com"
            )
            db.add(admin_profile)
            print(f"✓ Admin User created successfully!")
            print(f"  - Email: {admin_email}")
            print(f"  - Password: {admin_password}")
            print(f"  - User ID: {admin_user.user_id}")
        else:
            print(f"Admin User {admin_email} đã tồn tại!")

        # ========== TẠO REGULAR USER ==========
        user_email = "user@techshop.com"
        regular_user = db.query(User).filter(User.email == user_email).first()
        
        if not regular_user:
            print(f"\nTạo Regular User: {user_email}")
            user_hashed_pass = get_password_hash(user_password)
            regular_user = User(
                email=user_email,
                phone="0987654321",
                password=user_hashed_pass,
                is_admin=False,
                status=1  # active
            )
            db.add(regular_user)
            db.flush()  # Để lấy user_id vừa được generate
            
            # Tạo profile cho regular user
            user_profile = UserProfile(
                user_id=regular_user.user_id,
                first_name="John",
                last_name="Doe",
                avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=user@techshop.com"
            )
            db.add(user_profile)
            print(f"✓ Regular User created successfully!")
            print(f"  - Email: {user_email}")
            print(f"  - Password: {user_password}")
            print(f"  - User ID: {regular_user.user_id}")
        else:
            print(f"Regular User {user_email} đã tồn tại!")

        # Commit tất cả thay đổi
        db.commit()
        print("\n✓ Người dùng đã được tạo thành công!")
        
        # In thông tin chi tiết
        print("\n" + "="*50)
        print("THÔNG TIN ĐăNG NHẬP")
        print("="*50)
        print("\nADMIN:")
        print(f"  Email: {admin_email}")
        print(f"  Password: {admin_password}")
        print("\nREGULAR USER:")
        print(f"  Email: {user_email}")
        print(f"  Password: {user_password}")
        print("="*50)
        
    except Exception as e:
        db.rollback()
        print(f"❌ Lỗi khi tạo người dùng: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_users()
