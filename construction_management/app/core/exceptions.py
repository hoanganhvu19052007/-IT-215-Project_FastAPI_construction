from fastapi import Request, HTTPException, status
from datetime import datetime
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


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

    def general_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "status_code": 500,
                "message": "Lỗi máy chủ nội bộ. Vui lòng thử lại sau.",
                "path": request.url.path,
                "timestamp": datetime.now().isoformat(),
                "details": None,
            },
        )

    # Đăng ký các handlers
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
