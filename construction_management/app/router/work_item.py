from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.site import ConstructionSite
from app.schemas.work_item import (
    WorkItemCreate,
    WorkItemUpdate,
    WorkItemResponse,
)
from app.services.site_service import SiteService
from app.services.work_item_service import WorkItemService

# Tạo router cho API WorkItem
router = APIRouter(
    prefix="/work-items",
    tags=["work_items"],
)


# Tạo hạng mục công việc mới
@router.post(
    "/",
    response_model=WorkItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_work_item(
    payload: WorkItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tạo hạng mục công việc mới"""
    # Kiểm tra công trình tồn tại
    site = SiteService.get_site_by_id(db, payload.site_id)
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Công trình không tồn tại",
        )
    
    # Kiểm tra user có quyền tạo công việc trong công trình này không
    # Chỉ chủ công trình hoặc thành viên mới được tạo
    if site.owner_id != current_user.id:
        # Kiểm tra user có phải là thành viên không
        member = db.query(
            db.query(ConstructionSite.members).filter(
                ConstructionSite.id == payload.site_id
            ).exists()
        ).scalar()
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền tạo công việc trong công trình này",
            )
    
    return WorkItemService.create_work_item(db, payload)


# Lấy chi tiết hạng mục công việc
@router.get(
    "/{item_id}",
    response_model=WorkItemResponse,
)
def get_work_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lấy chi tiết hạng mục công việc"""
    work_item = WorkItemService.get_work_item_by_id(db, item_id)
    if not work_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hạng mục công việc không tồn tại",
        )
    return work_item


# Lấy danh sách hạng mục công việc của công trình
@router.get(
    "/site/{site_id}",
    response_model=list[WorkItemResponse],
)
def list_work_items_by_site(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lấy danh sách hạng mục công việc của một công trình"""
    site = SiteService.get_site_by_id(db, site_id)
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Công trình không tồn tại",
        )
    
    return WorkItemService.list_work_items_by_site(db, site_id)


# Lấy danh sách công việc được giao cho user
@router.get(
    "/my-tasks",
    response_model=list[WorkItemResponse],
)
def get_my_assigned_work_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lấy danh sách hạng mục công việc được giao cho user"""
    return WorkItemService.list_work_items_assigned_to_user(db, current_user.id)


# Cập nhật hạng mục công việc
@router.patch(
    "/{item_id}",
    response_model=WorkItemResponse,
)
def update_work_item(
    item_id: int,
    payload: WorkItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cập nhật hạng mục công việc"""
    work_item = WorkItemService.get_work_item_by_id(db, item_id)
    if not work_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hạng mục công việc không tồn tại",
        )
    
    # Kiểm tra quyền: chỉ chủ công trình hoặc người được giao việc mới được cập nhật
    site = SiteService.get_site_by_id(db, work_item.site_id)
    if site.owner_id != current_user.id and work_item.assignee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền cập nhật công việc này",
        )
    
    return WorkItemService.update_work_item(db, item_id, payload)


# Xóa hạng mục công việc
@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_work_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Xóa hạng mục công việc (chỉ chủ công trình)"""
    work_item = WorkItemService.get_work_item_by_id(db, item_id)
    if not work_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hạng mục công việc không tồn tại",
        )
    
    site = SiteService.get_site_by_id(db, work_item.site_id)
    if site.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ chủ công trình mới được phép xóa công việc",
        )
    
    WorkItemService.delete_work_item(db, item_id)


# Cập nhật trạng thái công việc
@router.patch(
    "/{item_id}/status",
    response_model=WorkItemResponse,
)
def update_work_item_status(
    item_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cập nhật trạng thái công việc"""
    work_item = WorkItemService.get_work_item_by_id(db, item_id)
    if not work_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hạng mục công việc không tồn tại",
        )
    
    # Kiểm tra quyền
    site = SiteService.get_site_by_id(db, work_item.site_id)
    if site.owner_id != current_user.id and work_item.assignee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền cập nhật trạng thái công việc này",
        )
    
    return WorkItemService.update_work_item_status(db, item_id, status)
