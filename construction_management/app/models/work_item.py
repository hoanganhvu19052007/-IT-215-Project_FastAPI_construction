from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.database import Base


# Model quản lý công việc tại công trường
class WorkItem(Base):

    # Tên bảng trong database
    __tablename__ = "work_items"

    # ID công việc
    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # ID công trường mà công việc thuộc về
    site_id = Column(
        Integer,
        ForeignKey("construction_sites.id"),
        nullable=False,
    )

    # Tên công việc
    title = Column(
        String(255),
        nullable=False,
    )

    # Mô tả công việc
    description = Column(
        Text,
        nullable=True,
    )

    # ID người được giao công việc
    # Có thể để trống nếu chưa giao cho ai
    assignee_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
    )

    # Trạng thái công việc
    # Mặc định là TODO
    status = Column(
        String(20),
        nullable=False,
        default="TODO",
    )

    # Mức độ ưu tiên
    # Mặc định là MEDIUM
    priority = Column(
        String(20),
        nullable=False,
        default="MEDIUM",
    )

    # Hạn hoàn thành công việc
    due_date = Column(
        DateTime,
        nullable=True,
    )

    # Thời gian tạo công việc
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    # Quan hệ với công trường
    site = relationship(
        "ConstructionSite",
        back_populates="work_items",
    )

    # Quan hệ với User được giao việc
    assignee = relationship(
        "User",
        back_populates="assigned_work_items",
    )
