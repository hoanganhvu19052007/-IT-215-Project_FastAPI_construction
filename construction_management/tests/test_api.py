import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, get_db

# Đăng ký SQLite in-memory database cho bộ test
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# --- TEST HEALTH CHECK ---
def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

    res_root = client.get("/")
    assert res_root.status_code == 200
    assert res_root.json()["success"] is True


# --- TEST AUTHENTICATION ---
def test_auth_flow(client):
    # 1. Register User 1 (Owner)
    reg_res = client.post(
        "/auth/register",
        json={
            "email": "owner@example.com",
            "password": "password123",
            "full_name": "Site Owner",
        },
    )
    assert reg_res.status_code == 201
    assert reg_res.json()["email"] == "owner@example.com"

    # 2. Register User 1 duplicate email error (Case lỗi - 400)
    dup_res = client.post(
        "/auth/register",
        json={
            "email": "owner@example.com",
            "password": "password123",
            "full_name": "Duplicate Owner",
        },
    )
    assert dup_res.status_code == 400
    assert dup_res.json()["success"] is False

    # 3. Register Invalid Data format (Case lỗi - 422)
    invalid_reg = client.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "password": "123",
            "full_name": "",
        },
    )
    assert invalid_reg.status_code == 422
    assert invalid_reg.json()["success"] is False

    # 4. Login User 1 wrong password (Case lỗi - 401)
    wrong_login = client.post(
        "/auth/login",
        json={
            "email": "owner@example.com",
            "password": "wrongpassword",
        },
    )
    assert wrong_login.status_code == 401
    assert wrong_login.json()["success"] is False

    # 5. Login User 1 correct credentials (Case đúng - 200)
    login_res = client.post(
        "/auth/login",
        json={
            "email": "owner@example.com",
            "password": "password123",
        },
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()


# --- TEST USER & PERMISSIONS ---
def test_user_me_and_admin_list(client):
    # Register User
    client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "password123", "full_name": "Normal User"},
    )
    login = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # GET /users/me (Case đúng - 200)
    me_res = client.get("/users/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "user@example.com"

    # GET /users/me without token (Case lỗi - 401)
    no_token_res = client.get("/users/me")
    assert no_token_res.status_code == 401

    # GET /users as non-admin (Case lỗi - 403)
    admin_list_res = client.get("/users", headers=headers)
    assert admin_list_res.status_code == 403


# --- TEST CONSTRUCTION SITE & MEMBERS ---
def test_site_flow(client):
    # 1. Register Owner & Member
    client.post(
        "/auth/register",
        json={"email": "owner@site.com", "password": "password123", "full_name": "Site Owner"},
    )
    client.post(
        "/auth/register",
        json={"email": "member@site.com", "password": "password123", "full_name": "Site Member"},
    )
    client.post(
        "/auth/register",
        json={"email": "stranger@site.com", "password": "password123", "full_name": "Stranger"},
    )

    owner_login = client.post(
        "/auth/login",
        json={"email": "owner@site.com", "password": "password123"},
    )
    owner_headers = {"Authorization": f"Bearer {owner_login.json()['access_token']}"}

    member_login = client.post(
        "/auth/login",
        json={"email": "member@site.com", "password": "password123"},
    )
    member_headers = {"Authorization": f"Bearer {member_login.json()['access_token']}"}

    stranger_login = client.post(
        "/auth/login",
        json={"email": "stranger@site.com", "password": "password123"},
    )
    stranger_headers = {"Authorization": f"Bearer {stranger_login.json()['access_token']}"}

    # 2. Create Construction Site (Case đúng - 201)
    create_site_res = client.post(
        "/construction-sites",
        json={"name": "Dự án Tòa nhà Landmark", "description": "Xây dựng tòa nhà 50 tầng"},
        headers=owner_headers,
    )
    assert create_site_res.status_code == 201
    site_id = create_site_res.json()["id"]

    # 3. List Sites of owner (Case đúng - 200)
    list_res = client.get("/construction-sites?search=Landmark", headers=owner_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    # 4. Stranger tries to access site (Case lỗi - 403)
    stranger_get = client.get(f"/construction-sites/{site_id}", headers=stranger_headers)
    assert stranger_get.status_code == 403

    # 5. Add Member to Site (Case đúng - 201)
    # member user_id = 2
    add_member_res = client.post(
        f"/construction-sites/{site_id}/members?user_id=2&role=MEMBER",
        headers=owner_headers,
    )
    assert add_member_res.status_code == 201

    # 6. Add Duplicate Member to Site (Case lỗi - 400)
    dup_member_res = client.post(
        f"/construction-sites/{site_id}/members?user_id=2&role=MEMBER",
        headers=owner_headers,
    )
    assert dup_member_res.status_code == 400

    # 7. Member now accesses site (Case đúng - 200)
    member_get = client.get(f"/construction-sites/{site_id}", headers=member_headers)
    assert member_get.status_code == 200

    # 8. Member tries to update site (Case lỗi - 403)
    member_update = client.put(
        f"/construction-sites/{site_id}",
        json={"name": "Đổi tên bởi member"},
        headers=member_headers,
    )
    assert member_update.status_code == 403

    # 9. Owner updates site (Case đúng - 200)
    owner_update = client.put(
        f"/construction-sites/{site_id}",
        json={"name": "Dự án Tòa nhà Landmark 81"},
        headers=owner_headers,
    )
    assert owner_update.status_code == 200
    assert owner_update.json()["name"] == "Dự án Tòa nhà Landmark 81"


# --- TEST WORK ITEMS FLOW ---
def test_work_item_flow(client):
    # Setup users and site
    client.post("/auth/register", json={"email": "owner2@site.com", "password": "password123", "full_name": "Owner 2"})
    client.post("/auth/register", json={"email": "worker@site.com", "password": "password123", "full_name": "Worker"})

    o_headers = {"Authorization": f"Bearer {client.post('/auth/login', json={'email': 'owner2@site.com', 'password': 'password123'}).json()['access_token']}"}
    w_headers = {"Authorization": f"Bearer {client.post('/auth/login', json={'email': 'worker@site.com', 'password': 'password123'}).json()['access_token']}"}

    site_res = client.post("/construction-sites", json={"name": "Cầu Vượt Nguyễn Văn Linh"}, headers=o_headers)
    site_id = site_res.json()["id"]

    # Add worker as member
    client.post(f"/construction-sites/{site_id}/members?user_id=2&role=MEMBER", headers=o_headers)

    # 1. Create Work Item assigned to Worker (Case đúng - 201)
    wi_res = client.post(
        f"/construction-sites/{site_id}/work-items",
        json={
            "site_id": site_id,
            "title": "Thi công móng đài cọc",
            "description": "Đổ bê tông móng cọc D600",
            "priority": "HIGH",
            "assignee_id": 2,
        },
        headers=o_headers,
    )
    assert wi_res.status_code == 201
    item_id = wi_res.json()["id"]

    # 2. Assignee creates work item with non-existent user_id (Case lỗi - 400)
    bad_wi = client.post(
        f"/construction-sites/{site_id}/work-items",
        json={"site_id": site_id, "title": "Công việc sai user", "assignee_id": 999},
        headers=o_headers,
    )
    assert bad_wi.status_code == 400

    # 3. Worker views my-tasks (Case đúng - 200)
    my_tasks = client.get("/work-items/my-tasks", headers=w_headers)
    assert my_tasks.status_code == 200
    assert len(my_tasks.json()) == 1

    # 4. Worker updates status of work item (Case đúng - 200)
    status_update = client.patch(
        f"/work-items/{item_id}/status?new_status=IN_PROGRESS",
        headers=w_headers,
    )
    assert status_update.status_code == 200
    assert status_update.json()["status"] == "IN_PROGRESS"

    # 5. Worker tries to update title (Forbidden - 403)
    worker_title_update = client.patch(
        f"/work-items/{item_id}",
        json={"title": "Tự ý đổi tên công việc"},
        headers=w_headers,
    )
    assert worker_title_update.status_code == 403

    # 6. List work items with filters (Case đúng - 200)
    list_wi = client.get(
        f"/construction-sites/{site_id}/work-items?status=IN_PROGRESS&priority=HIGH&search=m%C3%B3ng",
        headers=o_headers,
    )
    assert list_wi.status_code == 200
    assert len(list_wi.json()) == 1

    # 7. Owner deletes work item (Case đúng - 204)
    del_wi = client.delete(f"/work-items/{item_id}", headers=o_headers)
    assert del_wi.status_code == 204

    # 8. Get deleted work item (Case lỗi - 404)
    get_deleted = client.get(f"/work-items/{item_id}", headers=o_headers)
    assert get_deleted.status_code == 404
