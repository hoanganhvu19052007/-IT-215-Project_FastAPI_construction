from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.database import Base


class ConstructionSite(Base):
    __tablename__ = "construction_sites"
    # Khóa chính
    id = Column(Integer, primary_key=True, index=True)

    # Tên công trình (không vượt 255 ký tự)
    name = Column(String(255), nullable=False)

    # Mô tả công trình
    description = Column(Text, nullable=True)

    # Một User có thể sở hữu nhiều công trình
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Soft delete
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime, nullable=True)

    # Thời gian tạo công trình
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Công trình thuộc về một User
    owner = relationship("User", back_populates="owned_sites", foreign_keys=[owner_id])

    # Một công trình có nhiều thành viên
    members = relationship(
        "SiteMember", back_populates="site", cascade="all, delete-orphan"
    )

    # Một công trình có nhiều hạng mục
    work_items = relationship(
        "WorkItem", back_populates="site", cascade="all, delete-orphan"
    )


class SiteMember(Base):
    __tablename__ = "site_members"
    # ID công trình
    site_id = Column(Integer, ForeignKey("construction_sites.id"), primary_key=True)
    # ID người dùng
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    # Vai trò của User trong công trình
    # OWNER / MEMBER
    role = Column(String(20), nullable=False)
    # Thời gian tham gia công trình
    joined_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    # SiteMember -> ConstructionSite
    site = relationship("ConstructionSite", back_populates="members")
    # SiteMember -> User
    user = relationship("User", back_populates="site_memberships")
