from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.core.security import create_access_token, verify_password
from app.services.user_service import UserService


class AuthService:
    @staticmethod
    def authenticate_user(
        db: Session,
        email: str,
        password: str,
    ) -> User:
        """Kiểm tra thông tin đăng nhập"""
        user = UserService.get_user_by_email(db, email)

        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email hoặc mật khẩu không đúng",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tài khoản đã bị vô hiệu hóa",
            )

        return user

    @staticmethod
    def create_tokens(user: User) -> dict:
        """Tạo Access Token cho user"""
        access_token = create_access_token(
            {
                "sub": str(user.id),
                "role": user.role,
            }
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
        }
