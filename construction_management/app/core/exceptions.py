from fastapi import Request, HTTPException, status
from datetime import datetime
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


def register_exception_handlers(app):

    # Hàm trả về lỗi 422 ko đúng định dạng
    def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "success": False,
                "status_code": 422,
                "message": "Dữ liệu gửi lên không đúng định dạng",
                "path": request.url.path,
                "timestamp": datetime.now().isoformat(),
                "detail": exc.errors(),
            },
        )

    def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "status_code": exc.status_code,
                "message": exc.detail,
                "path": request.url.path,
                "timestamp": datetime.now().isoformat(),
                "detail": None,
            },
        )

    def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "status_code": 400,
                "message": str(exc),
                "path": request.url.path,
                "timestamp": datetime.now().isoformat(),
                "detail": None,
            },
        )

    def db_integrity_error_handler(request: Request, exc: IntegrityError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "status_code": 400,
                "message": "Dữ liệu đã tồn tại hoặc vi phạm ràng buộc dữ liệu trong hệ thống.",
                "path": request.url.path,
                "timestamp": datetime.now().isoformat(),
                "detail": None,
            },
        )

    def general_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "status_code": 500,
                "message": "Lỗi máy chủ nội bộ. Vui lòng thử lại sau.",
                "path": request.url.path,
                "timestamp": datetime.now().isoformat(),
                "detail": None,
            },
        )

    # Đăng ký các handlers
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(ValueError, value_error_handler)
    app.add_exception_handler(IntegrityError, db_integrity_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)

