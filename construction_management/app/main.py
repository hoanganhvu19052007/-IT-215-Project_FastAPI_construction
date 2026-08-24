from fastapi import FastAPI

from app.core.config import settings
from app.core.exceptions import register_exception_handlers

from app.router.auth import router as auth_router
from app.router.health import router as health_router
from app.router.user import router as user_router
from app.router.site import router as site_router
from app.router.work_item import router as work_item_router

app = FastAPI(
    title="Construction Management API",
    debug=settings.DEBUG,
)

register_exception_handlers(app)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(site_router)
app.include_router(work_item_router)


@app.get("/")
def root():
    return {"message": "Construction Management API is running"}
