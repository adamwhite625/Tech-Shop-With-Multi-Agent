from pydantic import BaseModel, EmailStr
from typing import Optional

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None

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