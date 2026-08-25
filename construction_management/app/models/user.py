from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class User(Base):
    __tablename__ = "users"
    # Khóa chính
    id = Column(Integer, primary_key=True, index=True)

    # Email đăng nhập
    email = Column(String(255), unique=True, nullable=False, index=True)

    # Mật khẩu đã được hash
    password_hash = Column(String(255), nullable=False)

    # Họ và tên
    full_name = Column(String(100), nullable=False)

    # Vai trò tài khoản
    role = Column(String(20), nullable=False, default="USER")

    # Trạng thái tài khoản
    is_active = Column(Boolean, nullable=False, default=True)

    # Thời gian tạo tài khoản
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Một user có thể sở hữu nhiều công trình
    owned_sites = relationship(
        "ConstructionSite",
        back_populates="owner",
        foreign_keys="[ConstructionSite.owner_id]",
    )

    # User N-N ConstructionSite
    # Thông qua bảng SiteMember
    site_memberships = relationship(
        "SiteMember", back_populates="user", cascade="all, delete-orphan"
    )

    # User 1-N WorkItem
    # Một user có thể được giao nhiều hạng mục
    assigned_work_items = relationship("WorkItem", back_populates="assignee")
