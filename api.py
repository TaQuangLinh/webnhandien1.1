from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for, session
from flask_cors import CORS
import base64
import cv2
import numpy as np
import threading
import time
import torch
from face_detection.scrfd.detector import SCRFD
from face_recognition.arcface.model import iresnet_inference
from face_recognition.arcface.utils import compare_encodings, read_features
from face_alignment.alignment import norm_crop
import mysql.connector
from datetime import datetime
import os
import shutil
from torchvision import transforms
from add_persons import add_persons
from db_config import DB_CONFIG, JWT_CONFIG, FACE_RECOGNITION_CONFIG, API_CONFIG

app = Flask(__name__,
           template_folder='templates',
           static_folder='static',
           static_url_path='/static')
CORS(app, origins=['http://localhost:5001', 'http://127.0.0.1:5001'])

# Cấu hình session
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SESSION_TYPE'] = 'filesystem'

# Khởi tạo các biến global
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Face detector
detector = SCRFD(model_file="face_detection/scrfd/weights/scrfd_2.5g_bnkps.onnx")

# Face recognizer
recognizer = iresnet_inference(
    model_name="r100",
    path="face_recognition/arcface/weights/arcface_r100.pth",
    device=device
)

# Load features
print("\nĐang tải dữ liệu nhận diện...")
features = None
try:
    features = read_features(feature_path="./datasets/face_features/feature")
    if features is not None:
        images_names, images_embs = features
        print(f"✓ Đã tải dữ liệu: {len(images_names)} mẫu")
except Exception as e:
    print(f"! Lỗi khi tải dữ liệu: {str(e)}")

def connect_database():
    """Kết nối đến cơ sở dữ liệu"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except mysql.connector.Error as error:
        print(f"Lỗi kết nối database: {error}")
        return None

def ensure_access_logs_table():
    """Đảm bảo bảng access logs tồn tại"""
    try:
        connection = connect_database()
        if not connection:
            return False

        cursor = connection.cursor()

        # SQL tạo bảng access logs
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS `nv5_dormitory_access_logs` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `student_id` int(11) NOT NULL,
            `student_code` varchar(20) NOT NULL,
            `access_type` tinyint(1) NOT NULL COMMENT '1=Vào, 2=Ra',
            `access_time` int(11) NOT NULL,
            `gate_location` varchar(100) DEFAULT 'Cổng chính',
            `verification_method` varchar(50) DEFAULT 'Nhận diện khuôn mặt',
            `device_id` varchar(50) DEFAULT NULL,
            `device_name` varchar(100) DEFAULT NULL,
            `ip_address` varchar(45) DEFAULT NULL,
            `recognition_rate` float DEFAULT NULL,
            `notes` text DEFAULT NULL,
            `status` tinyint(1) DEFAULT 1,
            `created_time` int(11) NOT NULL,
            PRIMARY KEY (`id`),
            KEY `student_code` (`student_code`),
            KEY `access_time` (`access_time`),
            KEY `access_type` (`access_type`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

        cursor.execute(create_table_sql)
        connection.commit()

        # Kiểm tra xem có dữ liệu mẫu chưa
        cursor.execute("SELECT COUNT(*) as count FROM nv5_dormitory_access_logs")
        result = cursor.fetchone()

        if result[0] == 0:
            # Thêm một số dữ liệu mẫu
            current_time = int(datetime.now().timestamp())
            sample_data = [
                (1, 'SV001', 1, current_time - 3600, 'Cổng chính', 'Nhận diện khuôn mặt', 'DEVICE_001', 'Camera cổng chính', '192.168.1.100', 95.5, 'Nhận diện thành công', 1, current_time - 3600),
                (1, 'SV001', 2, current_time - 1800, 'Cổng chính', 'Nhận diện khuôn mặt', 'DEVICE_001', 'Camera cổng chính', '192.168.1.100', 92.3, 'Nhận diện thành công', 1, current_time - 1800),
                (2, 'SV002', 1, current_time - 900, 'Cổng phụ', 'Thẻ sinh viên', 'DEVICE_002', 'Đầu đọc thẻ cổng phụ', '192.168.1.101', None, 'Quét thẻ thành công', 1, current_time - 900)
            ]

            insert_sample_sql = """
                INSERT INTO nv5_dormitory_access_logs
                (student_id, student_code, access_type, access_time, gate_location,
                 verification_method, device_id, device_name, ip_address,
                 recognition_rate, notes, status, created_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            cursor.executemany(insert_sample_sql, sample_data)
            connection.commit()
            print("✅ Đã thêm dữ liệu mẫu cho access logs")

        cursor.close()
        connection.close()

        print("✅ Bảng access logs đã được tạo/kiểm tra thành công")
        return True

    except Exception as e:
        print(f"❌ Lỗi tạo bảng access logs: {str(e)}")
        return False

def get_person_name(connection, folder_name):
    """Lấy tên sinh viên từ database dựa vào folder name (student_code)"""
    try:
        cursor = connection.cursor(dictionary=True)

        # Làm sạch folder_name (loại bỏ khoảng trắng, ký tự đặc biệt)
        clean_folder_name = str(folder_name).strip()

        print(f"🔍 Tìm kiếm sinh viên với mã: '{clean_folder_name}' (độ dài: {len(clean_folder_name)})")

        # Thử tìm chính xác trước
        sql = """SELECT full_name, birth_date, student_code, room_number, class_name
                FROM nv5_dormitory_students
                WHERE student_code = %s AND status = 1"""
        cursor.execute(sql, (clean_folder_name,))
        result = cursor.fetchone()

        # Nếu không tìm thấy, thử tìm với LIKE
        if not result:
            print(f"🔍 Không tìm thấy chính xác, thử tìm với LIKE...")
            sql_like = """SELECT full_name, birth_date, student_code, room_number, class_name
                         FROM nv5_dormitory_students
                         WHERE student_code LIKE %s AND status = 1"""
            cursor.execute(sql_like, (f"%{clean_folder_name}%",))
            result = cursor.fetchone()

        # Debug: Hiển thị tất cả sinh viên có status = 1
        if not result:
            print(f"🔍 Debug: Tất cả sinh viên hoạt động trong database:")
            debug_sql = """SELECT student_code, full_name FROM nv5_dormitory_students WHERE status = 1 LIMIT 10"""
            cursor.execute(debug_sql)
            debug_results = cursor.fetchall()
            for debug_student in debug_results:
                print(f"  - '{debug_student['student_code']}': {debug_student['full_name']}")

        cursor.close()

        if result:
            print(f"✅ Tìm thấy sinh viên: {result}")
            if result['birth_date']:
                birthday = result['birth_date'].strftime("%d/%m/%Y")
                return {
                    'name': f"{result['full_name']} ({birthday})",
                    'student_code': result['student_code'],
                    'room_number': result['room_number'] or 'N/A',
                    'class_name': result['class_name'] or 'N/A',
                    'birth_date': birthday
                }
            else:
                return {
                    'name': result['full_name'] or 'N/A',
                    'student_code': result['student_code'],
                    'room_number': result['room_number'] or 'N/A',
                    'class_name': result['class_name'] or 'N/A',
                    'birth_date': None
                }
        else:
            print(f"❌ Không tìm thấy sinh viên với mã: '{clean_folder_name}'")
            return None
    except mysql.connector.Error as error:
        print(f"❌ Lỗi truy vấn database: {error}")
        return None

def process_frame(frame):
    """Xử lý frame và trả về kết quả nhận diện"""
    try:
        # Phát hiện khuôn mặt
        bboxes, landmarks = detector.detect(frame)

        results = []
        if bboxes is not None and len(bboxes) > 0:
            for i, (bbox, landmark) in enumerate(zip(bboxes, landmarks)):
                try:
                    # Căn chỉnh khuôn mặt
                    face_aligned = norm_crop(frame, landmark)

                    # Chuyển đổi từ BGR sang RGB
                    face_aligned = cv2.cvtColor(face_aligned, cv2.COLOR_BGR2RGB)

                    # Chuyển đổi từ HWC sang CHW
                    face_aligned = face_aligned.transpose(2, 0, 1)

                    # Trích xuất đặc trưng
                    face_tensor = torch.from_numpy(face_aligned).float()
                    face_tensor = face_tensor.to(device)
                    face_tensor = face_tensor.unsqueeze(0)  # Thêm batch dimension

                    # Chuẩn hóa ảnh
                    face_tensor = (face_tensor - 127.5) / 128.0

                    # Thêm detach() trước khi chuyển sang numpy
                    embedding = recognizer(face_tensor).detach().cpu().numpy()

                    # So sánh với database
                    if features is not None:
                        score, idx = compare_encodings(embedding, images_embs)
                        folder_name = images_names[idx]
                        score = float(score[0])  # Chuyển score từ array sang float

                        # Chỉ thêm kết quả nếu score >= ngưỡng cấu hình
                        if score >= FACE_RECOGNITION_CONFIG['min_score_threshold']:
                            connection = connect_database()
                            if connection:
                                try:
                                    # folder_name chính là student_code - kiểm tra trong database
                                    print(f"🔍 Nhận diện được mã: {folder_name} với score: {score:.2f}")
                                    student_info = get_person_name(connection, folder_name)

                                    if student_info:
                                        # Tìm thấy sinh viên trong database
                                        print(f"✅ Hiển thị thông tin sinh viên: {student_info['name']}")
                                        results.append({
                                            "bbox": bbox.tolist(),
                                            "score": score,
                                            "name": student_info['name'],
                                            "student_code": student_info['student_code'],
                                            "room_number": student_info['room_number'],
                                            "class_name": student_info['class_name'],
                                            "birth_date": student_info['birth_date'],
                                            "folder_name": folder_name,
                                            "found_in_db": True
                                        })
                                    else:
                                        # Không tìm thấy trong DB - hiển thị thông tin cơ bản
                                        print(f"❌ Không tìm thấy sinh viên {folder_name} trong database")
                                        results.append({
                                            "bbox": bbox.tolist(),
                                            "score": score,
                                            "name": f"Unknown ({folder_name})",
                                            "student_code": folder_name,
                                            "room_number": "Chưa có thông tin",
                                            "class_name": "Chưa có thông tin",
                                            "birth_date": None,
                                            "folder_name": folder_name,
                                            "found_in_db": False
                                        })
                                finally:
                                    connection.close()
                            else:
                                # Lỗi kết nối database
                                print(f"❌ Lỗi kết nối database khi kiểm tra sinh viên {folder_name}")
                                results.append({
                                    "bbox": bbox.tolist(),
                                    "score": score,
                                    "name": f"DB Error ({folder_name})",
                                    "student_code": folder_name,
                                    "room_number": "Lỗi database",
                                    "class_name": "Lỗi database",
                                    "birth_date": None,
                                    "folder_name": folder_name,
                                    "found_in_db": False
                                })

                except Exception as e:
                    continue

        return results

    except Exception as e:
        return []

@app.route('/api/recognize', methods=['POST'])
def recognize():
    try:
        # Lấy frame từ request
        data = request.json
        frame_b64 = data['frame'].split(',')[1]
        frame_data = base64.b64decode(frame_b64)

        # Chuyển thành numpy array
        nparr = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Kiểm tra frame
        if frame is None:
            return jsonify({
                "success": False,
                "error": "Không thể đọc frame"
            })

        # Xử lý nhận diện
        results = process_frame(frame)

        # Phát hiện khuôn mặt trong frame
        bboxes, landmarks = detector.detect(frame)
        faces_detected = len(bboxes) if bboxes is not None else 0

        # Kiểm tra kết quả phát hiện khuôn mặt
        if results:
            # Tự động ghi nhận ra vào nếu có kết quả nhận diện
            auto_log_access = data.get('auto_log_access', False)
            access_type = data.get('access_type', 1)  # 1: Vào, 2: Ra

            if auto_log_access and results:
                for result in results:
                    if result.get('student_code') and result.get('score', 0) >= FACE_RECOGNITION_CONFIG['auto_log_threshold']:  # Chỉ log nếu score cao
                        try:
                            # Ghi nhận ra vào tự động với logic thông minh
                            connection = connect_database()
                            if connection:
                                try:
                                    cursor = connection.cursor(dictionary=True)

                                    # Kiểm tra sinh viên tồn tại
                                    student_query = "SELECT id FROM nv5_dormitory_students WHERE student_code = %s AND status = 1"
                                    cursor.execute(student_query, (result['student_code'],))
                                    student = cursor.fetchone()

                                    if student:
                                        current_time = int(datetime.now().timestamp())

                                        # **LOGIC THÔNG MINH: Kiểm tra trạng thái vào/ra gần nhất**
                                        last_access_query = """
                                            SELECT access_type, access_time
                                            FROM nv5_dormitory_access_logs
                                            WHERE student_code = %s
                                            ORDER BY access_time DESC
                                            LIMIT 1
                                        """
                                        cursor.execute(last_access_query, (result['student_code'],))
                                        last_access = cursor.fetchone()

                                        # Xác định access_type dựa trên lần cuối
                                        if last_access:
                                            # Nếu lần cuối là "Vào" (1) → Lần này là "Ra" (2)
                                            # Nếu lần cuối là "Ra" (2) → Lần này là "Vào" (1)
                                            smart_access_type = 2 if last_access['access_type'] == 1 else 1
                                            action_text = "ra khỏi" if smart_access_type == 2 else "vào"
                                        else:
                                            # Lần đầu tiên → Mặc định là "Vào"
                                            smart_access_type = 1
                                            action_text = "vào"

                                        # Ghi log với access_type thông minh
                                        insert_query = """
                                            INSERT INTO nv5_dormitory_access_logs
                                            (student_id, student_code, access_type, access_time, gate_location,
                                             verification_method, device_id, device_name, ip_address,
                                             recognition_rate, notes, status, created_time)
                                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                        """

                                        values = (
                                            student['id'],
                                            result['student_code'],
                                            smart_access_type,  # Sử dụng access_type thông minh
                                            current_time,
                                            data.get('gate_location', 'Cổng chính'),
                                            'Nhận diện khuôn mặt',
                                            data.get('device_id', 'FACE_RECOGNITION_CAM'),
                                            data.get('device_name', 'Camera nhận diện khuôn mặt'),
                                            request.remote_addr,
                                            result['score'] * 100,  # Convert to percentage
                                            f"Nhận diện tự động - {action_text} KTX - Score: {result['score']:.2f}",
                                            1,
                                            current_time
                                        )

                                        cursor.execute(insert_query, values)
                                        connection.commit()

                                        result['access_logged'] = True
                                        result['log_id'] = cursor.lastrowid
                                        result['access_type'] = smart_access_type
                                        result['action_text'] = action_text

                                finally:
                                    cursor.close()
                                    connection.close()

                        except Exception as e:
                            result['access_logged'] = False

        # Tạo thông báo dựa trên kết quả
        message = ""
        if faces_detected == 0:
            message = "Không phát hiện khuôn mặt nào trong frame"
        elif len(results) == 0 and faces_detected > 0:
            message = f"Phát hiện {faces_detected} khuôn mặt nhưng không nhận diện được (score thấp hoặc không có trong database)"
        elif len(results) > 0:
            message = f"Nhận diện thành công {len(results)} khuôn mặt"

        return jsonify({
            "success": True,
            "results": results,
            "faces_detected": faces_detected,
            "recognized_faces": len(results),
            "message": message,
            "frame_size": {
                "width": frame.shape[1],
                "height": frame.shape[0],
                "channels": frame.shape[2]
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

# Thêm route test để kiểm tra API có hoạt động
@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({
        "success": True,
        "message": "API đang hoạt động"
    })

@app.route('/api/test-student/<student_code>', methods=['GET'])
def test_student(student_code):
    """Test API để kiểm tra thông tin sinh viên"""
    try:
        connection = connect_database()
        if not connection:
            return jsonify({
                "success": False,
                "error": "Không thể kết nối database"
            })

        student_info = get_person_name(connection, student_code)
        connection.close()

        return jsonify({
            "success": True,
            "student_code": student_code,
            "student_info": student_info
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

# Route mặc định cho trang chủ đã được di chuyển xuống dưới

def save_face_images(student_code, images_base64):
    """Lưu ảnh khuôn mặt của sinh viên"""
    try:
        # Tạo thư mục cho sinh viên
        student_dir = f"./datasets/new_persons/{student_code}"
        os.makedirs(student_dir, exist_ok=True)

        # Lưu từng ảnh
        for i, image_base64 in enumerate(images_base64):
            # Loại bỏ header data URL nếu có
            if ',' in image_base64:
                image_base64 = image_base64.split(',')[1]

            # Decode base64
            image_data = base64.b64decode(image_base64)

            # Lưu file
            image_path = os.path.join(student_dir, f"{student_code}_{i+1:03d}.jpg")
            with open(image_path, 'wb') as f:
                f.write(image_data)

        return True

    except Exception as e:
        return False

def delete_face_images(student_code):
    """Xóa ảnh khuôn mặt của sinh viên"""
    try:
        student_dir = f"./datasets/new_persons/{student_code}"
        if os.path.exists(student_dir):
            shutil.rmtree(student_dir)

        # Xóa trong thư mục data nếu có
        data_dir = f"./datasets/data/{student_code}"
        if os.path.exists(data_dir):
            shutil.rmtree(data_dir)

        return True

    except Exception as e:
        return False

def get_feature(face_image):
    """
    Extract facial features from an image using the face recognition model.
    """
    try:
        # Chuyển đổi sang RGB
        face_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)

        # Định nghĩa các bước tiền xử lý
        face_preprocess = transforms.Compose([
            transforms.ToTensor(),
            transforms.Resize((112, 112)),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])

        # Áp dụng tiền xử lý
        face_tensor = face_preprocess(face_image).unsqueeze(0).to(device)

        # Trích xuất đặc trưng
        with torch.no_grad():
            emb = recognizer(face_tensor)[0].cpu().numpy()

        # Chuẩn hóa vector đặc trưng
        emb = emb / np.linalg.norm(emb)
        return emb

    except Exception as e:
        return None

def process_training():
    """
    Hàm xử lý training bằng cách gọi hàm add_persons từ file add_persons.py
    """
    try:
        backup_dir = "./datasets/backup"
        add_persons_dir = "./datasets/new_persons"
        faces_save_dir = "./datasets/data/"
        features_path = "./datasets/face_features/feature"

        # Đảm bảo các thư mục tồn tại
        os.makedirs(backup_dir, exist_ok=True)
        os.makedirs(add_persons_dir, exist_ok=True)
        os.makedirs(faces_save_dir, exist_ok=True)
        os.makedirs(os.path.dirname(features_path), exist_ok=True)

        # Kiểm tra xem có dữ liệu để training không
        if not os.path.exists(add_persons_dir) or not os.listdir(add_persons_dir):
            return False, "Không có dữ liệu để training. Vui lòng thêm ảnh vào thư mục datasets/new_persons"

        # Gọi hàm add_persons từ file add_persons.py
        add_persons(
            backup_dir=backup_dir,
            add_persons_dir=add_persons_dir,
            faces_save_dir=faces_save_dir,
            features_path=features_path,
            reset_cache=True  # Reset cache để đảm bảo xử lý lại toàn bộ dữ liệu
        )

        return True, "Training thành công! Đã xử lý và cập nhật dữ liệu nhận diện khuôn mặt."

    except Exception as e:
        return False, f"Lỗi trong quá trình training: {str(e)}"

@app.route('/api/training', methods=['POST'])
def training():
    """
    API endpoint để xử lý yêu cầu training
    """
    try:
        success, message = process_training()

        if success:
            # Reload features sau khi training thành công
            global features
            try:
                features = read_features(feature_path="./datasets/face_features/feature")
                if features is not None:
                    images_names, images_embs = features
                    print(f"✓ Đã reload features: {len(images_names)} mẫu")
                else:
                    print("! Không có features để reload")
            except Exception as e:
                print(f"! Lỗi khi reload features: {str(e)}")

            return jsonify({
                "success": True,
                "message": message
            })
        else:
            return jsonify({
                "success": False,
                "error": message
            })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

# =====================================================
# API QUẢN LÝ KÝ TÚC XÁ SINH VIÊN
# =====================================================

import jwt
import hashlib
from functools import wraps

# Cấu hình JWT
app.config['SECRET_KEY'] = JWT_CONFIG['secret_key']

def hash_password(password):
    """Mã hóa mật khẩu bằng SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def token_required(f):
    """Decorator để kiểm tra JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'success': False, 'message': 'Token không tồn tại'}), 401

        try:
            if token.startswith('Bearer '):
                token = token[7:]

            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Token đã hết hạn'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Token không hợp lệ'}), 401

        return f(current_user_id, *args, **kwargs)

    return decorated

@app.route('/api/login', methods=['POST'])
def login():
    """API đăng nhập tài khoản quản trị"""
    try:
        data = request.get_json()

        if not data or not data.get('username') or not data.get('password'):
            return jsonify({
                'success': False,
                'message': 'Vui lòng nhập đầy đủ username và password'
            }), 400

        username = data['username']
        password = data['password']

        connection = connect_database()
        if not connection:
            return jsonify({
                'success': False,
                'message': 'Lỗi kết nối database'
            }), 500

        try:
            cursor = connection.cursor(dictionary=True)

            # Tạo bảng admin accounts nếu chưa tồn tại
            create_admin_table_query = """
                CREATE TABLE IF NOT EXISTS `nv5_dormitory_admin_accounts` (
                    `id` int(11) NOT NULL AUTO_INCREMENT,
                    `username` varchar(50) NOT NULL,
                    `password` varchar(255) NOT NULL,
                    `full_name` varchar(100) NOT NULL,
                    `email` varchar(100) DEFAULT NULL,
                    `phone` varchar(15) DEFAULT NULL,
                    `role` varchar(20) DEFAULT 'admin',
                    `permissions` text DEFAULT NULL,
                    `status` tinyint(1) DEFAULT 1,
                    `created_time` int(11) NOT NULL,
                    `updated_time` int(11) DEFAULT NULL,
                    `last_login` int(11) DEFAULT NULL,
                    `last_ip` varchar(45) DEFAULT NULL,
                    PRIMARY KEY (`id`),
                    UNIQUE KEY `username` (`username`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            cursor.execute(create_admin_table_query)

            # Kiểm tra và thêm admin mặc định nếu chưa có
            check_admin_query = "SELECT COUNT(*) as count FROM nv5_dormitory_admin_accounts"
            cursor.execute(check_admin_query)
            admin_count = cursor.fetchone()['count']

            if admin_count == 0:
                # Thêm admin mặc định
                current_time = int(datetime.now().timestamp())
                insert_admin_query = """
                    INSERT INTO nv5_dormitory_admin_accounts
                    (username, password, full_name, email, role, status, created_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_admin_query, (
                    'admin', 'password', 'Quản trị viên KTX', 'admin@ktx.edu.vn', 'admin', 1, current_time
                ))
                connection.commit()

            query = """
                SELECT id, username, password, full_name, email, phone, role, permissions, status
                FROM nv5_dormitory_admin_accounts
                WHERE username = %s AND status = 1
            """
            cursor.execute(query, (username,))
            user = cursor.fetchone()

            if not user:
                return jsonify({
                    'success': False,
                    'message': 'Tài khoản không tồn tại hoặc đã bị khóa'
                }), 401

            # Kiểm tra mật khẩu (tạm thời dùng plain text)
            if password != user['password']:
                return jsonify({
                    'success': False,
                    'message': 'Mật khẩu không chính xác'
                }), 401

            # Tạo JWT token
            token_payload = {
                'user_id': user['id'],
                'username': user['username'],
                'role': user['role'],
                'exp': datetime.utcnow() + timedelta(hours=24)
            }

            token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm='HS256')

            # Lưu thông tin vào session
            session['logged_in'] = True
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['role'] = user['role']

            # Cập nhật thời gian đăng nhập cuối
            current_time = int(datetime.now().timestamp())
            update_query = """
                UPDATE nv5_dormitory_admin_accounts
                SET last_login = %s, last_ip = %s, updated_time = %s
                WHERE id = %s
            """
            cursor.execute(update_query, (current_time, request.remote_addr, current_time, user['id']))
            connection.commit()

            return jsonify({
                'success': True,
                'message': 'Đăng nhập thành công',
                'data': {
                    'token': token,
                    'user': {
                        'id': user['id'],
                        'username': user['username'],
                        'full_name': user['full_name'],
                        'email': user['email'],
                        'phone': user['phone'],
                        'role': user['role']
                    },
                    'redirect_url': '/index.html'  # Redirect đến dashboard sau login
                }
            })

        finally:
            cursor.close()
            connection.close()

    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Lỗi server nội bộ'
        }), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """API đăng xuất"""
    try:
        # Xóa session
        session.clear()

        return jsonify({
            'success': True,
            'message': 'Đăng xuất thành công',
            'redirect_url': '/'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Lỗi server nội bộ'
        }), 500

@app.route('/api/check-session', methods=['GET'])
def check_session():
    """Kiểm tra trạng thái session"""
    try:
        if session.get('logged_in'):
            return jsonify({
                'success': True,
                'logged_in': True,
                'user': {
                    'id': session.get('user_id'),
                    'username': session.get('username'),
                    'full_name': session.get('full_name'),
                    'role': session.get('role')
                }
            })
        else:
            return jsonify({
                'success': True,
                'logged_in': False
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Lỗi server nội bộ'
        }), 500

@app.route('/api/change-password', methods=['POST'])
def change_password():
    """API đổi mật khẩu admin - Không cần mật khẩu cũ"""
    try:
        # Kiểm tra session
        if not session.get('logged_in') or not session.get('user_id'):
            return jsonify({
                'success': False,
                'message': 'Vui lòng đăng nhập để thực hiện thao tác này'
            }), 401

        data = request.get_json()

        if not data or not data.get('new_password'):
            return jsonify({
                'success': False,
                'message': 'Vui lòng nhập mật khẩu mới'
            }), 400

        new_password = data['new_password']
        confirm_password = data.get('confirm_password', '')

        # Kiểm tra mật khẩu mới và xác nhận
        if new_password != confirm_password:
            return jsonify({
                'success': False,
                'message': 'Mật khẩu mới và xác nhận mật khẩu không khớp'
            }), 400

        # Kiểm tra độ dài mật khẩu mới - tối thiểu 3 ký tự
        if len(new_password) < 3:
            return jsonify({
                'success': False,
                'message': 'Mật khẩu mới phải có ít nhất 3 ký tự'
            }), 400

        connection = connect_database()
        if not connection:
            return jsonify({
                'success': False,
                'message': 'Lỗi kết nối database'
            }), 500

        try:
            cursor = connection.cursor(dictionary=True)
            user_id = session.get('user_id')

            # Kiểm tra user tồn tại
            query = "SELECT id FROM nv5_dormitory_admin_accounts WHERE id = %s AND status = 1"
            cursor.execute(query, (user_id,))
            user = cursor.fetchone()

            if not user:
                return jsonify({
                    'success': False,
                    'message': 'Không tìm thấy tài khoản'
                }), 404

            # Cập nhật mật khẩu mới (không cần kiểm tra mật khẩu cũ)
            current_time = int(datetime.now().timestamp())
            update_query = """
                UPDATE nv5_dormitory_admin_accounts
                SET password = %s, updated_time = %s
                WHERE id = %s
            """
            cursor.execute(update_query, (new_password, current_time, user_id))
            connection.commit()

            return jsonify({
                'success': True,
                'message': 'Đổi mật khẩu thành công'
            })

        finally:
            cursor.close()
            connection.close()

    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Lỗi server nội bộ'
        }), 500

@app.route('/api/students', methods=['POST'])
def create_student():
    """Tạo sinh viên mới"""
    try:
        data = request.get_json()

        required_fields = ['student_code', 'full_name', 'birth_date', 'room_number']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Trường {field} là bắt buộc'
                }), 400

        connection = connect_database()
        if not connection:
            return jsonify({
                'success': False,
                'message': 'Lỗi kết nối database'
            }), 500

        try:
            cursor = connection.cursor(dictionary=True)

            # Kiểm tra mã sinh viên đã tồn tại
            check_query = "SELECT id FROM nv5_dormitory_students WHERE student_code = %s"
            cursor.execute(check_query, (data['student_code'],))
            if cursor.fetchone():
                return jsonify({
                    'success': False,
                    'message': 'Mã sinh viên đã tồn tại'
                }), 400

            # Thêm sinh viên mới
            current_time = int(datetime.now().timestamp())

            # Chuyển đổi gender từ text sang số
            gender_value = 1  # Mặc định là Nam
            if data.get('gender'):
                if data['gender'].lower() in ['nữ', 'nu', 'female', '2']:
                    gender_value = 2
                elif data['gender'].lower() in ['nam', 'male', '1']:
                    gender_value = 1

            insert_query = """
                INSERT INTO nv5_dormitory_students
                (student_code, full_name, birth_date, gender, room_number, class_name,
                 major, course, faculty, phone, email, status, created_time, updated_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            values = (
                data['student_code'],
                data['full_name'],
                data['birth_date'],
                gender_value,
                data['room_number'],
                data.get('class_name', ''),
                data.get('major', ''),
                data.get('course', ''),
                data.get('faculty', ''),
                data.get('phone', ''),
                data.get('email', ''),
                data.get('status', 1),
                current_time,
                current_time
            )

            cursor.execute(insert_query, values)
            connection.commit()

            student_id = cursor.lastrowid

            # Xử lý ảnh khuôn mặt nếu có
            if data.get('images_base64'):
                save_face_images(data['student_code'], data['images_base64'])

            return jsonify({
                'success': True,
                'message': 'Thêm sinh viên thành công',
                'data': {
                    'id': student_id,
                    'student_code': data['student_code']
                }
            })

        finally:
            cursor.close()
            connection.close()

    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Lỗi server nội bộ'
        }), 500

@app.route('/api/students', methods=['GET'])
def get_students():
    """Lấy danh sách sinh viên"""
    try:
        connection = connect_database()
        if not connection:
            return jsonify({
                'success': False,
                'message': 'Lỗi kết nối database'
            }), 500

        try:
            cursor = connection.cursor(dictionary=True)

            page = int(request.args.get('page', 1))
            limit = int(request.args.get('limit', 10))
            search = request.args.get('search', '')

            offset = (page - 1) * limit

            where_clause = "WHERE status = 1"
            params = []

            if search:
                where_clause += " AND (student_code LIKE %s OR full_name LIKE %s OR room_number LIKE %s)"
                search_param = f"%{search}%"
                params.extend([search_param, search_param, search_param])

            # Đếm tổng số bản ghi
            count_query = f"SELECT COUNT(*) as total FROM nv5_dormitory_students {where_clause}"
            cursor.execute(count_query, params)
            total = cursor.fetchone()['total']

            # Lấy dữ liệu với phân trang
            query = f"""
                SELECT id, student_code, full_name, birth_date, gender, class_name, major,
                       course, faculty, room_number, phone, email, created_time
                FROM nv5_dormitory_students
                {where_clause}
                ORDER BY created_time DESC
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])
            cursor.execute(query, params)
            students = cursor.fetchall()

            # Format dữ liệu
            for student in students:
                if student['birth_date']:
                    student['birth_date'] = student['birth_date'].strftime('%Y-%m-%d')
                student['created_time'] = datetime.fromtimestamp(student['created_time']).strftime('%Y-%m-%d %H:%M:%S')

                # Chuyển đổi gender từ số sang text
                if student['gender'] == 1:
                    student['gender'] = 'Nam'
                elif student['gender'] == 2:
                    student['gender'] = 'Nữ'
                else:
                    student['gender'] = 'Không xác định'

            return jsonify({
                'success': True,
                'data': {
                    'students': students,
                    'pagination': {
                        'page': page,
                        'limit': limit,
                        'total': total,
                        'total_pages': (total + limit - 1) // limit
                    }
                }
            })

        finally:
            cursor.close()
            connection.close()

    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Lỗi server nội bộ'
        }), 500

@app.route('/api/students/<int:student_id>', methods=['GET'])
def get_student(student_id):
    """Lấy thông tin chi tiết 1 sinh viên"""
    try:
        connection = connect_database()
        if not connection:
            return jsonify({
                'success': False,
                'message': 'Lỗi kết nối database'
            }), 500

        try:
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT id, student_code, full_name, birth_date, gender, class_name, major,
                       course, faculty, room_number, phone, email, created_time, updated_time
                FROM nv5_dormitory_students
                WHERE id = %s AND status = 1
            """
            cursor.execute(query, (student_id,))
            student = cursor.fetchone()

            if not student:
                return jsonify({
                    'success': False,
                    'message': 'Không tìm thấy sinh viên'
                }), 404

            # Format dữ liệu
            if student['birth_date']:
                student['birth_date'] = student['birth_date'].strftime('%Y-%m-%d')

            if student['created_time']:
                student['created_time'] = datetime.fromtimestamp(student['created_time']).strftime('%Y-%m-%d %H:%M:%S')

            if student['updated_time']:
                student['updated_time'] = datetime.fromtimestamp(student['updated_time']).strftime('%Y-%m-%d %H:%M:%S')

            # Chuyển đổi gender từ số sang text
            if student['gender'] == 1:
                student['gender'] = 'Nam'
            elif student['gender'] == 2:
                student['gender'] = 'Nữ'
            else:
                student['gender'] = ''

            return jsonify({
                'success': True,
                'data': student
            })

        finally:
            cursor.close()
            connection.close()

    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Lỗi server nội bộ'
        }), 500

@app.route('/api/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    """Cập nhật thông tin sinh viên"""
    try:
        data = request.get_json()

        connection = connect_database()
        if not connection:
            return jsonify({
                'success': False,
                'message': 'Lỗi kết nối database'
            }), 500

        try:
            cursor = connection.cursor(dictionary=True)

            # Kiểm tra sinh viên tồn tại
            check_query = "SELECT id FROM nv5_dormitory_students WHERE id = %s"
            cursor.execute(check_query, (student_id,))
            if not cursor.fetchone():
                return jsonify({
                    'success': False,
                    'message': 'Không tìm thấy sinh viên'
                }), 404

            # Cập nhật thông tin
            current_time = int(datetime.now().timestamp())

            # Chuyển đổi gender từ text sang số
            gender_value = 1  # Mặc định là Nam
            if data.get('gender'):
                if data['gender'].lower() in ['nữ', 'nu', 'female', '2']:
                    gender_value = 2
                elif data['gender'].lower() in ['nam', 'male', '1']:
                    gender_value = 1

            update_query = """
                UPDATE nv5_dormitory_students
                SET full_name = %s, birth_date = %s, gender = %s, room_number = %s,
                    class_name = %s, major = %s, course = %s, faculty = %s,
                    phone = %s, email = %s, updated_time = %s
                WHERE id = %s
            """

            values = (
                data.get('full_name', ''),
                data.get('birth_date', ''),
                gender_value,
                data.get('room_number', ''),
                data.get('class_name', ''),
                data.get('major', ''),
                data.get('course', ''),
                data.get('faculty', ''),
                data.get('phone', ''),
                data.get('email', ''),
                current_time,
                student_id
            )

            cursor.execute(update_query, values)
            connection.commit()

            # Xử lý ảnh khuôn mặt nếu có
            if data.get('images_base64'):
                save_face_images(data.get('student_code', str(student_id)), data['images_base64'])

            return jsonify({
                'success': True,
                'message': 'Cập nhật thông tin sinh viên thành công'
            })

        finally:
            cursor.close()
            connection.close()

    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Lỗi server nội bộ'
        }), 500

@app.route('/api/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    """Xóa sinh viên"""
    try:
        connection = connect_database()
        if not connection:
            return jsonify({
                'success': False,
                'message': 'Lỗi kết nối database'
            }), 500

        try:
            cursor = connection.cursor(dictionary=True)

            # Kiểm tra sinh viên tồn tại và lấy student_code
            check_query = "SELECT student_code FROM nv5_dormitory_students WHERE id = %s"
            cursor.execute(check_query, (student_id,))
            student = cursor.fetchone()

            if not student:
                return jsonify({
                    'success': False,
                    'message': 'Không tìm thấy sinh viên'
                }), 404

            # Xóa sinh viên (soft delete)
            delete_query = "UPDATE nv5_dormitory_students SET status = 0 WHERE id = %s"
            cursor.execute(delete_query, (student_id,))
            connection.commit()

            # Xóa ảnh khuôn mặt nếu có
            try:
                delete_face_images(student['student_code'])
            except Exception as e:
                pass

            return jsonify({
                'success': True,
                'message': 'Xóa sinh viên thành công'
            })

        finally:
            cursor.close()
            connection.close()

    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Lỗi server nội bộ'
        }), 500

@app.route('/api/students/<student_code>/check-images', methods=['GET'])
def check_student_images(student_code):
    """Kiểm tra xem sinh viên đã có ảnh trong thư mục datasets/new_persons chưa"""
    try:
        student_dir = f"./datasets/new_persons/{student_code}"

        if os.path.exists(student_dir):
            # Đếm số file ảnh trong thư mục
            all_files = os.listdir(student_dir)
            image_files = [f for f in all_files
                          if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

            result = {
                'success': True,
                'has_images': len(image_files) > 0,
                'image_count': len(image_files),
                'message': f'Tìm thấy {len(image_files)} ảnh trong thư mục' if len(image_files) > 0 else 'Chưa có ảnh',
                'directory_path': student_dir,
                'all_files': all_files,
                'image_files': image_files
            }

            return jsonify(result)
        else:
            result = {
                'success': True,
                'has_images': False,
                'image_count': 0,
                'message': 'Chưa có ảnh',
                'directory_path': student_dir
            }
            return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Lỗi server nội bộ',
            'error': str(e)
        }), 500

@app.route('/api/access-logs', methods=['GET'])
def get_access_logs():
    """Lấy danh sách lịch sử ra/vào"""
    try:
        connection = connect_database()
        if not connection:
            return jsonify({
                'success': False,
                'message': 'Lỗi kết nối database'
            }), 500

        try:
            cursor = connection.cursor(dictionary=True)

            page = int(request.args.get('page', 1))
            limit = int(request.args.get('limit', 50))
            offset = (page - 1) * limit

            # Query để lấy access logs với thông tin sinh viên
            query = """
                SELECT al.id, al.student_code,
                       FROM_UNIXTIME(al.access_time) as access_time,
                       al.access_type, al.gate_location,
                       al.verification_method, al.recognition_rate, al.notes,
                       s.full_name as student_name, s.room_number
                FROM nv5_dormitory_access_logs al
                LEFT JOIN nv5_dormitory_students s ON al.student_code = s.student_code
                ORDER BY al.access_time DESC
                LIMIT %s OFFSET %s
            """

            cursor.execute(query, (limit, offset))
            logs = cursor.fetchall()

            # Format dữ liệu
            for log in logs:
                # access_time đã được format bởi FROM_UNIXTIME trong query
                if log['access_time'] and hasattr(log['access_time'], 'strftime'):
                    log['access_time'] = log['access_time'].strftime('%Y-%m-%d %H:%M:%S')

                # Chuyển đổi access_type từ số sang text
                if log['access_type'] == 1:
                    log['access_type'] = 'entry'
                elif log['access_type'] == 2:
                    log['access_type'] = 'exit'

            return jsonify({
                'success': True,
                'data': logs
            })

        finally:
            cursor.close()
            connection.close()

    except Exception as e:
        error_msg = str(e)

        # Kiểm tra nếu bảng không tồn tại
        if "doesn't exist" in error_msg or "Table" in error_msg:
            return jsonify({
                'success': True,
                'data': [],
                'message': 'Bảng access logs chưa được tạo. Hệ thống sẽ tạo tự động khi có dữ liệu đầu tiên.'
            })

        return jsonify({
            'success': False,
            'message': f'Lỗi server nội bộ: {error_msg}'
        }), 500

@app.route('/api/access-logs', methods=['POST'])
@token_required
def create_access_log(current_user_id):
    """Tạo bản ghi ra vào từ nhận diện khuôn mặt"""
    try:
        data = request.get_json()

        required_fields = ['student_code', 'access_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Trường {field} là bắt buộc'
                }), 400

        connection = connect_database()
        if not connection:
            return jsonify({
                'success': False,
                'message': 'Lỗi kết nối database'
            }), 500

        try:
            cursor = connection.cursor(dictionary=True)

            # Tìm sinh viên theo mã
            student_query = "SELECT id FROM nv5_dormitory_students WHERE student_code = %s AND status = 1"
            cursor.execute(student_query, (data['student_code'],))
            student = cursor.fetchone()

            if not student:
                return jsonify({
                    'success': False,
                    'message': 'Không tìm thấy sinh viên với mã này'
                }), 404

            # Thêm bản ghi ra vào
            current_time = int(datetime.now().timestamp())

            insert_query = """
                INSERT INTO nv5_dormitory_access_logs
                (student_id, student_code, access_type, access_time, gate_location,
                 verification_method, device_id, device_name, ip_address,
                 recognition_rate, notes, status, created_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            values = (
                student['id'],
                data['student_code'],
                data['access_type'],
                current_time,
                data.get('gate_location', 'Cổng chính'),
                data.get('verification_method', 'Nhận diện khuôn mặt'),
                data.get('device_id', 'FACE_RECOGNITION_CAM'),
                data.get('device_name', 'Camera nhận diện khuôn mặt'),
                request.remote_addr,
                data.get('recognition_rate', 0),
                data.get('notes', 'Nhận diện tự động'),
                data.get('status', 1),
                current_time
            )

            cursor.execute(insert_query, values)
            connection.commit()

            log_id = cursor.lastrowid

            return jsonify({
                'success': True,
                'message': 'Ghi nhận ra vào thành công',
                'data': {
                    'log_id': log_id,
                    'student_code': data['student_code'],
                    'access_type': data['access_type'],
                    'access_time': current_time
                }
            })

        finally:
            cursor.close()
            connection.close()

    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Lỗi server nội bộ'
        }), 500

# =====================================================
# ROUTES SERVE STATIC FILES VÀ FRONTEND
# =====================================================

@app.route('/')
def index():
    """Trang chủ - Kiểm tra authentication và hiển thị giao diện phù hợp"""
    # Kiểm tra session để xác định đã login hay chưa
    if session.get('logged_in') and session.get('user_id'):
        # Đã login → hiển thị dashboard mới
        return send_from_directory(app.static_folder, 'dashboard.html')
    else:
        # Chưa login → hiển thị trang login
        return send_from_directory(app.static_folder, 'home.html')

@app.route('/home.html')
def login_page():
    """Trang đăng nhập"""
    return send_from_directory(app.static_folder, 'home.html')

@app.route('/index.html')
def dashboard():
    """Dashboard chính - yêu cầu đăng nhập"""
    # Kiểm tra authentication
    if not session.get('logged_in') or not session.get('user_id'):
        # Chưa login → redirect về trang chủ (sẽ hiển thị login)
        return redirect('/')

    # Đã login → hiển thị dashboard
    return send_from_directory(app.static_folder, 'dashboard.html')

import os

import os
import mysql.connector  # hoặc thư viện kết nối MySQL bạn dùng

def check_table_exists(connection, table_name):
    cursor = connection.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables 
        WHERE table_schema = DATABASE() AND table_name = %s
    """, (table_name,))
    exists = cursor.fetchone()[0] == 1
    cursor.close()
    return exists

def initialize_database():
    connection = connect_database()
    if not connection:
        print("Không thể kết nối MySQL để khởi tạo DB")
        return False
    
    if check_table_exists(connection, 'nv5_dormitory_students'):
        print("✅ Bảng đã tồn tại, không cần khởi tạo lại.")
        connection.close()
        return True
    
    cursor = connection.cursor()
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))  
        sql_file_path = os.path.join(base_dir, 'database', 'db_ktx.sql')

        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_commands = f.read()
        
        sql_statements = sql_commands.split(';')
        
        for statement in sql_statements:
            stmt = statement.strip()
            if stmt:
                cursor.execute(stmt)
        
        connection.commit()
        print("✅ Đã khởi tạo CSDL và bảng từ file SQL")
        return True
    except Exception as e:
        print(f"❌ Lỗi khởi tạo DB: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

@app.route('/change-password.html')
def change_password_page():
    """Trang đổi mật khẩu - yêu cầu đăng nhập"""
    # Kiểm tra authentication
    if not session.get('logged_in') or not session.get('user_id'):
        # Chưa login → redirect về trang chủ (sẽ hiển thị login)
        return redirect('/')

    # Đã login → hiển thị trang đổi mật khẩu
    return send_from_directory(app.static_folder, 'change_password.html')

@app.route('/css/<path:filename>')
def serve_css(filename):
    """Serve CSS files"""
    return send_from_directory(os.path.join(app.static_folder, 'css'), filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    """Serve JavaScript files"""
    return send_from_directory(os.path.join(app.static_folder, 'js'), filename)

@app.route('/images/<path:filename>')
def serve_images(filename):
    """Serve image files"""
    return send_from_directory(os.path.join(app.static_folder, 'images'), filename)

if __name__ == '__main__':
    # Import thêm datetime và timedelta
    from datetime import datetime, timedelta

    # Khởi tạo DB nếu cần
    initialize_database()

    print("🚀 Starting Face Recognition + Dormitory API...")

    # Đảm bảo bảng access logs tồn tại
    print("🔧 Checking database tables...")
    ensure_access_logs_table()

    print("📋 Available endpoints:")
    print("   GET  / - Trang chủ (login nếu chưa đăng nhập, dashboard nếu đã đăng nhập)")
    print("   GET  /home.html - Trang đăng nhập")
    print("   GET  /index.html - Dashboard (yêu cầu đăng nhập)")
    print("   GET  /change-password.html - 🔑 Đổi mật khẩu (yêu cầu đăng nhập)")
    print("   GET  /api/test - Test connection")
    print("   POST /api/recognize - Face recognition")
    print("   POST /api/training - 🧠 Training model")
    print("   POST /api/login - Login")
    print("   POST /api/logout - Logout")
    print("   POST /api/change-password - 🔑 Change admin password")
    print("   GET  /api/check-session - Check session status")
    print("   GET  /api/students - Get students list")
    print("   GET  /api/students/<id> - Get student details")
    print("   POST /api/students - Create new student")
    print("   PUT  /api/students/<id> - Update student")
    print("   DELETE /api/students/<id> - Delete student")
    print("   GET  /api/students/<code>/check-images - Check existing images")
    print("   GET  /api/access-logs - Get access logs")
    print("   POST /api/access-logs - Create access log")
    print("🌐 Server running on http://localhost:5001")
    print("🔑 Default login: admin / password")
    print("� Truy cập http://localhost:5001 để sử dụng hệ thống")

    app.run(
        host=API_CONFIG['host'],
        port=API_CONFIG['port'],
        debug=True,  # Bật debug mode
        use_reloader=True,  # Bật auto-reload
        threaded=True  # Cho phép xử lý nhiều request đồng thời
    )
