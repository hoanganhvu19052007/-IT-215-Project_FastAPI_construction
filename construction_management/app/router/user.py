from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.permission import require_admin
from app.models.user import User
from app.schemas.user import UserResponse
from app.schemas.common import ErrorResponse
from app.services.user_service import UserService

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Lấy thông tin tài khoản hiện tại",
    description="""
Trả về thông tin hồ sơ của tài khoản đang đăng nhập dựa trên JWT token được gửi kèm trong header.
* Yêu cầu: Đã đăng nhập (tất cả vai trò USER và ADMIN).
""",
    responses={
        200: {"description": "Lấy thông tin thành công"},
        401: {"model": ErrorResponse, "description": "Token không hợp lệ hoặc đã hết hạn"},
        403: {"model": ErrorResponse, "description": "Tài khoản đã bị vô hiệu hóa"},
    },
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.get(
    "",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Lấy danh sách người dùng (Chỉ ADMIN)",
    description="""
Lấy danh sách toàn bộ người dùng trong hệ thống.
* **search**: Lọc tìm kiếm theo họ tên hoặc email.
* **is_active**: Lọc theo trạng thái hoạt động (true/false).
* **Quyền hạn**: Chỉ quản trị viên (ADMIN) mới có quyền gọi API này.
""",
    responses={
        200: {"description": "Lấy danh sách người dùng thành công"},
        401: {"model": ErrorResponse, "description": "Token không hợp lệ hoặc đã hết hạn"},
        403: {"model": ErrorResponse, "description": "Không có quyền ADMIN"},
    },
)
@router.get(
    "/",
    response_model=list[UserResponse],
    include_in_schema=False,
)
def list_users(
    search: str | None = None,
    is_active: bool | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return UserService.list_all_users(db, search=search, is_active=is_active)
