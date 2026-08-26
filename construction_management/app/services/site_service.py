from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.site import ConstructionSite, SiteMember
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.site import ConstructionSiteCreate, ConstructionSiteUpdate


class SiteService:
    @staticmethod
    def create_site(db: Session, payload: ConstructionSiteCreate, owner_id: int) -> ConstructionSite:
        """Tạo công trình mới (tự động trở thành OWNER trong SiteMember và lưu AuditLog)"""
        site = ConstructionSite(
            name=payload.name,
            description=payload.description,
            owner_id=owner_id,
            is_deleted=False,
        )
        db.add(site)
        db.flush()

        # Tự động tạo bản ghi owner trong SiteMember
        owner_member = SiteMember(
            site_id=site.id,
            user_id=owner_id,
            role="OWNER",
        )
        db.add(owner_member)

        # Lưu audit log
        log = AuditLog(
            site_id=site.id,
            user_id=owner_id,
            action="CREATE_SITE",
            details=f"Tạo công trình '{site.name}'",
        )
        db.add(log)
        db.commit()
        db.refresh(site)
        return site

    @staticmethod
    def get_site_by_id(db: Session, site_id: int) -> Optional[ConstructionSite]:
        """Lấy thông tin công trình theo ID (chỉ lấy chưa bị xóa)"""
        return (
            db.query(ConstructionSite)
            .filter(ConstructionSite.id == site_id, ConstructionSite.is_deleted == False)
            .first()
        )

    @staticmethod
    def list_sites_of_user(db: Session, user_id: int, search: Optional[str] = None) -> list[ConstructionSite]:
        """Lấy danh sách công trình của user (sở hữu hoặc là thành viên) kèm tìm kiếm theo tên"""
        # Subquery hoặc join các site chưa bị xóa
        query = (
            db.query(ConstructionSite)
            .outerjoin(SiteMember, SiteMember.site_id == ConstructionSite.id)
            .filter(
                ConstructionSite.is_deleted == False,
                or_(
                    ConstructionSite.owner_id == user_id,
                    SiteMember.user_id == user_id,
                ),
            )
        )

        if search:
            query = query.filter(ConstructionSite.name.ilike(f"%{search}%"))

        return query.distinct().all()

    @staticmethod
    def update_site(db: Session, site_id: int, payload: ConstructionSiteUpdate, actor_id: int) -> Optional[ConstructionSite]:
        """Cập nhật thông tin công trình"""
        site = SiteService.get_site_by_id(db, site_id)
        if not site:
            return None

        if payload.name is not None:
            site.name = payload.name
        if payload.description is not None:
            site.description = payload.description

        log = AuditLog(
            site_id=site.id,
            user_id=actor_id,
            action="UPDATE_SITE",
            details=f"Cập nhật công trình ID {site.id}",
        )
        db.add(log)
        db.commit()
        db.refresh(site)
        return site

    @staticmethod
    def delete_site(db: Session, site_id: int, actor_id: int) -> bool:
        """Xóa mềm công trình (is_deleted=True, lưu deleted_at)"""
        site = SiteService.get_site_by_id(db, site_id)
        if not site:
            return False

        site.is_deleted = True
        site.deleted_at = datetime.utcnow()

        log = AuditLog(
            site_id=site.id,
            user_id=actor_id,
            action="DELETE_SITE",
            details=f"Xóa công trình ID {site.id}",
        )
        db.add(log)
        db.commit()
        return True

    @staticmethod
    def add_member_to_site(
        db: Session, site_id: int, user_id: int, role: str = "MEMBER", actor_id: int = None
    ) -> SiteMember:
        """Thêm thành viên vào công trình"""
        site = SiteService.get_site_by_id(db, site_id)
        if not site:
            raise ValueError("Công trình không tồn tại")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("Người dùng không tồn tại")

        existing_member = (
            db.query(SiteMember)
            .filter(SiteMember.site_id == site_id, SiteMember.user_id == user_id)
            .first()
        )
        if existing_member:
            raise ValueError("Người dùng đã là thành viên của công trình này")

        member = SiteMember(
            site_id=site_id,
            user_id=user_id,
            role=role,
        )
        db.add(member)

        log = AuditLog(
            site_id=site.id,
            user_id=actor_id or site.owner_id,
            action="ADD_MEMBER",
            details=f"Thêm user {user_id} vào công trình với vai trò {role}",
        )
        db.add(log)
        db.commit()
        db.refresh(member)
        return member

    @staticmethod
    def remove_member_from_site(db: Session, site_id: int, user_id: int, actor_id: int = None) -> bool:
        """Xóa thành viên khỏi công trình (không cho xóa Owner của công trình)"""
        site = SiteService.get_site_by_id(db, site_id)
        if not site:
            raise ValueError("Công trình không tồn tại")

        if site.owner_id == user_id:
            raise ValueError("Không thể xóa Owner chính của công trình")

        member = (
            db.query(SiteMember)
            .filter(SiteMember.site_id == site_id, SiteMember.user_id == user_id)
            .first()
        )
        if not member:
            return False

        # Kiểm tra nếu đây là owner cuối cùng trong bảng site_members
        if member.role == "OWNER":
            owner_count = (
                db.query(SiteMember)
                .filter(SiteMember.site_id == site_id, SiteMember.role == "OWNER")
                .count()
            )
            if owner_count <= 1:
                raise ValueError("Không thể xóa OWNER cuối cùng của công trình")

        db.delete(member)

        log = AuditLog(
            site_id=site.id,
            user_id=actor_id or site.owner_id,
            action="REMOVE_MEMBER",
            details=f"Xóa user {user_id} khỏi công trình",
        )
        db.add(log)
        db.commit()
        return True

    @staticmethod
    def get_site_members(db: Session, site_id: int) -> list[SiteMember]:
        """Lấy danh sách thành viên của công trình"""
        return db.query(SiteMember).filter(SiteMember.site_id == site_id).all()

    @staticmethod
    def update_member_role(db: Session, site_id: int, user_id: int, role: str, actor_id: int = None) -> Optional[SiteMember]:
        """Cập nhật vai trò của thành viên"""
        member = (
            db.query(SiteMember)
            .filter(SiteMember.site_id == site_id, SiteMember.user_id == user_id)
            .first()
        )
        if not member:
            return None

        member.role = role
        db.commit()
        db.refresh(member)
        return member
