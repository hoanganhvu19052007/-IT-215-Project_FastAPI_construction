from sqlalchemy.orm import Session
from datetime import datetime

from app.models.work_item import WorkItem
from app.schemas.work_item import WorkItemCreate, WorkItemUpdate


class WorkItemService:
    @staticmethod
    def create_work_item(db: Session, payload: WorkItemCreate):
        """Tạo hạng mục công việc mới"""
        work_item = WorkItem(
            site_id=payload.site_id,
            title=payload.title,
            description=payload.description,
            assignee_id=payload.assignee_id,
            priority=payload.priority,
            due_date=payload.due_date,
        )
        db.add(work_item)
        db.commit()
        db.refresh(work_item)
        return work_item

    @staticmethod
    def get_work_item_by_id(db: Session, item_id: int):
        """Lấy chi tiết hạng mục công việc"""
        return db.query(WorkItem).filter(WorkItem.id == item_id).first()

    @staticmethod
    def list_work_items_by_site(db: Session, site_id: int):
        """Lấy danh sách hạng mục công việc của một công trình"""
        return db.query(WorkItem).filter(WorkItem.site_id == site_id).all()

    @staticmethod
    def list_work_items_assigned_to_user(db: Session, user_id: int):
        """Lấy danh sách hạng mục công việc được giao cho user"""
        return db.query(WorkItem).filter(WorkItem.assignee_id == user_id).all()

    @staticmethod
    def update_work_item(db: Session, item_id: int, payload: WorkItemUpdate):
        """Cập nhật hạng mục công việc"""
        work_item = WorkItemService.get_work_item_by_id(db, item_id)
        if not work_item:
            return None
        
        if payload.title is not None:
            work_item.title = payload.title
        if payload.description is not None:
            work_item.description = payload.description
        if payload.assignee_id is not None:
            work_item.assignee_id = payload.assignee_id
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
    def delete_work_item(db: Session, item_id: int):
        """Xóa hạng mục công việc"""
        work_item = WorkItemService.get_work_item_by_id(db, item_id)
        if not work_item:
            return False
        
        db.delete(work_item)
        db.commit()
        return True

    @staticmethod
    def update_work_item_status(db: Session, item_id: int, status: str):
        """Cập nhật trạng thái hạng mục công việc"""
        work_item = WorkItemService.get_work_item_by_id(db, item_id)
        if not work_item:
            return None
        
        work_item.status = status
        db.commit()
        db.refresh(work_item)
        return work_item
