from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
import re

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str
    last_name: str
    phone: Optional[str] = None

    @validator('password')
    def validate_password(cls, v):
        """
        Validate password strength:
        - At least 8 characters
        - At least one uppercase letter
        - At least one number
        """
        if len(v) < 8:
            raise ValueError('Mật khẩu phải có ít nhất 8 ký tự')
        if not any(c.isupper() for c in v):
            raise ValueError('Mật khẩu phải chứa chữ hoa (A-Z)')
        if not any(c.isdigit() for c in v):
            raise ValueError('Mật khẩu phải chứa số (0-9)')
        return v

class UserInfo(BaseModel):
    user_id: int
    email: str
    first_name: str
    last_name: str
    is_admin: bool

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in_days: int = 7
    user: UserInfo