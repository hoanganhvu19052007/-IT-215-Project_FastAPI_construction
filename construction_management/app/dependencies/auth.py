from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.database import get_db
from app.models.user import User

# Lấy JWT từ header:
# Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# Lấy thông tin user đang đăng nhập
def get_current_user(
    # Lấy token từ Authorization header
    token: str = Depends(oauth2_scheme),
    # Kết nối database
    db: Session = Depends(get_db),
) -> User:

    # Giải mã và kiểm tra JWT
    data = decode_token(token)

    # Token không hợp lệ hoặc đã hết hạn
    if not data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Chỉ cho phép Access Token truy cập API
    if data.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Lấy user ID từ token
    user_id = data.get("sub")

    # Token không có user ID
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không chứa user ID",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Chuyển user ID từ string sang số
    try:
        user_id = int(user_id)

    # User ID không đúng định dạng
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID không hợp lệ",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Tìm user trong database
    user = db.query(User).filter(User.id == user_id).first()

    # Không tìm thấy user
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Không tìm thấy người dùng",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Kiểm tra tài khoản có đang hoạt động không
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hóa",
        )

    # Trả về user hiện tại
    return user
