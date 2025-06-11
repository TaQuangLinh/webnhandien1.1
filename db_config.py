# Cấu hình kết nối database cho hệ thống nhận diện khuôn mặt ký túc xá

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Thay đổi password theo cấu hình MySQL của bạn
    'database': 'db_ktx',  # Database cho hệ thống ký túc xá
    'charset': 'utf8mb4',
    'autocommit': True
}

# Cấu hình JWT
JWT_CONFIG = {
    'secret_key': 'dormitory_face_recognition_secret_2025',
    'algorithm': 'HS256',
    'token_expiry_hours': 24
}

# Cấu hình nhận diện khuôn mặt
FACE_RECOGNITION_CONFIG = {
    'min_score_threshold': 0.25,  # Ngưỡng điểm tối thiểu để nhận diện
    'auto_log_threshold': 0.4,    # Ngưỡng điểm để tự động ghi nhận ra vào
    'face_image_size': (112, 112) # Kích thước ảnh khuôn mặt chuẩn hóa
}

# Cấu hình đường dẫn
PATHS_CONFIG = {
    'datasets_dir': './datasets',
    'data_dir': './datasets/data',
    'backup_dir': './datasets/backup',
    'new_persons_dir': './datasets/new_persons',
    'features_dir': './datasets/face_features',
    'features_file': './datasets/face_features/feature'
}

# Cấu hình API
API_CONFIG = {
    'host': '0.0.0.0',
    'port': 5001,
    'debug': True
}
