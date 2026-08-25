from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.work_item import WorkItem
from app.models.site import ConstructionSite, SiteMember
from app.models.user import User
from app.schemas.work_item import (
    WorkItemCreate,
    WorkItemResponse,
    WorkItemUpdate,
)
from app.core.security import decode_token

router = APIRouter(tags=["Work Items"])


# Dependency: lấy current_user từ JWT token
def get_current_user(
    authorization: Optional[str] = None, db: Session = Depends(get_db)
) -> User:
    """
    Lấy thông tin user hiện tại từ Authorization header
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ",
        )

    token = authorization.split(" ")[1]
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token hết hạn hoặc không hợp lệ",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không chứa user ID",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User không tồn tại",
        )

    return user


# Dependency: kiểm tra user có quyền truy cập site không
def verify_site_access(
    site_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConstructionSite:
    """
    Kiểm tra user có quyền truy cập site hay không
    User phải là owner hoặc member của site
    """
    site = db.query(ConstructionSite).filter(
        ConstructionSite.id == site_id
    ).first()

    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Công trình với ID {site_id} không tồn tại",
        )

    # Kiểm tra user có phải owner không
    if site.owner_id == current_user.id:
        return site

    # Kiểm tra user có phải member của site không
    site_member = db.query(SiteMember).filter(
        and_(
            SiteMember.site_id == site_id,
            SiteMember.user_id == current_user.id,
        )
    ).first()

    if not site_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập công trình này",
        )

    return site


# POST /construction-sites/{site_id}/work-items
# Tạo mới một hạng mục thi công
@router.post(
    "/construction-sites/{site_id}/work-items",
    response_model=WorkItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_work_item(
    site_id: int,
    work_item_data: WorkItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Tạo mới một hạng mục thi công
    
    **Yêu cầu:**
    - User phải là owner hoặc member của site
    - site_id phải hợp lệ
    
    **Request body:**
    - title (str): Tên hạng mục (bắt buộc)
    - description (str): Mô tả (tùy chọn)
    - priority (str): Mức độ ưu tiên - LOW/MEDIUM/HIGH (mặc định: MEDIUM)
    - due_date (datetime): Hạn hoàn thành (tùy chọn)
    - assignee_id (int): ID người được giao việc (tùy chọn)
    """
    # Kiểm tra site tồn tại và user có quyền
    site = verify_site_access(site_id, current_user, db)

    # Nếu có assignee_id, kiểm tra người đó có tồn tại không
    if work_item_data.assignee_id:
        assignee = db.query(User).filter(
            User.id == work_item_data.assignee_id
        ).first()
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User với ID {work_item_data.assignee_id} không tồn tại",
            )

        # Kiểm tra assignee có phải member của site không
        assignee_membership = db.query(SiteMember).filter(
            and_(
                SiteMember.site_id == site_id,
                SiteMember.user_id == work_item_data.assignee_id,
            )
        ).first()

        # Assignee phải là owner hoặc member của site
        if assignee.id != site.owner_id and not assignee_membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Người được giao việc phải là thành viên của công trình",
            )

    # Tạo work item mới
    new_work_item = WorkItem(
        site_id=site_id,
        title=work_item_data.title,
        description=work_item_data.description,
        priority=work_item_data.priority,
        due_date=work_item_data.due_date,
        assignee_id=work_item_data.assignee_id,
        status="TODO",  # Trạng thái mặc định
    )

    db.add(new_work_item)
    db.commit()
    db.refresh(new_work_item)

    return new_work_item


# GET /construction-sites/{site_id}/work-items
# Lấy danh sách hạng mục của một công trình
@router.get(
    "/construction-sites/{site_id}/work-items",
    response_model=list[WorkItemResponse],
)
def list_work_items(
    site_id: int,
    status: Optional[str] = Query(None, pattern="^(TODO|IN_PROGRESS|DONE)$"),
    priority: Optional[str] = Query(None, pattern="^(LOW|MEDIUM|HIGH)$"),
    assignee_id: Optional[int] = None,
    sort_by: str = Query("created_at", regex="^(created_at|due_date|priority)$"),
    order: str = Query("asc", regex="^(asc|desc)$"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Lấy danh sách hạng mục của một công trình với các tính năng:
    
    **Query parameters:**
    - status (str): Lọc theo trạng thái - TODO/IN_PROGRESS/DONE
    - priority (str): Lọc theo mức độ ưu tiên - LOW/MEDIUM/HIGH
    - assignee_id (int): Lọc theo người được giao việc
    - sort_by (str): Sắp xếp theo - created_at/due_date/priority (mặc định: created_at)
    - order (str): Thứ tự sắp xếp - asc/desc (mặc định: asc)
    - limit (int): Số kết quả trên 1 trang (mặc định: 10, tối đa: 100)
    - offset (int): Số bản ghi bỏ qua (mặc định: 0)
    """
    # Kiểm tra site tồn tại và user có quyền
    verify_site_access(site_id, current_user, db)

    # Xây dựng query
    query = db.query(WorkItem).filter(WorkItem.site_id == site_id)

    # Filter theo status
    if status:
        query = query.filter(WorkItem.status == status)

    # Filter theo priority
    if priority:
        query = query.filter(WorkItem.priority == priority)

    # Filter theo assignee_id
    if assignee_id is not None:
        query = query.filter(WorkItem.assignee_id == assignee_id)

    # Sắp xếp
    if sort_by == "created_at":
        sort_column = WorkItem.created_at
    elif sort_by == "due_date":
        sort_column = WorkItem.due_date
    else:  # priority
        sort_column = WorkItem.priority

    if order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Pagination
    total_count = query.count()
    work_items = query.limit(limit).offset(offset).all()

    return work_items


# GET /work-items/{item_id}
# Lấy chi tiết một hạng mục
@router.get("/work-items/{item_id}", response_model=WorkItemResponse)
def get_work_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Lấy chi tiết một hạng mục thi công
    
    **Path parameters:**
    - item_id (int): ID của hạng mục
    """
    work_item = db.query(WorkItem).filter(WorkItem.id == item_id).first()

    if not work_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hạng mục với ID {item_id} không tồn tại",
        )

    # Kiểm tra user có quyền truy cập công trình này không
    verify_site_access(work_item.site_id, current_user, db)

    return work_item


# PATCH /work-items/{item_id}
# Cập nhật hạng mục
@router.patch("/work-items/{item_id}", response_model=WorkItemResponse)
def update_work_item(
    item_id: int,
    work_item_update: WorkItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Cập nhật thông tin hạng mục thi công
    
    **Path parameters:**
    - item_id (int): ID của hạng mục
    
    **Request body (tất cả tùy chọn):**
    - title (str): Tên hạng mục
    - description (str): Mô tả
    - status (str): Trạng thái - TODO/IN_PROGRESS/DONE
    - priority (str): Mức độ ưu tiên - LOW/MEDIUM/HIGH
    - due_date (datetime): Hạn hoàn thành
    - assignee_id (int): Người được giao việc
    
    **Lưu ý:** Không thể cập nhật site_id
    """
    work_item = db.query(WorkItem).filter(WorkItem.id == item_id).first()

    if not work_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hạng mục với ID {item_id} không tồn tại",
        )

    # Kiểm tra user có quyền truy cập công trình này không
    verify_site_access(work_item.site_id, current_user, db)

    # Cập nhật các trường nếu có
    if work_item_update.title is not None:
        work_item.title = work_item_update.title

    if work_item_update.description is not None:
        work_item.description = work_item_update.description

    if work_item_update.status is not None:
        work_item.status = work_item_update.status

    if work_item_update.priority is not None:
        work_item.priority = work_item_update.priority

    if work_item_update.due_date is not None:
        work_item.due_date = work_item_update.due_date

    if work_item_update.assignee_id is not None:
        # Kiểm tra assignee tồn tại
        assignee = db.query(User).filter(
            User.id == work_item_update.assignee_id
        ).first()
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User với ID {work_item_update.assignee_id} không tồn tại",
            )

        # Kiểm tra assignee có phải member của site không
        site = work_item.site
        assignee_membership = db.query(SiteMember).filter(
            and_(
                SiteMember.site_id == site.id,
                SiteMember.user_id == work_item_update.assignee_id,
            )
        ).first()

        # Assignee phải là owner hoặc member của site
        if assignee.id != site.owner_id and not assignee_membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Người được giao việc phải là thành viên của công trình",
            )

        work_item.assignee_id = work_item_update.assignee_id

    db.commit()
    db.refresh(work_item)

    return work_item


# DELETE /work-items/{item_id}
# Xóa hạng mục
@router.delete("/work-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_work_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Xóa một hạng mục thi công
    
    **Path parameters:**
    - item_id (int): ID của hạng mục
    
    **Yêu cầu:**
    - User phải là owner của site hoặc có quyền trong site
    """
    work_item = db.query(WorkItem).filter(WorkItem.id == item_id).first()

    if not work_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hạng mục với ID {item_id} không tồn tại",
        )

    # Kiểm tra user có quyền truy cập công trình này không
    site = verify_site_access(work_item.site_id, current_user, db)

    # Chỉ owner của site có thể xóa
    if site.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ owner của công trình mới có thể xóa hạng mục",
        )

    db.delete(work_item)
    db.commit()

    return None
