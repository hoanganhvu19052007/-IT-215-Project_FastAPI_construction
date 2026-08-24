from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Dict
from fastapi.security import OAuth2PasswordRequestForm

from app.db.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import RegisterRequest, LoginRequest, Token
from app.services.user_service import UserService
from app.services.auth_service import AuthService

# Tạo router cho các API xác thực
router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


# API đăng ký tài khoản
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Đăng ký tài khoản mới:
    - Kiểm tra email đã tồn tại
    - Hash mật khẩu
    - Lưu user vào database
    """

    # Gọi service để tạo user
    return UserService.create_user(db, payload)


# API đăng nhập
@router.post(
    "/login",
    response_model=Token,
)
def login(
    # Nhận username và password từ form đăng nhập
    payload: OAuth2PasswordRequestForm = Depends(),
    # Kết nối database
    db: Session = Depends(get_db),
):
    """
    Đăng nhập và cấp JWT token:
    - Kiểm tra username và password
    - Tạo access token và refresh token
    """

    # Kiểm tra thông tin đăng nhập
    user = AuthService.authenticate_user(
        db,
        payload.username,
        payload.password,
    )

    # Tạo token cho user
    return AuthService.create_tokens(user)
