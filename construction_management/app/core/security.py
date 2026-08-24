from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Cấu hình bcrypt để mã hóa (hash) mật khẩu
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


# Hash mật khẩu trước khi lưu vào database
def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


# Kiểm tra mật khẩu người dùng nhập
# với mật khẩu đã được hash trong database
def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return pwd_context.verify(
        plain_password,
        hashed_password,
    )


# Tạo Access Token dùng để xác thực người dùng
def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    # Sao chép dữ liệu để tạo nội dung cho token
    to_encode = data.copy()

    # Tính thời gian hết hạn của Access Token
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    # Thêm thời gian hết hạn và loại token
    to_encode.update(
        {
            "exp": expire,
            "type": "access",
        }
    )

    # Mã hóa và tạo JWT
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


# Tạo Refresh Token dùng để cấp lại Access Token
def create_refresh_token(data: dict) -> str:
    # Sao chép dữ liệu để tạo nội dung cho token
    to_encode = data.copy()

    # Refresh Token có thời gian sống dài hơn Access Token
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    # Thêm thời gian hết hạn và loại token
    to_encode.update(
        {
            "exp": expire,
            "type": "refresh",
        }
    )

    # Mã hóa và tạo JWT
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


# Giải mã và kiểm tra JWT
def decode_token(token: str) -> Optional[dict]:
    try:
        # Giải mã token bằng SECRET_KEY
        # Nếu token hợp lệ thì trả về dữ liệu bên trong
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

    except JWTError:
        # Token sai, hết hạn hoặc không hợp lệ
        return None
