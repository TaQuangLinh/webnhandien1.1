#!/bin/bash

echo "========================================"
echo "   HỆ THỐNG NHẬN DIỆN KHUÔN MẶT KTX"
echo "        Quick Start Script"
echo "========================================"

# Kiểm tra Docker
echo "[1] Kiểm tra Docker..."
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker chưa cài đặt!"
    echo "Tải tại: https://www.docker.com/products/docker-desktop/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "[ERROR] Docker Compose chưa cài đặt!"
    echo "Cài đặt: sudo apt-get install docker-compose"
    exit 1
fi

echo "[INFO] Docker đã cài đặt."

# Kiểm tra file .env
if [ ! -f .env ]; then
    echo "[INFO] Tạo file .env từ .env.example..."
    cp .env.example .env
    echo "[WARNING] Vui lòng kiểm tra cấu hình trong file .env"
fi

# Tạo thư mục cần thiết
echo "[2] Tạo thư mục cần thiết..."
mkdir -p datasets/{data,backup,new_persons,face_features}
mkdir -p logs/mysql
mkdir -p static/uploads
mkdir -p backups

# Set permissions
chmod -R 755 datasets logs static backups

# Khởi động hệ thống
echo "[3] Khởi động hệ thống..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "[ERROR] Khởi động thất bại!"
    echo "Kiểm tra Docker daemon đã chạy chưa."
    exit 1
fi

echo ""
echo "========================================"
echo "[SUCCESS] HỆ THỐNG ĐÃ KHỞI ĐỘNG!"
echo "========================================"
echo ""
echo "Truy cập hệ thống:"
echo "- Ứng dụng chính: http://localhost:5001"
echo "- phpMyAdmin:     http://localhost:81"
echo "- Tài khoản mặc định: admin / password"
echo ""
echo "Các lệnh hữu ích:"
echo "- Xem logs:       docker-compose logs -f"
echo "- Dừng hệ thống:  docker-compose down"
echo "- Khởi động lại:  docker-compose restart"
echo ""

# Mở trình duyệt (nếu có desktop environment)
if command -v xdg-open &> /dev/null; then
    echo "Đang mở trình duyệt..."
    sleep 3
    xdg-open http://localhost:5001 &
elif command -v open &> /dev/null; then
    echo "Đang mở trình duyệt..."
    sleep 3
    open http://localhost:5001 &
fi

echo ""
echo "Nhấn Ctrl+C để thoát hoặc Enter để xem logs..."
read -r
docker-compose logs -f
