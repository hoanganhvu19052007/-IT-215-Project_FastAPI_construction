from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.work_item import WorkItem
from app.models.user import User
from app.models.site import ConstructionSite, SiteMember
from app.schemas.work_item import WorkItemCreate, WorkItemUpdate


class WorkItemService:
    @staticmethod
    def create_work_item(db: Session, payload: WorkItemCreate) -> WorkItem:
        """Tạo hạng mục công việc mới"""
        assignee_id = payload.assignee_id
        if assignee_id and assignee_id > 0:
            assignee = db.query(User).filter(User.id == assignee_id).first()
            if not assignee:
                raise ValueError(f"User với ID {assignee_id} không tồn tại")

            site = (
                db.query(ConstructionSite)
                .filter(ConstructionSite.id == payload.site_id, ConstructionSite.is_deleted == False)
                .first()
            )
            if not site:
                raise ValueError("Công trình không tồn tại")

            is_member = (
                db.query(SiteMember)
                .filter(
                    SiteMember.site_id == payload.site_id,
                    SiteMember.user_id == assignee_id,
                )
                .first()
            )

            if assignee.id != site.owner_id and not is_member:
                raise ValueError("Người được giao việc phải là thành viên hoặc owner của công trình")
        else:
            assignee_id = None

        work_item = WorkItem(
            site_id=payload.site_id,
            title=payload.title,
            description=payload.description,
            assignee_id=assignee_id,
            priority=payload.priority,
            due_date=payload.due_date,
            status="TODO",
        )
        db.add(work_item)
        db.commit()
        db.refresh(work_item)
        return work_item

    @staticmethod
    def get_work_item_by_id(db: Session, item_id: int) -> Optional[WorkItem]:
        """Lấy chi tiết hạng mục công việc"""
        return db.query(WorkItem).filter(WorkItem.id == item_id).first()

    @staticmethod
    def list_work_items_by_site(
        db: Session,
        site_id: int,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assignee_id: Optional[int] = None,
    ) -> list[WorkItem]:
        """Lấy danh sách hạng mục đơn giản của một công trình"""
        query = db.query(WorkItem).filter(WorkItem.site_id == site_id)
        if status:
            query = query.filter(WorkItem.status == status)
        if priority:
            query = query.filter(WorkItem.priority == priority)
        if assignee_id:
            query = query.filter(WorkItem.assignee_id == assignee_id)
        return query.all()

    @staticmethod
    def list_work_items_by_site_with_filters(
        db: Session,
        site_id: int,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assignee_id: Optional[int] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        order: str = "desc",
        limit: int = 10,
        offset: int = 0,
    ) -> list[WorkItem]:
        """Lấy danh sách hạng mục công việc với filter, search, sort và pagination"""
        query = db.query(WorkItem).filter(WorkItem.site_id == site_id)

        if status:
            query = query.filter(WorkItem.status == status)
        if priority:
            query = query.filter(WorkItem.priority == priority)
        if assignee_id is not None:
            query = query.filter(WorkItem.assignee_id == assignee_id)
        if search:
            query = query.filter(WorkItem.title.ilike(f"%{search}%"))

        # Sắp xếp
        if sort_by == "due_date":
            sort_col = WorkItem.due_date
        elif sort_by == "priority":
            sort_col = WorkItem.priority
        else:
            sort_col = WorkItem.created_at

        if order == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())

        return query.limit(limit).offset(offset).all()

    @staticmethod
    def list_work_items_assigned_to_user_with_filters(
        db: Session,
        user_id: int,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        sort_by: str = "created_at",
        order: str = "desc",
        limit: int = 10,
        offset: int = 0,
    ) -> list[WorkItem]:
        """Lấy danh sách công việc được giao cho user với filter, sort và pagination"""
        query = db.query(WorkItem).filter(WorkItem.assignee_id == user_id)

        if status:
            query = query.filter(WorkItem.status == status)
        if priority:
            query = query.filter(WorkItem.priority == priority)

        if sort_by == "due_date":
            sort_col = WorkItem.due_date
        elif sort_by == "priority":
            sort_col = WorkItem.priority
        else:
            sort_col = WorkItem.created_at

        if order == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())

        return query.limit(limit).offset(offset).all()

    @staticmethod
    def update_work_item(db: Session, item_id: int, payload: WorkItemUpdate) -> Optional[WorkItem]:
        """Cập nhật hạng mục công việc"""
        work_item = WorkItemService.get_work_item_by_id(db, item_id)
        if not work_item:
            return None

        if payload.title is not None:
            work_item.title = payload.title
        if payload.description is not None:
            work_item.description = payload.description

        if payload.assignee_id is not None:
            if payload.assignee_id > 0:
                assignee = db.query(User).filter(User.id == payload.assignee_id).first()
                if not assignee:
                    raise ValueError(f"User với ID {payload.assignee_id} không tồn tại")

                site = (
                    db.query(ConstructionSite)
                    .filter(ConstructionSite.id == work_item.site_id, ConstructionSite.is_deleted == False)
                    .first()
                )

                if site:
                    is_member = (
                        db.query(SiteMember)
                        .filter(
                            SiteMember.site_id == work_item.site_id,
                            SiteMember.user_id == payload.assignee_id,
                        )
                        .first()
                    )

                    if assignee.id != site.owner_id and not is_member:
                        raise ValueError("Người được giao việc phải là thành viên hoặc owner của công trình")

                work_item.assignee_id = payload.assignee_id
            else:
                work_item.assignee_id = None

        if payload.status is not None:
            work_item.status = payload.status
        if payload.priority is not None:
            work_item.priority = payload.priority
        if payload.due_date is not None:
            work_item.due_date = payload.due_date

        db.commit()
        db.refresh(work_item)
        return work_item

    @staticmethod
    def delete_work_item(db: Session, item_id: int) -> bool:
        """Xóa hạng mục công việc"""
        work_item = WorkItemService.get_work_item_by_id(db, item_id)
        if not work_item:
            return False

        db.delete(work_item)
        db.commit()
        return True

    @staticmethod
    def update_work_item_status(db: Session, item_id: int, status: str) -> Optional[WorkItem]:
        """Cập nhật trạng thái hạng mục công việc"""
        work_item = WorkItemService.get_work_item_by_id(db, item_id)
        if not work_item:
            return None

        work_item.status = status
        db.commit()
        db.refresh(work_item)
        return work_item
