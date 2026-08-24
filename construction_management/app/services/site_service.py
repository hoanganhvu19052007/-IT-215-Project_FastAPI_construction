from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.site import ConstructionSite, SiteMember
from app.models.user import User
from app.schemas.site import ConstructionSiteCreate, ConstructionSiteUpdate


class SiteService:
    @staticmethod
    def create_site(db: Session, payload: ConstructionSiteCreate, owner_id: int):
        """Tạo công trình mới"""
        site = ConstructionSite(
            name=payload.name,
            description=payload.description,
            owner_id=owner_id,
        )
        db.add(site)
        db.commit()
        db.refresh(site)
        return site

    @staticmethod
    def get_site_by_id(db: Session, site_id: int):
        """Lấy thông tin công trình theo ID"""
        return db.query(ConstructionSite).filter(ConstructionSite.id == site_id).first()

    @staticmethod
    def list_sites(db: Session):
        """Lấy danh sách tất cả công trình"""
        return db.query(ConstructionSite).all()

    @staticmethod
    def list_sites_of_user(db: Session, user_id: int):
        """Lấy danh sách công trình của user (sở hữu hoặc là thành viên)"""
        # Lấy công trình mà user sở hữu
        owned_sites = db.query(ConstructionSite).filter(
            ConstructionSite.owner_id == user_id
        ).all()
        
        # Lấy công trình mà user là thành viên
        member_sites = db.query(ConstructionSite).join(SiteMember).filter(
            SiteMember.user_id == user_id
        ).all()
        
        # Gộp và loại bỏ trùng lặp
        sites = list(set(owned_sites + member_sites))
        return sites

    @staticmethod
    def update_site(db: Session, site_id: int, payload: ConstructionSiteUpdate):
        """Cập nhật thông tin công trình"""
        site = SiteService.get_site_by_id(db, site_id)
        if not site:
            return None
        
        if payload.name:
            site.name = payload.name
        if payload.description is not None:
            site.description = payload.description
        
        db.commit()
        db.refresh(site)
        return site

    @staticmethod
    def delete_site(db: Session, site_id: int):
        """Xóa công trình"""
        site = SiteService.get_site_by_id(db, site_id)
        if not site:
            return False
        
        db.delete(site)
        db.commit()
        return True

    @staticmethod
    def add_member_to_site(db: Session, site_id: int, user_id: int, role: str = "MEMBER"):
        """Thêm thành viên vào công trình"""
        # Kiểm tra công trình tồn tại
        site = SiteService.get_site_by_id(db, site_id)
        if not site:
            raise ValueError("Công trình không tồn tại")
        
        # Kiểm tra user tồn tại
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("Người dùng không tồn tại")
        
        # Kiểm tra user đã là thành viên
        existing_member = db.query(SiteMember).filter(
            SiteMember.site_id == site_id,
            SiteMember.user_id == user_id
        ).first()
        if existing_member:
            raise ValueError("Người dùng đã là thành viên của công trình này")
        
        # Thêm thành viên mới
        member = SiteMember(
            site_id=site_id,
            user_id=user_id,
            role=role,
        )
        db.add(member)
        db.commit()
        return member

    @staticmethod
    def remove_member_from_site(db: Session, site_id: int, user_id: int):
        """Xóa thành viên khỏi công trình"""
        member = db.query(SiteMember).filter(
            SiteMember.site_id == site_id,
            SiteMember.user_id == user_id
        ).first()
        if not member:
            return False
        
        db.delete(member)
        db.commit()
        return True

    @staticmethod
    def get_site_members(db: Session, site_id: int):
        """Lấy danh sách thành viên của công trình"""
        return db.query(SiteMember).filter(SiteMember.site_id == site_id).all()

    @staticmethod
    def update_member_role(db: Session, site_id: int, user_id: int, role: str):
        """Cập nhật vai trò của thành viên"""
        member = db.query(SiteMember).filter(
            SiteMember.site_id == site_id,
            SiteMember.user_id == user_id
        ).first()
        if not member:
            return None
        
        member.role = role
        db.commit()
        db.refresh(member)
        return member
