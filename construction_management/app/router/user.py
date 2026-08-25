from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.permission import require_admin
from app.models.user import User
from app.schemas.user import UserResponse
from app.services.user_service import UserService

# Tạo router cho API User
router = APIRouter(
    prefix="/users",
    tags=["users"],
)


# Lấy thông tin tài khoản hiện tại
@router.get(
    "/me",
    response_model=UserResponse,
)
def get_current_user_profile(
    # Kiểm tra user đã đăng nhập
    current_user: User = Depends(get_current_user),
):
    # USER và ADMIN đều được xem tài khoản của mình
    return current_user


# Lấy danh sách tất cả User (Chỉ Admin, hỗ trợ search theo tên/email và trạng thái)
@router.get(
    "",
    response_model=list[UserResponse],
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
    users = UserService.list_all_users(db, search=search, is_active=is_active)
    return users


# Lấy thông tin một User theo ID
# @router.get(
#     "/{user_id}",
#     response_model=UserResponse,
# )
# def get_user(
#     # ID của user cần tìm
#     user_id: int,
#     # Kết nối database
#     db: Session = Depends(get_db),
#     # Chỉ ADMIN được phép truy cập
#     current_user: User = Depends(require_admin),
# ):
#     # Tìm user theo ID
#     user = UserService.get_user_by_id(
#         db,
#         user_id,
#     )

#     return user
