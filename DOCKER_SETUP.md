# 🐳 Hướng dẫn sử dụng Docker cho Hệ thống Nhận diện Khuôn mặt Ký túc xá

## 📋 Yêu cầu hệ thống

- **Docker Desktop** (Windows/Mac) hoặc **Docker Engine** (Linux)
- **Docker Compose** v3.8+
- **RAM**: Tối thiểu 4GB, khuyến nghị 8GB+
- **Ổ cứng**: Tối thiểu 10GB trống

## 🚀 Cách sử dụng nhanh

### 1. Tải về và giải nén
```bash
# Tải về source code hoặc clone repository
git clone <repository-url>
cd face-recognition
```

### 2. Chạy hệ thống (Development)
```bash
# Khởi động tất cả services
docker-compose up -d

# Xem logs
docker-compose logs -f

# Dừng hệ thống
docker-compose down
```

### 3. Truy cập hệ thống
- **Ứng dụng chính**: http://localhost:5001
- **phpMyAdmin**: http://localhost:81
- **Tài khoản mặc định**: admin / 123

## 📁 Cấu trúc files

```
face-recognition/
├── docker-compose.yml              # File chính cho development
├── docker-compose.production.yml   # File cho production
├── mysql-config/
│   └── my.cnf                      # Cấu hình MySQL
├── Database/
│   └── db_ktx.sql                  # Database schema và data mẫu
├── datasets/                       # Dữ liệu training (sẽ được tạo)
├── logs/                          # Log files (sẽ được tạo)
└── static/                        # Static files
```

## ⚙️ Cấu hình chi tiết

### Services được cung cấp:

1. **MySQL 8.0**
   - Port: 3307
   - Database: `db_ktx`
   - User: `root` (no password)
   - Auto-import: `Database/db_ktx.sql`

2. **Face Recognition API**
   - Port: 5001
   - Image: `talinh/webnhandien:latest`
   - Auto-restart khi crash

3. **phpMyAdmin**
   - Port: 81
   - Quản lý database qua web interface

## 🔧 Các lệnh hữu ích

### Quản lý containers
```bash
# Xem trạng thái
docker-compose ps

# Restart một service
docker-compose restart face-recognition

# Xem logs của một service
docker-compose logs mysql

# Vào shell của container
docker-compose exec face-recognition bash
docker-compose exec mysql mysql -u root -p
```

### Backup và Restore
```bash
# Backup database
docker-compose exec mysql mysqldump -u root db_ktx > backup.sql

# Restore database
docker-compose exec -T mysql mysql -u root db_ktx < backup.sql
```

### Cập nhật image
```bash
# Pull image mới nhất
docker-compose pull face-recognition

# Restart với image mới
docker-compose up -d face-recognition
```

## 🏭 Production Deployment

### 1. Sử dụng file production
```bash
# Chạy với cấu hình production
docker-compose -f docker-compose.production.yml up -d
```

### 2. Thay đổi passwords (QUAN TRỌNG!)
Sửa file `docker-compose.production.yml`:
```yaml
environment:
  MYSQL_ROOT_PASSWORD: "your_secure_password_here"
  MYSQL_PASSWORD: "ktx_secure_password"
```

### 3. Cấu hình SSL (tùy chọn)
- Thêm certificates vào `nginx/ssl/`
- Cấu hình `nginx/nginx.conf`

## 🐛 Troubleshooting

### Port đã được sử dụng
```bash
# Thay đổi port trong .env
APP_PORT=5002
MYSQL_PORT=3308
PHPMYADMIN_PORT=82
```

### MySQL không khởi động
```bash
# Xem logs MySQL
docker-compose logs mysql

# Reset MySQL data
docker-compose down -v
docker-compose up -d
```

### Face Recognition không kết nối được database
```bash
# Kiểm tra MySQL đã sẵn sàng chưa
docker-compose exec mysql mysqladmin ping -u root

# Restart face-recognition service
docker-compose restart face-recognition
```

### Xóa tất cả data và bắt đầu lại
```bash
# CẢNH BÁO: Lệnh này sẽ xóa tất cả dữ liệu!
docker-compose down -v
docker system prune -a
docker-compose up -d
```

## 📊 Monitoring

### Xem resource usage
```bash
# Xem CPU, RAM usage
docker stats

# Xem disk usage
docker system df
```

### Health checks
```bash
# Kiểm tra health của services
docker-compose ps
```

## 🔐 Security Notes

1. **Đổi passwords mặc định** trong production
2. **Tắt phpMyAdmin** trong production nếu không cần
3. **Sử dụng firewall** để hạn chế truy cập
4. **Backup định kỳ** database và datasets
5. **Cập nhật images** thường xuyên

## 📞 Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra logs: `docker-compose logs`
2. Kiểm tra Docker Desktop đã chạy chưa
3. Đảm bảo ports không bị conflict
4. Restart Docker Desktop nếu cần

---

**🎯 Lưu ý**: File này được tạo để chia sẻ cho người khác sử dụng. Đảm bảo họ có Docker Desktop và làm theo hướng dẫn từng bước.
