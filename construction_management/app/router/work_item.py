from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.site import ConstructionSite, SiteMember
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
    """
    Tạo hạng mục công việc mới

    **Quyền:** Chỉ owner hoặc member của site
    """
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
        member = (
            db.query(SiteMember)
            .filter(
                SiteMember.site_id == payload.site_id,
                SiteMember.user_id == current_user.id,
            )
            .first()
        )
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền tạo công việc trong công trình này",
            )

    return WorkItemService.create_work_item(db, payload)


# Lấy danh sách hạng mục công việc của công trình với search & filter & pagination & sort
@router.get(
    "/construction-sites/{site_id}/work-items",
    response_model=list[WorkItemResponse],
)
def list_work_items_by_site(
    site_id: int,
    status: Optional[str] = Query(
        None, regex="^(TODO|IN_PROGRESS|DONE)$", description="Lọc theo trạng thái"
    ),
    priority: Optional[str] = Query(
        None, regex="^(LOW|MEDIUM|HIGH)$", description="Lọc theo mức độ ưu tiên"
    ),
    assignee_id: Optional[int] = Query(
        None, description="Lọc theo người được giao việc"
    ),
    search: Optional[str] = Query(
        None, min_length=1, max_length=255, description="Tìm kiếm theo title"
    ),
    sort_by: str = Query(
        "created_at",
        regex="^(created_at|due_date|priority)$",
        description="Sắp xếp theo",
    ),
    order: str = Query("desc", regex="^(asc|desc)$", description="Thứ tự sắp xếp"),
    limit: int = Query(10, ge=1, le=100, description="Số kết quả trên 1 trang"),
    offset: int = Query(0, ge=0, description="Số bản ghi bỏ qua"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lấy danh sách hạng mục công việc của một công trình với đầy đủ tính năng:

    **Tính năng:**
    - Filter theo status, priority, assignee
    - Search theo title
    - Pagination (limit/offset)
    - Sort theo created_at/due_date/priority

    **Quyền:** Owner hoặc member của site
    """
    # Kiểm tra công trình tồn tại
    site = SiteService.get_site_by_id(db, site_id)
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Công trình không tồn tại",
        )

    # Kiểm tra user có quyền truy cập site
    if site.owner_id != current_user.id:
        member = (
            db.query(SiteMember)
            .filter(
                SiteMember.site_id == site_id, SiteMember.user_id == current_user.id
            )
            .first()
        )
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền truy cập công trình này",
            )

    # Gọi service với tất cả các filter
    work_items = WorkItemService.list_work_items_by_site_with_filters(
        db=db,
        site_id=site_id,
        status=status,
        priority=priority,
        assignee_id=assignee_id,
        search=search,
        sort_by=sort_by,
        order=order,
        limit=limit,
        offset=offset,
    )

    return work_items


# Lấy chi tiết hạng mục công việc
@router.get(
    "/work-items/{item_id}",
    response_model=WorkItemResponse,
)
def get_work_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lấy chi tiết hạng mục công việc

    **Quyền:** Owner/member/assignee của site
    """
    work_item = WorkItemService.get_work_item_by_id(db, item_id)
    if not work_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hạng mục công việc không tồn tại",
        )

    # Kiểm tra quyền truy cập
    site = work_item.site
    if site.owner_id != current_user.id:
        member = (
            db.query(SiteMember)
            .filter(
                SiteMember.site_id == site.id, SiteMember.user_id == current_user.id
            )
            .first()
        )
        if not member and work_item.assignee_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền truy cập công việc này",
            )

    return work_item


# Lấy danh sách công việc được giao cho user
@router.get(
    "/my-tasks",
    response_model=list[WorkItemResponse],
)
def get_my_assigned_work_items(
    status: Optional[str] = Query(
        None, regex="^(TODO|IN_PROGRESS|DONE)$", description="Lọc theo trạng thái"
    ),
    priority: Optional[str] = Query(
        None, regex="^(LOW|MEDIUM|HIGH)$", description="Lọc theo mức độ ưu tiên"
    ),
    sort_by: str = Query(
        "created_at",
        regex="^(created_at|due_date|priority)$",
        description="Sắp xếp theo",
    ),
    order: str = Query("desc", regex="^(asc|desc)$", description="Thứ tự sắp xếp"),
    limit: int = Query(10, ge=1, le=100, description="Số kết quả trên 1 trang"),
    offset: int = Query(0, ge=0, description="Số bản ghi bỏ qua"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lấy danh sách hạng mục công việc được giao cho user hiện tại

    **Tính năng:**
    - Filter theo status, priority
    - Pagination (limit/offset)
    - Sort theo created_at/due_date/priority
    """
    return WorkItemService.list_work_items_assigned_to_user_with_filters(
        db=db,
        user_id=current_user.id,
        status=status,
        priority=priority,
        sort_by=sort_by,
        order=order,
        limit=limit,
        offset=offset,
    )


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
    """
    Cập nhật hạng mục công việc

    **Quyền:**
    - Owner của site: cập nhật tất cả fields
    - Member của site: cập nhật status, priority (nếu được giao)
    - Assignee: cập nhật status, priority của công việc được giao
    """
    work_item = WorkItemService.get_work_item_by_id(db, item_id)
    if not work_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hạng mục công việc không tồn tại",
        )

    # Lấy site để kiểm tra quyền
    site = SiteService.get_site_by_id(db, work_item.site_id)

    # Permission Matrix
    is_owner = site.owner_id == current_user.id
    is_member = (
        db.query(SiteMember)
        .filter(SiteMember.site_id == site.id, SiteMember.user_id == current_user.id)
        .first()
        is not None
    )
    is_assignee = work_item.assignee_id == current_user.id

    if not (is_owner or is_member or is_assignee):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền cập nhật công việc này",
        )

    # Kiểm tra quyền cập nhật từng field
    if payload.assignee_id is not None and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ owner mới có thể thay đổi người được giao việc",
        )

    if payload.title is not None and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ owner mới có thể cập nhật title",
        )

    if payload.due_date is not None and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ owner mới có thể cập nhật due_date",
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
    """
    Xóa hạng mục công việc

    **Quyền:** Chỉ owner của site
    """
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
    new_status: str = Query(..., regex="^(TODO|IN_PROGRESS|DONE)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cập nhật trạng thái công việc

    **Quyền:** Owner/member/assignee của site
    """
    work_item = WorkItemService.get_work_item_by_id(db, item_id)
    if not work_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hạng mục công việc không tồn tại",
        )

    # Kiểm tra quyền
    site = SiteService.get_site_by_id(db, work_item.site_id)
    is_owner = site.owner_id == current_user.id
    is_member = (
        db.query(SiteMember)
        .filter(SiteMember.site_id == site.id, SiteMember.user_id == current_user.id)
        .first()
        is not None
    )
    is_assignee = work_item.assignee_id == current_user.id

    if not (is_owner or is_member or is_assignee):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền cập nhật trạng thái công việc này",
        )

    return WorkItemService.update_work_item_status(db, item_id, new_status)
