from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.core.security import hash_password


# Service xử lý các nghiệp vụ liên quan đến User
class UserService:

    # Tạo User mới
    @staticmethod
    def create_user(
        db: Session,
        payload: UserCreate,
    ) -> User:

        # Kiểm tra email đã tồn tại chưa
        existing = db.query(User).filter(User.email == payload.email).first()

        # Nếu email đã tồn tại thì báo lỗi
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email đã được sử dụng",
            )

        # Tạo User mới
        # Password phải được hash trước khi lưu
        user = User(
            email=payload.email,
            full_name=payload.full_name,
            password_hash=hash_password(payload.password),
        )

        # Thêm User vào database
        db.add(user)

        # Lưu thay đổi
        db.commit()

        # Lấy lại dữ liệu User sau khi lưu
        db.refresh(user)

        return user

    # Tìm User theo ID
    @staticmethod
    def get_user_by_id(
        db: Session,
        user_id: int,
    ) -> User:

        # Tìm User trong database
        user = db.query(User).filter(User.id == user_id).first()

        # Không tìm thấy User
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return user

    # Tìm User theo email
    @staticmethod
    def get_user_by_email(
        db: Session,
        email: str,
    ) -> User:

        # Tìm User theo email
        user = db.query(User).filter(User.email == email).first()

        return user

    # Lấy danh sách tất cả User
    @staticmethod
    def list_all_users(
        db: Session,
    ) -> list[User]:

        return db.query(User).all()

    # Cập nhật thông tin User
    @staticmethod
    def update_user(
        db: Session,
        user_id: int,
        payload: UserUpdate,
    ) -> User:

        # Tìm User cần cập nhật
        user = UserService.get_user_by_id(
            db,
            user_id,
        )

        # Nếu có full_name thì cập nhật
        if payload.full_name is not None:
            user.full_name = payload.full_name

        # Nếu có is_active thì cập nhật trạng thái
        if payload.is_active is not None:
            user.is_active = payload.is_active

        # Lưu thay đổi vào database
        db.add(user)
        db.commit()

        # Lấy lại User sau khi cập nhật
        db.refresh(user)

        return user
