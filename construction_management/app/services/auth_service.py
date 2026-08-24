from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)

from app.services.user_service import UserService


# Service xử lý xác thực và token
class AuthService:

    # Kiểm tra thông tin đăng nhập
    @staticmethod
    def authenticate_user(
        db: Session,
        email: str,
        password: str,
    ) -> User:

        # Tìm user theo email
        user = UserService.get_user_by_email(db, email)

        # Email không tồn tại hoặc mật khẩu sai
        if not user or not verify_password(
            password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email hoặc mật khẩu không đúng",
            )

        # Kiểm tra tài khoản có đang hoạt động không
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tài khoản đã bị vô hiệu hóa",
            )

        # Đăng nhập thành công
        return user

    # Tạo Access Token và Refresh Token
    @staticmethod
    def create_tokens(user: User) -> dict:

        # Tạo Access Token
        # sub = ID của user
        # role = quyền của user
        access_token = create_access_token(
            {
                "sub": str(user.id),
                "role": user.role,
            }
        )

        # Tạo Refresh Token
        refresh_token = create_refresh_token(
            {
                "sub": str(user.id),
                "role": user.role,
            }
        )

        # Trả token về cho client
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token,
        }

    # # Tạo Access Token mới bằng Refresh Token
    # @staticmethod
    # def refresh_access_token(
    #     db: Session,
    #     refresh_token: str,
    # ) -> dict:

    #     # Kiểm tra có gửi refresh token không
    #     if not refresh_token:
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail="refresh_token is required",
    #         )

    #     # Giải mã Refresh Token
    #     data = decode_token(refresh_token)

    #     # Kiểm tra token có hợp lệ và đúng loại refresh không
    #     if not data or data.get("type") != "refresh":
    #         raise HTTPException(
    #             status_code=status.HTTP_401_UNAUTHORIZED,
    #             detail="Invalid refresh token",
    #         )

    #     # Lấy ID user từ token
    #     user_id = data.get("sub")

    #     # Tìm user trong database
    #     user = UserService.get_user_by_id(
    #         db,
    #         int(user_id),
    #     )

    #     # Kiểm tra tài khoản còn hoạt động không
    #     if not user.is_active:
    #         raise HTTPException(
    #             status_code=status.HTTP_403_FORBIDDEN,
    #             detail="User is not active",
    #         )

    #     # Tạo Access Token và Refresh Token mới
    #     return AuthService.create_tokens(user)
