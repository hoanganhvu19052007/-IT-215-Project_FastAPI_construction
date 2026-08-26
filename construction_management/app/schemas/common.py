from typing import Optional, Any
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Schema chuẩn cho phản hồi lỗi"""

    success: bool = False
    status_code: int
    message: str
    path: str
    timestamp: str
    detail: Optional[Any] = None


class MessageResponse(BaseModel):
    """Schema chuẩn cho phản hồi thông báo thành công"""

    success: bool = True
    message: str
