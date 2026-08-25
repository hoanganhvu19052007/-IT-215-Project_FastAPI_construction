from fastapi import Depends, HTTPException, status

from app.dependencies.auth import get_current_user
from app.models.user import User


# Kiểm tra người dùng đã đăng nhập chưa
def require_user(
    current_user: User = Depends(get_current_user),
) -> User:

    # USER và ADMIN đều được phép
    return current_user


# Kiểm tra người dùng có phải ADMIN không
def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:

    # Nếu không phải ADMIN thì từ chối truy cập
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ ADMIN mới có quyền thực hiện thao tác này",
        )

    # Trả về ADMIN hiện tại
    return current_user
