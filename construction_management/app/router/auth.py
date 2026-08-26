from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.user import UserResponse
from app.schemas.auth import RegisterRequest, LoginRequest, Token
from app.schemas.common import ErrorResponse
from app.services.user_service import UserService
from app.services.auth_service import AuthService

# Router cho các API xác thực
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản người dùng mới",
    description="""
Tạo tài khoản người dùng mới trong hệ thống.
* **email**: Phải là email hợp lệ và chưa từng đăng ký.
* **password**: Mật khẩu tối thiểu 6 ký tự (sẽ được mã hóa bảo mật bằng bcrypt).
* **full_name**: Họ và tên người dùng.
""",
    responses={
        201: {"description": "Đăng ký thành công, trả về thông tin user (không kèm mật khẩu)"},
        400: {"model": ErrorResponse, "description": "Email đã được sử dụng"},
        422: {"model": ErrorResponse, "description": "Dữ liệu đầu vào không đúng định dạng"},
    },
)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
):
    return UserService.create_user(db, payload)


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Đăng nhập hệ thống & Cấp JWT Token",
    description="""
Xác thực người dùng bằng email và mật khẩu.
* Trả về JWT `access_token` dạng `bearer`.
* Sử dụng token này để dán vào Authorization header khi gọi các API cần bảo mật.
""",
    responses={
        200: {"description": "Đăng nhập thành công, nhận Access Token"},
        401: {"model": ErrorResponse, "description": "Email hoặc mật khẩu không đúng"},
        403: {"model": ErrorResponse, "description": "Tài khoản đã bị vô hiệu hóa"},
        422: {"model": ErrorResponse, "description": "Dữ liệu đầu vào không đúng định dạng"},
    },
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    user = AuthService.authenticate_user(
        db,
        payload.email,
        payload.password,
    )

    return AuthService.create_tokens(user)
