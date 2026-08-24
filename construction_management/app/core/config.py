# Thư viện os dùng để làm việc với hệ điều hành
import os

# lru_cache dùng để lưu kết quả của hàm, giúp không phải tạo lại Settings nhiều lần.
from functools import lru_cache

# BaseSettings: dùng để đọc các biến môi trường từ file .env
# SettingsConfigDict: cấu hình cách BaseSettings đọc file .env
from pydantic_settings import BaseSettings, SettingsConfigDict

# Chọn file .env nếu có, không thì dùng .env.example
_env_file = ".env" if os.path.exists(".env") else ".env.example"


# Class chứa các cấu hình của ứng dụng
class Settings(BaseSettings):

    # Database
    DATABASE_URL: str

    # JWT
    # Khóa bí mật
    SECRET_KEY: str
    # Thuật toán JWT
    ALGORITHM: str = "HS256"
    # Access Token hết hạn sau 30 phút
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # Refresh Token hết hạn sau 7 ngày
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # App
    # Môi trường chạy app
    APP_ENV: str = "development"
    # Bật/tắt chế độ debug
    DEBUG: bool = False

    # Cấu hình đọc file .env
    model_config = SettingsConfigDict(
        # File chứa biến môi trường
        env_file=_env_file,
        # Encoding của file
        env_file_encoding="utf-8",
        # Bỏ qua biến không khai báo
        extra="ignore",
    )


# Cache settings để không tạo lại nhiều lần
@lru_cache
def get_settings() -> Settings:
    return Settings()


# Tạo settings dùng chung trong toàn project
settings = get_settings()
