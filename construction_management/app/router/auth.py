from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.user import UserResponse
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
    return UserService.create_user(db, payload)


# API đăng nhập
@router.post(
    "/login",
    response_model=Token,
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Đăng nhập và cấp JWT access token:
    - Kiểm tra email và password
    - Tạo access token
    """
    user = AuthService.authenticate_user(
        db,
        payload.email,
        payload.password,
    )

    return AuthService.create_tokens(user)
