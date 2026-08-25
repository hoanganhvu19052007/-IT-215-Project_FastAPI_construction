from fastapi import APIRouter

from app.db.database import check_db_connection

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    db_ok = check_db_connection()
    return {
        "success": True,
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
    }
