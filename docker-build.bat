@echo off
echo ========================================
echo    DORMITORY FACE RECOGNITION DOCKER
echo         Build and Push to Hub
echo ========================================

:: Cau hinh
set USERNAME=talinh
set IMAGE=nhandiensvktx
set /p TAG=Nhap ten tag (vi du: v1.2.3): 

:: Kiem tra tag co trong hay khong
if "%TAG%"=="" (
    echo [ERROR] Ban chua nhap TAG!
    pause
    exit /b 1
)

echo [1] Kiem tra Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker chua cai dat! Tai tai: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

echo [INFO] Docker da cai dat. Kiem tra ket noi...
timeout /t 2 >nul
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Docker co the chua khoi dong hoan toan.
    echo [INFO] Dang thu ket noi Docker...
    timeout /t 5 >nul
)

echo [2] Dang nhap Docker Hub...
docker login
if %errorlevel% neq 0 (
    echo [ERROR] Dang nhap that bai!
    pause
    exit /b 1
)

echo [3] Build image (co the mat 10-20 phut)...
docker build -t %USERNAME%/%IMAGE%:latest .
if %errorlevel% neq 0 (
    echo [ERROR] Build that bai!
    pause
    exit /b 1
)

echo [4] Tao tag version: %TAG%
docker tag %USERNAME%/%IMAGE%:latest %USERNAME%/%IMAGE%:%TAG%

echo [5] Push image len Docker Hub...
docker push %USERNAME%/%IMAGE%:latest
docker push %USERNAME%/%IMAGE%:%TAG%

echo.
echo ========================================
echo [SUCCESS] HOAN THANH!
echo ========================================
echo Da push cac image:
echo - %USERNAME%/%IMAGE%:latest
echo - %USERNAME%/%IMAGE%:%TAG%
echo.
echo Chay thu: docker run -p 5000:5000 %USERNAME%/%IMAGE%:latest
echo Hoac: docker-compose up -d
echo ========================================
pause
