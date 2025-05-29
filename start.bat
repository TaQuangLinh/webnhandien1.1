@echo off
echo ========================================
echo    HE THONG NHAN DIEN KHUON MAT KTX
echo         Quick Start Script
echo ========================================

:: Kiem tra Docker
echo [1] Kiem tra Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker chua cai dat!
    echo Tai tai: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

echo [INFO] Docker da cai dat.

:: Kiem tra file .env
if not exist .env (
    echo [INFO] Tao file .env tu .env.example...
    copy .env.example .env >nul
    echo [WARNING] Vui long kiem tra cau hinh trong file .env
)

:: Tao thu muc can thiet
echo [2] Tao thu muc can thiet...
if not exist datasets mkdir datasets
if not exist datasets\data mkdir datasets\data
if not exist datasets\backup mkdir datasets\backup
if not exist datasets\new_persons mkdir datasets\new_persons
if not exist datasets\face_features mkdir datasets\face_features
if not exist logs mkdir logs
if not exist logs\mysql mkdir logs\mysql
if not exist static mkdir static
if not exist static\uploads mkdir static\uploads
if not exist backups mkdir backups

:: Khoi dong he thong
echo [3] Khoi dong he thong...
docker-compose up -d

if %errorlevel% neq 0 (
    echo [ERROR] Khoi dong that bai!
    echo Kiem tra Docker Desktop da chay chua.
    pause
    exit /b 1
)

echo.
echo ========================================
echo [SUCCESS] HE THONG DA KHOI DONG!
echo ========================================
echo.
echo Truy cap he thong:
echo - Ung dung chinh: http://localhost:5001
echo - phpMyAdmin:     http://localhost:81
echo - MySQL:          localhost:3308
echo - Tai khoan mac dinh: admin / password
echo.
echo Cac lenh huu ich:
echo - Xem logs:       docker-compose logs -f
echo - Dung he thong:  docker-compose down
echo - Khoi dong lai:  docker-compose restart
echo.
echo Dang mo trinh duyet...
timeout /t 3 >nul
start http://localhost:5001

echo.
echo Nhan phim bat ky de dong...
pause >nul
