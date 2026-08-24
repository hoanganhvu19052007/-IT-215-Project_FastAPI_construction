from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# Tạo kết nối đến database
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)


# Tạo Session để làm việc với database
sessionlocal = sessionmaker(
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


# Tạo Base để các model kế thừa
Base = declarative_base()


# Tạo session database cho mỗi request
def get_db():
    db = sessionlocal()
    try:
        # Trả session cho API sử dụng
        yield db
    finally:
        # Đóng session sau khi xử lý xong
        db.close()


# Kiểm tra database có kết nối được không
def check_db_connection() -> bool:
    try:
        # Mở kết nối đến database
        with engine.connect() as conn:

            # Thực hiện câu lệnh kiểm tra đơn giản
            conn.execute(text("SELECT 1"))

        # Kết nối thành công
        return True

    except Exception as e:
        # Kết nối thất bại
        print(f"Database connection failed: {e}")
        return False


# Khởi tạo các bảng trong database
def init_db() -> None:
    # Import models để SQLAlchemy nhận biết các bảng
    from app import models

    # Tạo bảng nếu bảng chưa tồn tại
    Base.metadata.create_all(bind=engine)
