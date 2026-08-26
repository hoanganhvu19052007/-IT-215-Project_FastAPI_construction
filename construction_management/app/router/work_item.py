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
from app.schemas.common import ErrorResponse
from app.services.site_service import SiteService
from app.services.work_item_service import WorkItemService

router = APIRouter(
    tags=["Work Items"],
)


@router.post(
    "/construction-sites/{site_id}/work-items",
    response_model=WorkItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo hạng mục thi công trong công trình",
    description="""
Tạo một hạng mục công việc thi công mới cho công trình.
* **site_id**: ID công trình cần tạo công việc.
* **assignee_id**: (Tùy chọn) ID người dùng được giao việc (phải là thành viên hoặc owner của công trình).
* **priority**: Độ ưu tiên (`LOW`, `MEDIUM`, `HIGH`). Mặc định là `MEDIUM`.
* Yêu cầu: Chủ công trình (`OWNER`) hoặc thành viên (`MEMBER`) của công trình.
""",
    responses={
        201: {"description": "Tạo hạng mục công việc thành công"},
        400: {"model": ErrorResponse, "description": "Lỗi dữ liệu (ví dụ người giao việc không phải thành viên công trình)"},
        401: {"model": ErrorResponse, "description": "Chưa đăng nhập"},
        403: {"model": ErrorResponse, "description": "Không có quyền tạo công việc trong công trình này"},
        404: {"model": ErrorResponse, "description": "Công trình không tồn tại"},
    },
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
    target_site_id = site_id or payload.site_id
    payload.site_id = target_site_id

    site = SiteService.get_site_by_id(db, target_site_id)
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Công trình không tồn tại",
        )

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


@router.get(
    "/construction-sites/{site_id}/work-items",
    response_model=list[WorkItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Lấy danh sách hạng mục thi công của công trình",
    description="""
Lấy danh sách các hạng mục công việc thi công thuộc công trình. Hỗ trợ lọc, tìm kiếm, sắp xếp và phân trang.
* **status**: Lọc theo trạng thái (`TODO`, `IN_PROGRESS`, `DONE`).
* **priority**: Lọc theo độ ưu tiên (`LOW`, `MEDIUM`, `HIGH`).
* **assignee_id**: Lọc theo ID người được giao việc.
* **search**: Tìm kiếm tiêu đề công việc.
* **sort_by**: Sắp xếp theo `created_at`, `due_date`, `priority`.
* **order**: Thứ tự `asc` hoặc `desc`.
* **limit & offset**: Phân trang kết quả.
""",
    responses={
        200: {"description": "Lấy danh sách hạng mục thành công"},
        401: {"model": ErrorResponse, "description": "Chưa đăng nhập"},
        403: {"model": ErrorResponse, "description": "Bạn không có quyền truy cập công trình này"},
        404: {"model": ErrorResponse, "description": "Công trình không tồn tại"},
    },
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


@router.get(
    "/work-items/my-tasks",
    response_model=list[WorkItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Lấy danh sách công việc được giao cho tôi",
    description="""
Lấy tất cả các hạng mục thi công được giao cho tài khoản đang đăng nhập.
* Hỗ trợ lọc theo trạng thái, độ ưu tiên, sắp xếp và phân trang.
""",
    responses={
        200: {"description": "Lấy danh sách công việc thành công"},
        401: {"model": ErrorResponse, "description": "Chưa đăng nhập"},
    },
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


@router.get(
    "/work-items/{item_id}",
    response_model=WorkItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Lấy chi tiết hạng mục thi công",
    description="""
Lấy chi tiết thông tin một công việc theo `item_id`.
* Yêu cầu: Quyền chủ công trình, thành viên công trình hoặc người được giao công việc.
""",
    responses={
        200: {"description": "Lấy chi tiết công việc thành công"},
        401: {"model": ErrorResponse, "description": "Chưa đăng nhập"},
        403: {"model": ErrorResponse, "description": "Bạn không có quyền truy cập công việc này"},
        404: {"model": ErrorResponse, "description": "Hạng mục công việc không tồn tại"},
    },
)
def get_work_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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


@router.patch(
    "/work-items/{item_id}",
    response_model=WorkItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Cập nhật hạng mục thi công",
    description="""
Cập nhật nội dung công việc (tiêu đề, mô tả, phân công, trạng thái, độ ưu tiên, hạn chót).
* **Phân quyền**:
  - Chủ công trình (`OWNER`): Được cập nhật tất cả các trường.
  - Thành viên / Người được giao: Chỉ được cập nhật trạng thái (`status`), không được chỉnh sửa tiêu đề, hạn chót hoặc phân công người khác.
""",
    responses={
        200: {"description": "Cập nhật công việc thành công"},
        400: {"model": ErrorResponse, "description": "Lỗi dữ liệu (người được phân công không thuộc công trình)"},
        401: {"model": ErrorResponse, "description": "Chưa đăng nhập"},
        403: {"model": ErrorResponse, "description": "Không có quyền cập nhật trường thông tin này"},
        404: {"model": ErrorResponse, "description": "Công việc không tồn tại"},
    },
)
def update_work_item(
    item_id: int,
    payload: WorkItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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


@router.delete(
    "/work-items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa hạng mục thi công",
    description="""
Xóa hoàn toàn một hạng mục thi công khỏi công trình.
* Yêu cầu: Chỉ chủ công trình (`OWNER`) mới có quyền xóa.
""",
    responses={
        204: {"description": "Xóa công việc thành công"},
        401: {"model": ErrorResponse, "description": "Chưa đăng nhập"},
        403: {"model": ErrorResponse, "description": "Chỉ chủ công trình mới được phép xóa công việc"},
        404: {"model": ErrorResponse, "description": "Hạng mục công việc không tồn tại"},
    },
)
def delete_work_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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


@router.patch(
    "/work-items/{item_id}/status",
    response_model=WorkItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Cập nhật nhanh trạng thái hạng mục thi công",
    description="""
Thay đổi nhanh trạng thái công việc (`TODO`, `IN_PROGRESS`, `DONE`).
* Yêu cầu: Chủ công trình, thành viên công trình hoặc người được giao việc.
""",
    responses={
        200: {"description": "Cập nhật trạng thái thành công"},
        400: {"model": ErrorResponse, "description": "Trạng thái không hợp lệ"},
        401: {"model": ErrorResponse, "description": "Chưa đăng nhập"},
        403: {"model": ErrorResponse, "description": "Bạn không có quyền cập nhật trạng thái công việc này"},
        404: {"model": ErrorResponse, "description": "Công việc không tồn tại"},
    },
)
def update_work_item_status(
    item_id: int,
    new_status: str = Query(..., pattern="^(TODO|IN_PROGRESS|DONE)$", description="Trạng thái mới"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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
