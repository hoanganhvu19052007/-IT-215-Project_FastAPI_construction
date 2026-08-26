from fastapi import APIRouter

router = APIRouter(
    prefix="/health",
    tags=["Health Check"],
)


@router.get(
    "",
    summary="Kiểm tra trạng thái sức khỏe dịch vụ",
    description="Trả về thông tin xác nhận API service đang hoạt động bình thường.",
    responses={
        200: {
            "description": "Dịch vụ hoạt động tốt",
            "content": {"application/json": {"example": {"status": "ok"}}},
        }
    },
)
def health_check():
    return {"status": "ok"}
