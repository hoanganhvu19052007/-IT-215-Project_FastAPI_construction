from typing import Optional
from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.site import SiteMember
from app.schemas.work_item import (
    WorkItemCreate,
    WorkItemUpdate,
    WorkItemResponse,
)
from app.services.site_service import SiteService
from app.services.work_item_service import WorkItemService

# Router cho Work Items (không prefix cứng để linh hoạt REST paths)
router = APIRouter(
    tags=["work-items"],
)


# POST /construction-sites/{site_id}/work-items: tạo hạng mục công việc trong công trình
@router.post(
    "/construction-sites/{site_id}/work-items",
    response_model=WorkItemResponse,
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "/work-items/",
    response_model=WorkItemResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def create_work_item(
    payload: WorkItemCreate,
    site_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Tạo mới một hạng mục thi công cho công trình
    Quyền: Owner hoặc member của site
    """
    target_site_id = site_id or payload.site_id
    payload.site_id = target_site_id

    # Kiểm tra công trình tồn tại
    site = SiteService.get_site_by_id(db, target_site_id)
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Công trình không tồn tại",
        )

    # Kiểm tra user có quyền trong công trình không (owner hoặc member)
    if site.owner_id != current_user.id:
        member = (
            db.query(SiteMember)
            .filter(
                SiteMember.site_id == target_site_id,
                SiteMember.user_id == current_user.id,
            )
            .first()
        )
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền tạo công việc trong công trình này",
            )

    try:
        return WorkItemService.create_work_item(db, payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# GET /construction-sites/{site_id}/work-items: danh sách hạng mục của công trình
@router.get(
    "/construction-sites/{site_id}/work-items",
    response_model=list[WorkItemResponse],
)
def list_work_items_by_site(
    site_id: int,
    status_filter: Optional[str] = Query(
        None, alias="status", pattern="^(TODO|IN_PROGRESS|DONE)$", description="Lọc theo trạng thái"
    ),
    priority: Optional[str] = Query(
        None, pattern="^(LOW|MEDIUM|HIGH)$", description="Lọc theo mức độ ưu tiên"
    ),
    assignee_id: Optional[int] = Query(
        None, description="Lọc theo người được giao việc"
    ),
    search: Optional[str] = Query(
        None, min_length=1, max_length=255, description="Tìm kiếm theo tiêu đề"
    ),
    sort_by: str = Query(
        "created_at",
        pattern="^(created_at|due_date|priority)$",
        description="Sắp xếp theo",
    ),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Thứ tự sắp xếp"),
    limit: int = Query(10, ge=1, le=100, description="Số lượng kết quả"),
    offset: int = Query(0, ge=0, description="Số lượng bỏ qua"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lấy danh sách hạng mục thi công thuộc công trình (không lộ công trình khác)
    Quyền: Owner hoặc member của site
    """
    site = SiteService.get_site_by_id(db, site_id)
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Công trình không tồn tại",
        )

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

    return WorkItemService.list_work_items_by_site_with_filters(
        db=db,
        site_id=site_id,
        status=status_filter,
        priority=priority,
        assignee_id=assignee_id,
        search=search,
        sort_by=sort_by,
        order=order,
        limit=limit,
        offset=offset,
    )


# GET /work-items/my-tasks: danh sách hạng mục giao cho user
@router.get(
    "/work-items/my-tasks",
    response_model=list[WorkItemResponse],
)
def get_my_assigned_work_items(
    status_filter: Optional[str] = Query(
        None, alias="status", pattern="^(TODO|IN_PROGRESS|DONE)$", description="Lọc theo trạng thái"
    ),
    priority: Optional[str] = Query(
        None, pattern="^(LOW|MEDIUM|HIGH)$", description="Lọc theo mức độ ưu tiên"
    ),
    sort_by: str = Query(
        "created_at",
        pattern="^(created_at|due_date|priority)$",
        description="Sắp xếp theo",
    ),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Thứ tự sắp xếp"),
    limit: int = Query(10, ge=1, le=100, description="Số lượng kết quả"),
    offset: int = Query(0, ge=0, description="Số lượng bỏ qua"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lấy danh sách công việc được giao cho người dùng hiện tại
    """
    return WorkItemService.list_work_items_assigned_to_user_with_filters(
        db=db,
        user_id=current_user.id,
        status=status_filter,
        priority=priority,
        sort_by=sort_by,
        order=order,
        limit=limit,
        offset=offset,
    )


# GET /work-items/{item_id}: xem chi tiết hạng mục
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
    Lấy chi tiết một hạng mục thi công (kiểm tra thuộc công trình)
    """
    work_item = WorkItemService.get_work_item_by_id(db, item_id)
    if not work_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hạng mục công việc không tồn tại",
        )

    site = SiteService.get_site_by_id(db, work_item.site_id)
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Công trình không tồn tại",
        )

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
            detail="Bạn không có quyền truy cập công việc này",
        )

    return work_item


# PATCH /work-items/{item_id}: cập nhật hạng mục
@router.patch(
    "/work-items/{item_id}",
    response_model=WorkItemResponse,
)
def update_work_item(
    item_id: int,
    payload: WorkItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cập nhật các trường gửi lên của hạng mục thi công
    """
    work_item = WorkItemService.get_work_item_by_id(db, item_id)
    if not work_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hạng mục công việc không tồn tại",
        )

    site = SiteService.get_site_by_id(db, work_item.site_id)
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Công trình không tồn tại",
        )

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

    # Nếu chỉ là member/assignee không phải owner thì không sửa title, due_date, assignee_id
    if not is_owner:
        if payload.assignee_id is not None or payload.title is not None or payload.due_date is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Chỉ chủ công trình mới có quyền cập nhật tiêu đề, hạn chót hoặc phân công người làm",
            )

    try:
        return WorkItemService.update_work_item(db, item_id, payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# DELETE /work-items/{item_id}: xóa hạng mục
@router.delete(
    "/work-items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_work_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Xóa một hạng mục thi công (chỉ chủ công trình)
    """
    work_item = WorkItemService.get_work_item_by_id(db, item_id)
    if not work_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hạng mục công việc không tồn tại",
        )

    site = SiteService.get_site_by_id(db, work_item.site_id)
    if not site or site.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ chủ công trình mới được phép xóa công việc",
        )

    WorkItemService.delete_work_item(db, item_id)


# PATCH /work-items/{item_id}/status: cập nhật riêng trạng thái
@router.patch(
    "/work-items/{item_id}/status",
    response_model=WorkItemResponse,
)
def update_work_item_status(
    item_id: int,
    new_status: str = Query(..., pattern="^(TODO|IN_PROGRESS|DONE)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cập nhật nhanh trạng thái hạng mục công việc
    """
    work_item = WorkItemService.get_work_item_by_id(db, item_id)
    if not work_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hạng mục công việc không tồn tại",
        )

    site = SiteService.get_site_by_id(db, work_item.site_id)
    is_owner = site and site.owner_id == current_user.id
    is_member = (
        site
        and db.query(SiteMember)
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
