from typing import Optional
from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.site import SiteMember
from app.schemas.site import (
    ConstructionSiteCreate,
    ConstructionSiteUpdate,
    ConstructionSiteResponse,
)
from app.schemas.site_member import SiteMemberResponse
from app.schemas.common import ErrorResponse
from app.services.site_service import SiteService

router = APIRouter(
    prefix="/construction-sites",
    tags=["Construction Sites"],
)


@router.post(
    "",
    response_model=ConstructionSiteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo mới công trình thi công",
    description="""
Tạo một công trình xây dựng mới. Người tạo sẽ tự động được phân quyền vai trò `OWNER` trong công trình này.
""",
    responses={
        201: {"description": "Tạo công trình thành công"},
        401: {"model": ErrorResponse, "description": "Token không hợp lệ hoặc đã hết hạn"},
        422: {"model": ErrorResponse, "description": "Dữ liệu đầu vào không đúng định dạng"},
    },
)
@router.post(
    "/",
    response_model=ConstructionSiteResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def create_site(
    payload: ConstructionSiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return SiteService.create_site(db, payload, current_user.id)


@router.get(
    "",
    response_model=list[ConstructionSiteResponse],
    status_code=status.HTTP_200_OK,
    summary="Lấy danh sách công trình của tôi",
    description="""
Lấy danh sách các công trình mà người dùng hiện tại sở hữu (`OWNER`) hoặc tham gia với tư cách thành viên (`MEMBER`).
* **search**: Tìm kiếm theo tên công trình (không phân biệt chữ hoa/thường).
""",
    responses={
        200: {"description": "Lấy danh sách công trình thành công"},
        401: {"model": ErrorResponse, "description": "Token không hợp lệ hoặc đã hết hạn"},
    },
)
@router.get(
    "/",
    response_model=list[ConstructionSiteResponse],
    include_in_schema=False,
)
def list_sites(
    search: Optional[str] = Query(None, description="Tìm kiếm theo tên công trình"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return SiteService.list_sites_of_user(db, current_user.id, search=search)


@router.get(
    "/{site_id}",
    response_model=ConstructionSiteResponse,
    status_code=status.HTTP_200_OK,
    summary="Lấy chi tiết công trình thi công",
    description="""
Xem thông tin chi tiết của công trình thi công theo `site_id`.
* Yêu cầu: Người dùng phải là Chủ công trình (`OWNER`) hoặc thành viên (`MEMBER`) của công trình đó.
""",
    responses={
        200: {"description": "Lấy chi tiết thành công"},
        401: {"model": ErrorResponse, "description": "Chưa đăng nhập"},
        403: {"model": ErrorResponse, "description": "Bạn không có quyền truy cập công trình này"},
        404: {"model": ErrorResponse, "description": "Công trình không tồn tại"},
    },
)
def get_site(
    site_id: int,
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

    return site


@router.put(
    "/{site_id}",
    response_model=ConstructionSiteResponse,
    status_code=status.HTTP_200_OK,
    summary="Cập nhật thông tin công trình",
    description="""
Cập nhật thông tin tên và mô tả của công trình thi công.
* Yêu cầu: Chỉ chủ công trình (`OWNER`) mới được phép chỉnh sửa.
""",
    responses={
        200: {"description": "Cập nhật công trình thành công"},
        401: {"model": ErrorResponse, "description": "Chưa đăng nhập"},
        403: {"model": ErrorResponse, "description": "Chỉ chủ công trình mới được phép cập nhật"},
        404: {"model": ErrorResponse, "description": "Công trình không tồn tại"},
    },
)
@router.patch(
    "/{site_id}",
    response_model=ConstructionSiteResponse,
    include_in_schema=False,
)
def update_site(
    site_id: int,
    payload: ConstructionSiteUpdate,
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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ chủ công trình mới được phép cập nhật",
        )

    return SiteService.update_site(db, site_id, payload, actor_id=current_user.id)


@router.delete(
    "/{site_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa mềm công trình thi công",
    description="""
Xóa mềm (`Soft Delete`) công trình thi công. Dữ liệu công trình sẽ đánh dấu ẩn và lưu mốc thời gian xóa mà không bị mất hẳn khỏi database.
* Yêu cầu: Chỉ chủ công trình (`OWNER`) mới được phép xóa.
""",
    responses={
        204: {"description": "Xóa công trình thành công (no content)"},
        401: {"model": ErrorResponse, "description": "Chưa đăng nhập"},
        403: {"model": ErrorResponse, "description": "Chỉ chủ công trình mới được phép xóa"},
        404: {"model": ErrorResponse, "description": "Công trình không tồn tại"},
    },
)
def delete_site(
    site_id: int,
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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ chủ công trình mới được phép xóa",
        )

    SiteService.delete_site(db, site_id, actor_id=current_user.id)


# --- SITE MEMBERS ENDPOINTS ---

@router.post(
    "/{site_id}/members",
    response_model=SiteMemberResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Site Members"],
    summary="Thêm thành viên vào công trình",
    description="""
Thêm một người dùng khác làm thành viên của công trình thi công.
* **user_id**: ID của người dùng cần thêm.
* **role**: Vai trò trong công trình (`MEMBER` hoặc `OWNER`). Mặc định là `MEMBER`.
* Yêu cầu: Chỉ chủ công trình (`OWNER`) mới có quyền thêm thành viên.
""",
    responses={
        201: {"description": "Thêm thành viên thành công"},
        400: {"model": ErrorResponse, "description": "Người dùng đã là thành viên hoặc không tồn tại"},
        401: {"model": ErrorResponse, "description": "Chưa đăng nhập"},
        403: {"model": ErrorResponse, "description": "Chỉ chủ công trình mới được phép thêm thành viên"},
        404: {"model": ErrorResponse, "description": "Công trình không tồn tại"},
    },
)
def add_member_to_site(
    site_id: int,
    user_id: int,
    role: str = Query("MEMBER", pattern="^(OWNER|MEMBER)$", description="Vai trò thành viên"),
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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ chủ công trình mới được phép thêm thành viên",
        )

    try:
        return SiteService.add_member_to_site(
            db, site_id, user_id, role, actor_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{site_id}/members",
    response_model=list[SiteMemberResponse],
    status_code=status.HTTP_200_OK,
    tags=["Site Members"],
    summary="Lấy danh sách thành viên của công trình",
    description="""
Xem danh sách tất cả các thành viên tham gia công trình thi công.
* Yêu cầu: Người dùng phải là Chủ công trình (`OWNER`) hoặc thành viên (`MEMBER`) của công trình.
""",
    responses={
        200: {"description": "Lấy danh sách thành viên thành công"},
        401: {"model": ErrorResponse, "description": "Chưa đăng nhập"},
        403: {"model": ErrorResponse, "description": "Bạn không có quyền truy cập công trình này"},
        404: {"model": ErrorResponse, "description": "Công trình không tồn tại"},
    },
)
def get_site_members(
    site_id: int,
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

    return SiteService.get_site_members(db, site_id)


@router.delete(
    "/{site_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Site Members"],
    summary="Xóa thành viên khỏi công trình",
    description="""
Xóa một thành viên khỏi công trình thi công.
* Yêu cầu: Chỉ chủ công trình (`OWNER`) mới được phép xóa thành viên. Không thể xóa chính chủ sở hữu công trình.
""",
    responses={
        204: {"description": "Xóa thành viên thành công"},
        400: {"model": ErrorResponse, "description": "Không thể xóa chủ công trình chính"},
        401: {"model": ErrorResponse, "description": "Chưa đăng nhập"},
        403: {"model": ErrorResponse, "description": "Chỉ chủ công trình mới được phép xóa thành viên"},
        404: {"model": ErrorResponse, "description": "Công trình hoặc thành viên không tồn tại"},
    },
)
def remove_member_from_site(
    site_id: int,
    user_id: int,
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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ chủ công trình mới được phép xóa thành viên",
        )

    try:
        success = SiteService.remove_member_from_site(
            db, site_id, user_id, actor_id=current_user.id
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thành viên không tồn tại trong công trình",
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.patch(
    "/{site_id}/members/{user_id}",
    response_model=SiteMemberResponse,
    status_code=status.HTTP_200_OK,
    tags=["Site Members"],
    summary="Cập nhật vai trò của thành viên trong công trình",
    description="""
Cập nhật vai trò (`OWNER` hoặc `MEMBER`) của một thành viên trong công trình.
* Yêu cầu: Chỉ chủ sở hữu công trình (`OWNER`) mới được điều chỉnh vai trò.
""",
    responses={
        200: {"description": "Cập nhật vai trò thành công"},
        401: {"model": ErrorResponse, "description": "Chưa đăng nhập"},
        403: {"model": ErrorResponse, "description": "Chỉ chủ công trình mới được phép cập nhật vai trò"},
        404: {"model": ErrorResponse, "description": "Công trình hoặc thành viên không tồn tại"},
    },
)
def update_member_role(
    site_id: int,
    user_id: int,
    role: str = Query(..., pattern="^(OWNER|MEMBER)$", description="Vai trò mới"),
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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ chủ công trình mới được phép cập nhật vai trò",
        )

    member = SiteService.update_member_role(
        db, site_id, user_id, role, actor_id=current_user.id
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thành viên không tồn tại trong công trình",
        )

    return member
