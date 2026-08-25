# Construction Management API

API quản lý công trình xây dựng với FastAPI, SQLAlchemy và JWT authentication.

## 📋 Tính năng

- 🔐 **Authentication**: Đăng ký, đăng nhập, refresh token (JWT)
- 👤 **User Management**: Xem thông tin user, danh sách user
- 🏗️ **Construction Sites**: Quản lý công trình (owner: 1-N users)
- 👥 **Site Members**: Thành viên công trình (N-N relationship via SiteMember)
- ✏️ **Work Items**: Hạng mục thi công (với assignee, status, priority, due_date)
- 🛡️ **Exception Handling**: Xử lý lỗi toàn cục
- 📚 **Swagger UI**: API documentation tương tác

## 📊 Cơ sở dữ liệu

### Mô hình dữ liệu

```
users (1) -------- (N) construction_sites
  |                        |
  | (1)                    | (1)
  |                        |
  +------- site_members ---+
  |              |
  | (1)          | (N)
  |              |
work_items ------+
```

### Bảng chính

**users**
- `id` (PK)
- `email` (UNIQUE, NOT NULL)
- `password_hash` (NOT NULL)
- `full_name` (NOT NULL)
- `role` (DEFAULT: USER) - USER, ADMIN
- `is_active` (DEFAULT: TRUE)
- `created_at`

**construction_sites**
- `id` (PK)
- `name` (NOT NULL)
- `description` (NULLABLE)
- `owner_id` (FK → users.id)
- `created_at`

**site_members**
- `site_id` (FK → construction_sites.id, PK)
- `user_id` (FK → users.id, PK)
- `role` - OWNER, MEMBER
- `joined_at`

**work_items**
- `id` (PK)
- `site_id` (FK → construction_sites.id)
- `title` (NOT NULL)
- `description` (NULLABLE)
- `assignee_id` (FK → users.id, NULLABLE)
- `status` (DEFAULT: TODO) - TODO, IN_PROGRESS, DONE
- `priority` (DEFAULT: MEDIUM) - LOW, MEDIUM, HIGH
- `due_date` (NULLABLE)
- `created_at`

## 🚀 Cài đặt

### 1. Clone repository
```bash
git clone <repository-url>
cd construction_management
```

### 2. Tạo virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 4. Cấu hình environment
```bash
cp .env.example .env
```

Sửa file `.env` với các giá trị phù hợp:
```
DATABASE_URL=sqlite:///./test.db
SECRET_KEY=your-super-secret-key-here
DEBUG=True
```

### 5. Chạy server
```bash
python -m uvicorn app.main:app --reload
```

Server chạy tại: `http://localhost:8000`

## 📚 API Endpoints

### Health Check
```
GET /health
```

### Authentication
```
POST /auth/register
  Body: {
    "email": "user@example.com",
    "password": "password123",
    "full_name": "John Doe"
  }
  Response: 201 Created

POST /auth/login
  Body: {
    "email": "user@example.com",
    "password": "password123"
  }
  Response: 200 OK
  {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "bearer",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }

POST /auth/refresh
  Body: {"refresh_token": "..."}
  Response: 200 OK
```

### Users
```
GET /users/me
  Headers: Authorization: Bearer <token>
  Response: 200 OK - Current user info

GET /users/
  Headers: Authorization: Bearer <token>
  Response: 200 OK - List all users (Admin only)

GET /users/{user_id}
  Headers: Authorization: Bearer <token>
  Response: 200 OK - User info by ID
```

## 📖 Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔑 Environment Variables

```
DATABASE_URL         - SQLAlchemy connection string
SECRET_KEY           - JWT signing key
ALGORITHM            - JWT algorithm (default: HS256)
ACCESS_TOKEN_EXPIRE_MINUTES  - Access token expiry (default: 30)
REFRESH_TOKEN_EXPIRE_DAYS    - Refresh token expiry (default: 7)
APP_ENV              - Environment (development/production)
DEBUG                - Enable debug mode
```

## 📁 Cấu trúc dự án

```
construction_management/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app, include routers, middleware
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Đọc biến môi trường từ .env
│   │   ├── exceptions.py       # Exception handlers
│   │   └── security.py         # Hash password, JWT encode/decode, get_current_user
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py         # engine, SessionLocal, Base, get_db
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py             # Model User
│   │   ├── site.py             # Model ConstructionSite, SiteMember
│   │   └── work_item.py        # Model WorkItem
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py             # RegisterRequest, LoginRequest, Token
│   │   ├── user.py             # UserCreate, UserResponse, UserUpdate
│   │   ├── site.py             # SiteCreate, SiteResponse
│   │   ├── site_member.py      # SiteMemberCreate, SiteMemberResponse
│   │   └── work_item.py        # WorkItemCreate, WorkItemResponse
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py             # Register, Login, Refresh endpoints
│   │   ├── user.py             # User endpoints (me, list, get by id)
│   │   ├── site.py             # Site endpoints
│   │   ├── work_item.py        # WorkItem endpoints
│   │   └── health.py           # Health check
│   ├── services/
│   │   ├── __init__.py
│   │   └── (service files)     # Business logic
│   └── dependencies/
│       ├── __init__.py
│       └── (dependency files)  # get_current_user, role guards
├── .env.example                # Mẫu biến môi trường
├── requirements.txt            # Danh sách dependencies
└── README.md                   # Documentation
```

## 🤝 Contribution

Mọi đóng góp đều được chào đón! Vui lòng tạo pull request.

## 📝 License

MIT
