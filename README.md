# Sport Booking API

Backend Django REST Framework và MongoEngine cho hệ thống đặt sân, giỏ hàng và bán sản phẩm thể thao.

## Công nghệ sử dụng

- Python
- Django REST Framework
- MongoEngine
- MongoDB Atlas
- JWT Authentication
- Mongomock cho integration test

## Cài đặt

Tạo môi trường ảo:

```bash
python -m venv venv
```

Kích hoạt môi trường ảo trên Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Cài đặt thư viện:

```powershell
pip install -r requirements.txt
```

Tạo file `.env` dựa trên `.env.example`:

```powershell
Copy-Item .env.example .env
```

Cập nhật các giá trị sau trong `.env`:

- `MONGO_URI`
- `SECRET_KEY`
- `JWT_SECRET`

Chạy migrate cho các thành phần Django mặc định:

```powershell
python manage.py migrate
```

Khởi động server:

```powershell
python manage.py runserver
```

API mặc định:

```text
http://127.0.0.1:8000/api/
```

Health check:

```text
GET http://127.0.0.1:8000/api/health/
```

## Chạy kiểm tra

Kiểm tra cấu hình:

```powershell
python manage.py check
```

Chạy toàn bộ test:

```powershell
python manage.py test
```

Integration test mặc định sử dụng `mongomock`. Test không đọc, sửa hoặc xóa dữ liệu trên MongoDB Atlas.

## Quy trình nhánh Git

- `main`: chỉ chứa phiên bản đã hoàn thành và ổn định.
- `develop`: nhánh tích hợp backend và frontend.
- `feature/*`: phát triển chức năng mới.
- `fix/*`: sửa lỗi và đồng bộ API.
- `test/*`: bổ sung hoặc kiểm tra integration test.

Không push code đang phát triển trực tiếp vào `main`.
