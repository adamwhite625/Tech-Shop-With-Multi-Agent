from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, UserProfile
from app.schemas.user import UserRegister, UserLogin, TokenResponse, UserInfo
from app.core.security import get_password_hash, verify_password, create_access_token

router = APIRouter()

@router.post("/register", response_model=dict)
def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    # 1. Kiểm tra Email đã tồn tại chưa
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email này đã được đăng ký.")

    # 2. Tạo User mới (Mặc định is_admin = False)
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        password=hashed_password,
        phone=user_data.phone,
        is_admin=False, # Mặc định là user thường
        status=1 # Active
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 3. Tạo User Profile đi kèm
    new_profile = UserProfile(
        user_id=new_user.user_id,
        first_name=user_data.first_name,
        last_name=user_data.last_name
    )
    db.add(new_profile)
    db.commit()

    return {"message": "Đăng ký tài khoản thành công!", "user_id": new_user.user_id}


@router.post("/login", response_model=TokenResponse)
def login_user(user_data: UserLogin, db: Session = Depends(get_db)):
    # 1. Tìm user theo email
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng.")

    # 2. Kiểm tra mật khẩu
    if not verify_password(user_data.password, user.password):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng.")

    # 3. Kiểm tra trạng thái tài khoản
    if user.status != 1:
        raise HTTPException(status_code=403, detail="Tài khoản của bạn đã bị khóa hoặc vô hiệu hóa.")

    # 4. Lấy Profile để trả về Frontend
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.user_id).first()
    first_name = profile.first_name if profile else ""
    last_name = profile.last_name if profile else ""

    # 5. Tạo JWT Token (Gói thông tin vào payload)
    access_token_payload = {
        "sub": str(user.user_id),
        "email": user.email,
        "is_admin": user.is_admin
    }
    access_token = create_access_token(data=access_token_payload)

    # 6. Trả về Token và thông tin cơ bản
    return TokenResponse(
        access_token=access_token,
        user=UserInfo(
            user_id=user.user_id,
            email=user.email,
            first_name=first_name,
            last_name=last_name,
            is_admin=user.is_admin
        )
    )


@router.post("/token", response_model=TokenResponse)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2 compatible token endpoint.
    Accepts username (email) and password as form data for Swagger UI authorization.
    """
    # 1. Tìm user theo email
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng.")

    # 2. Kiểm tra mật khẩu
    if not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng.")

    # 3. Kiểm tra trạng thái tài khoản
    if user.status != 1:
        raise HTTPException(status_code=403, detail="Tài khoản của bạn đã bị khóa hoặc vô hiệu hóa.")

    # 4. Lấy Profile để trả về Frontend
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.user_id).first()
    first_name = profile.first_name if profile else ""
    last_name = profile.last_name if profile else ""

    # 5. Tạo JWT Token (Gói thông tin vào payload)
    access_token_payload = {
        "sub": str(user.user_id),
        "email": user.email,
        "is_admin": user.is_admin
    }
    access_token = create_access_token(data=access_token_payload)

    # 6. Trả về Token và thông tin cơ bản
    return TokenResponse(
        access_token=access_token,
        user=UserInfo(
            user_id=user.user_id,
            email=user.email,
            first_name=first_name,
            last_name=last_name,
            is_admin=user.is_admin
        )
    )