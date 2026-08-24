from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.site import ConstructionSite, SiteMember
from app.schemas.site import (
    ConstructionSiteCreate,
    ConstructionSiteUpdate,
    ConstructionSiteResponse,
)
from app.schemas.site_member import SiteMemberResponse
from app.services.site_service import SiteService

# Tạo router cho API Site
router = APIRouter(
    prefix="/construction-sites",
    tags=["construction-sites"],
)


# Tạo công trình mới
@router.post(
    "/",
    response_model=ConstructionSiteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_site(
    payload: ConstructionSiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tạo công trình mới (user là chủ công trình)"""
    return SiteService.create_site(db, payload, current_user.id)


# Lấy danh sách công trình của user hiện tại
@router.get(
    "/my-sites",
    response_model=list[ConstructionSiteResponse],
)
def list_my_sites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lấy danh sách công trình của user (sở hữu hoặc là thành viên)"""
    return SiteService.list_sites_of_user(db, current_user.id)


# Lấy danh sách tất cả công trình
@router.get(
    "/",
    response_model=list[ConstructionSiteResponse],
)
def list_sites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lấy danh sách tất cả công trình"""
    return SiteService.list_sites(db)


# Lấy chi tiết công trình
@router.get(
    "/{site_id}",
    response_model=ConstructionSiteResponse,
)
def get_site(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lấy chi tiết công trình theo ID"""
    site = SiteService.get_site_by_id(db, site_id)
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Công trình không tồn tại",
        )
    return site


# Cập nhật công trình
@router.patch(
    "/{site_id}",
    response_model=ConstructionSiteResponse,
)
def update_site(
    site_id: int,
    payload: ConstructionSiteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cập nhật thông tin công trình (chỉ chủ công trình)"""
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
    
    return SiteService.update_site(db, site_id, payload)


# Xóa công trình
@router.delete(
    "/{site_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_site(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Xóa công trình (chỉ chủ công trình)"""
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
    
    SiteService.delete_site(db, site_id)


# Thêm thành viên vào công trình
@router.post(
    "/{site_id}/members",
    response_model=SiteMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_member_to_site(
    site_id: int,
    user_id: int,
    role: str = "MEMBER",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Thêm thành viên vào công trình (chỉ chủ công trình)"""
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
        return SiteService.add_member_to_site(db, site_id, user_id, role)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# Lấy danh sách thành viên của công trình
@router.get(
    "/{site_id}/members",
    response_model=list[SiteMemberResponse],
)
def get_site_members(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lấy danh sách thành viên của công trình"""
    site = SiteService.get_site_by_id(db, site_id)
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Công trình không tồn tại",
        )
    
    return SiteService.get_site_members(db, site_id)


# Xóa thành viên khỏi công trình
@router.delete(
    "/{site_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_member_from_site(
    site_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Xóa thành viên khỏi công trình (chỉ chủ công trình)"""
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
    
    success = SiteService.remove_member_from_site(db, site_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thành viên không tồn tại trong công trình",
        )


# Cập nhật vai trò thành viên
@router.patch(
    "/{site_id}/members/{user_id}",
    response_model=SiteMemberResponse,
)
def update_member_role(
    site_id: int,
    user_id: int,
    role: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cập nhật vai trò thành viên (chỉ chủ công trình)"""
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
    
    member = SiteService.update_member_role(db, site_id, user_id, role)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thành viên không tồn tại",
        )
    
    return member
