# API Test Checklist & Integration Testing Summary

Dưới đây là bảng checklist kiểm thử toàn bộ hệ thống API Construction Management System, áp dụng cho việc test trực tiếp qua **Swagger UI (`http://localhost:8000/docs`)** hoặc **Postman**.

---

## 1. Nhóm API Xác thực (Authentication - `/auth`)

| STT | Endpoint | Method | Trường hợp test | Input / Body | Trạng thái kỳ vọng | Kết quả mong đợi |
|-----|----------|--------|-----------------|--------------|--------------------|------------------|
| 1.1 | `/auth/register` | `POST` | Đăng ký thành công | Email mới, password, full_name | `201 Created` | Trả về thông tin user (ID, email, role, is_active), không lộ password_hash. |
| 1.2 | `/auth/register` | `POST` | Email đã tồn tại | Email đã trùng trong DB | `400 Bad Request` | `message: "Email đã được sử dụng"` |
| 1.3 | `/auth/register` | `POST` | Dữ liệu không hợp lệ | Email sai định dạng, pass ngắn | `422 Unprocessable` | Detail danh sách lỗi validation |
| 1.4 | `/auth/login` | `POST` | Đăng nhập đúng | Email & Password hợp lệ | `200 OK` | Trả về `access_token` và `token_type: "bearer"` |
| 1.5 | `/auth/login` | `POST` | Đăng nhập sai pass | Sai password | `401 Unauthorized` | `message: "Email hoặc mật khẩu không đúng"` |
| 1.6 | `/auth/login` | `POST` | Tài khoản bị khóa | Account có `is_active=False` | `403 Forbidden` | `message: "Tài khoản đã bị vô hiệu hóa"` |

---

## 2. Nhóm API Người dùng (Users - `/users`)

| STT | Endpoint | Method | Trường hợp test | Input / Header | Trạng thái kỳ vọng | Kết quả mong đợi |
|-----|----------|--------|-----------------|----------------|--------------------|------------------|
| 2.1 | `/users/me` | `GET` | Xem profile cá nhân | Token hợp lệ trong Header | `200 OK` | Trả về thông tin user đang đăng nhập |
| 2.2 | `/users/me` | `GET` | Chưa đăng nhập | Không truyền Token / Token sai | `401 Unauthorized` | `message: "Token không hợp lệ hoặc đã hết hạn"` |
| 2.3 | `/users` | `GET` | Admin xem danh sách user | Admin Token | `200 OK` | Trả về mảng danh sách người dùng |
| 2.4 | `/users` | `GET` | User thường xem danh sách | Non-Admin Token | `403 Forbidden` | `message: "Chỉ ADMIN mới có quyền thực hiện thao tác này"` |

---

## 3. Nhóm API Công trình thi công (Construction Sites - `/construction-sites`)

| STT | Endpoint | Method | Trường hợp test | Input / Params | Trạng thái kỳ vọng | Kết quả mong đợi |
|-----|----------|--------|-----------------|----------------|--------------------|------------------|
| 3.1 | `/construction-sites` | `POST` | Tạo công trình mới | name, description + Token | `201 Created` | Tạo site mới, tự động gán creator làm OWNER |
| 3.2 | `/construction-sites` | `GET` | Lấy danh sách công trình | Token + `search` query | `200 OK` | Trả về các công trình user làm owner hoặc member |
| 3.3 | `/construction-sites/{id}` | `GET` | Xem chi tiết công trình | ID hợp lệ (Owner/Member) | `200 OK` | Trả về thông tin chi tiết công trình |
| 3.4 | `/construction-sites/{id}` | `GET` | Ngẫu nhiên truy cập site người khác | User không thuộc công trình | `403 Forbidden` | `message: "Bạn không có quyền truy cập công trình này"` |
| 3.5 | `/construction-sites/{id}` | `PUT` | Cập nhật thông tin site | Owner Token + name mới | `200 OK` | Cập nhật thông tin site |
| 3.6 | `/construction-sites/{id}` | `PUT` | Thành viên cố cập nhật site | Member Token | `403 Forbidden` | `message: "Chỉ chủ công trình mới được phép cập nhật"` |
| 3.7 | `/construction-sites/{id}` | `DELETE` | Xóa mềm công trình | Owner Token | `204 No Content` | Cập nhật `is_deleted=True`, ẩn khỏi danh sách |
| 3.8 | `/construction-sites/{id}` | `GET` | Xem site đã xóa | ID site đã xóa | `404 Not Found` | `message: "Công trình không tồn tại"` |

---

## 4. Nhóm API Thành viên công trình (Site Members - `/construction-sites/{id}/members`)

| STT | Endpoint | Method | Trường hợp test | Input / Params | Trạng thái kỳ vọng | Kết quả mong đợi |
|-----|----------|--------|-----------------|----------------|--------------------|------------------|
| 4.1 | `/members` | `POST` | Owner thêm member mới | `user_id`, `role=MEMBER` | `201 Created` | Thêm thành viên vào công trình |
| 4.2 | `/members` | `POST` | Thêm trùng thành viên | `user_id` đã có trong site | `400 Bad Request` | `message: "Người dùng đã là thành viên của công trình này"` |
| 4.3 | `/members` | `GET` | Xem danh sách thành viên | Token thuộc site | `200 OK` | Trả về danh sách thành viên |
| 4.4 | `/members/{user_id}`| `PATCH`| Cập nhật vai trò member | `role=OWNER` | `200 OK` | Cập nhật vai trò thành công |
| 4.5 | `/members/{user_id}`| `DELETE`| Xóa member khỏi site | Owner xóa Member | `204 No Content` | Thành viên bị xóa khỏi site |
| 4.6 | `/members/{user_id}`| `DELETE`| Cố xóa Owner chính | Owner ID | `400 Bad Request` | `message: "Không thể xóa Owner chính của công trình"` |

---

## 5. Nhóm API Hạng mục thi công (Work Items - `/work-items`)

| STT | Endpoint | Method | Trường hợp test | Input / Params | Trạng thái kỳ vọng | Kết quả mong đợi |
|-----|----------|--------|-----------------|----------------|--------------------|------------------|
| 5.1 | `/work-items` | `POST` | Tạo công việc thi công | title, priority, assignee_id | `201 Created` | Tạo work item thành công |
| 5.2 | `/work-items` | `POST` | Giao việc cho người ngoài site | assignee_id không thuộc site | `400 Bad Request` | `message: "Người được giao việc phải là thành viên hoặc owner..."` |
| 5.3 | `/work-items` | `GET` | Xem danh sách công việc site | `status`, `priority`, `search` | `200 OK` | Danh sách công việc có lọc và phân trang |
| 5.4 | `/my-tasks` | `GET` | Xem công việc được giao | Token người được giao | `200 OK` | Danh sách các task được giao cho user |
| 5.5 | `/work-items/{id}/status`| `PATCH`| Cập nhật nhanh trạng thái | `new_status=IN_PROGRESS` | `200 OK` | Trạng thái chuyển sang IN_PROGRESS |
| 5.6 | `/work-items/{id}` | `PATCH` | Worker cập nhật tiêu đề | Worker Token (non-owner) | `403 Forbidden` | `message: "Chỉ chủ công trình mới có quyền..."` |
| 5.7 | `/work-items/{id}` | `DELETE` | Xóa công việc | Owner Token | `204 No Content` | Xóa công việc thành công |
