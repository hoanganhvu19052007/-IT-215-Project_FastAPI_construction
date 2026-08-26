from fastapi import FastAPI

from app.core.config import settings
from app.core.exceptions import register_exception_handlers

from app.router.auth import router as auth_router
from app.router.health import router as health_router
from app.router.user import router as user_router
from app.router.site import router as site_router
from app.router.work_item import router as work_item_router

from app.db.database import init_db

# Định nghĩa danh sách các tags và mô tả hiển thị trên Swagger UI
tags_metadata = [
    {
        "name": "Health Check",
        "description": "API kiểm tra trạng thái hoạt động của hệ thống backend và cơ sở dữ liệu SQL.",
    },
    {
        "name": "Authentication",
        "description": "Các API đăng ký tài khoản, đăng nhập và cấp phát JWT Access Token.",
    },
    {
        "name": "Users",
        "description": "Các API quản lý thông tin tài khoản người dùng và xem danh sách (dành cho Admin).",
    },
    {
        "name": "Construction Sites",
        "description": "Các API tạo, xem, cập nhật và xóa công trình thi công xây dựng.",
    },
    {
        "name": "Site Members",
        "description": "Các API quản lý phân quyền thành viên (OWNER / MEMBER) trong từng công trình.",
    },
    {
        "name": "Work Items",
        "description": "Các API quản lý các hạng mục thi công, công việc, phân công người thực hiện và trạng thái.",
    },
]

app = FastAPI(
    title="Construction Management API System",
    description="""
### Hệ Thống Quản Lý Thi Công Công Trình Xây Dựng (Construction Management System)

API cung cấp đầy đủ giải pháp backend phục vụ quản lý dự án xây dựng:
* **Xác thực & Phân quyền**: Đăng ký, đăng nhập JWT Bearer Token, hỗ trợ vai trò ADMIN / USER và OWNER / MEMBER trong công trình.
* **Quản lý công trình**: Tạo mới công trình, liệt kê, chỉnh sửa, xóa mềm (Soft Delete), truy vết nhật ký Audit Log.
* **Quản lý thành viên**: Thêm/xóa thành viên công trình, phân quyền vai trò.
* **Hạng mục thi công (Work Items)**: Quản lý công việc, lọc theo trạng thái (TODO, IN_PROGRESS, DONE), độ ưu tiên (LOW, MEDIUM, HIGH), tìm kiếm, phân trang và sắp xếp.
""",
    version="1.0.0",
    openapi_tags=tags_metadata,
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Tự động cập nhật bảng và cột DB khi khởi động
init_db()

register_exception_handlers(app)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(site_router)
app.include_router(work_item_router)


@app.get(
    "/",
    summary="Kiểm tra trạng thái máy chủ",
    description="Endpoint kiểm tra xem dịch vụ API có đang chạy hay không.",
    tags=["Health Check"],
)
def root():
    return {
        "success": True,
        "message": "Construction Management API is running",
        "version": "1.0.0",
    }
