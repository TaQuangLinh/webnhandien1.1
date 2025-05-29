# Dockerfile tối ưu cho Face Recognition System
FROM python:3.11-slim

# Metadata
LABEL maintainer="talinh"
LABEL description="Website nhận diện sinh viên ra vào ký tý xá"
LABEL version="2.0"

# Environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# System dependencies tối thiểu
RUN apt-get update && apt-get install -y \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install PyTorch CPU-only (smaller size)
RUN pip install --no-cache-dir \
    torch==2.6.0+cpu \
    torchvision==0.21.0+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Install core packages
RUN pip install --no-cache-dir \
    Flask==3.1.0 \
    flask-cors==5.0.1 \
    numpy==1.26.4 \
    pandas==2.2.3 \
    opencv-python==4.11.0.86 \
    Pillow==11.1.0 \
    scipy==1.15.2 \
    scikit-image==0.22.0 \
    mysql-connector-python==9.2.0 \
    onnxruntime==1.16.3 \
    requests==2.32.3 \
    PyYAML==6.0.1 \
    python-dateutil==2.9.0.post0

# mới thêm 
RUN pip install --no-cache-dir -r requirements.txt


# Copy source code
COPY . .

# Create directories
RUN mkdir -p datasets/data datasets/backup datasets/new_persons datasets/face_features

# Use Docker config
RUN cp db_config_docker.py db_config.py

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/api/test || exit 1

EXPOSE 5000
CMD ["python", "api.py"]
