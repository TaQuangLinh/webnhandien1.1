import os
import time
import cv2
import mysql.connector
from face_detection.scrfd.detector import SCRFD
import unidecode  # Thêm thư viện để chuyển đổi tiếng Việt có dấu sang không dấu
from datetime import datetime  # Thêm import datetime

def convert_to_no_accent(text):
    """Chuyển chuỗi có dấu thành không dấu"""
    return unidecode.unidecode(text)

def connect_database():
    """Kết nối đến cơ sở dữ liệu"""
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="nukeviet5_0"
        )
        return connection
    except mysql.connector.Error as error:
        print(f"Lỗi kết nối database: {error}")
        return None

def check_person_exists(cursor, fullname, birthday_timestamp):
    """Kiểm tra người dùng đã tồn tại chưa"""
    try:
        sql = """SELECT id, foder_img FROM nv5_vi_checkin_person
                WHERE fullname = %s AND birthday = %s"""
        cursor.execute(sql, (fullname, birthday_timestamp))
        result = cursor.fetchone()
        return result
    except mysql.connector.Error as error:
        print(f"Lỗi kiểm tra dữ liệu: {error}")
        return None

def get_folder_name(fullname, birthday_timestamp):
    """Tạo tên thư mục từ tên và ngày sinh"""
    name_no_accent = convert_to_no_accent(fullname)
    name_normalized = name_no_accent.replace(" ", "_").lower()
    # Chuyển timestamp thành chuỗi ngày tháng
    birthday_date = datetime.fromtimestamp(birthday_timestamp)
    birthday_str = birthday_date.strftime("%Y%m%d")
    return f"{name_normalized}_{birthday_str}"

def capture_faces():
    print("\nĐang khởi tạo hệ thống nhận diện khuôn mặt...")
    try:
        # Khởi tạo detector
        detector = SCRFD(model_file="face_detection/scrfd/weights/scrfd_2.5g_bnkps.onnx")
        print("✓ Đã khởi tạo detector thành công")
    except Exception as e:
        print(f"✗ Lỗi khởi tạo detector: {str(e)}")
        return

    print("\nĐang kết nối camera...")
    try:
        # Mở camera
        cap = cv2.VideoCapture(1)
        if not cap.isOpened():
            print("✗ Không thể kết nối camera! Đang thử camera mặc định...")
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("✗ Không tìm thấy camera nào! Vui lòng kiểm tra lại.")
                return
        print("✓ Đã kết nối camera thành công")
    except Exception as e:
        print(f"✗ Lỗi kết nối camera: {str(e)}")
        return

    print("\nĐang kết nối cơ sở dữ liệu...")
    try:
        # Kết nối database
        connection = connect_database()
        if not connection:
            print("✗ Không thể kết nối cơ sở dữ liệu!")
            return
        print("✓ Đã kết nối cơ sở dữ liệu thành công")
    except Exception as e:
        print(f"✗ Lỗi kết nối CSDL: {str(e)}")
        return

    # Tạo thư mục để lưu ảnh
    print("\nHệ thống đã sẵn sàng!")
    print("-" * 50)

    # Nhập thông tin người dùng
    print("\nNhập thông tin người dùng:")
    while True:
        print("\nNhập họ tên (có dấu): ")
        fullname = input().strip()
        if not fullname:
            print("Tên không được để trống!")
            continue

        # Nhập và kiểm tra ngày sinh
        while True:
            print("Nhập ngày sinh (dd/mm/yyyy): ")
            birthday_str = input().strip()
            try:
                # Chuyển chuỗi ngày tháng thành datetime object
                birthday_date = datetime.strptime(birthday_str, "%d/%m/%Y")
                # Chuyển datetime thành timestamp
                birthday_timestamp = int(birthday_date.timestamp())
                break
            except ValueError:
                print("Ngày sinh không hợp lệ! Vui lòng nhập theo định dạng dd/mm/yyyy")

        # Kiểm tra người dùng đã tồn tại
        cursor = connection.cursor()
        existing_person = check_person_exists(cursor, fullname, birthday_timestamp)
        if existing_person:
            print(f"\n⚠️ Người dùng này đã tồn tại trong hệ thống!")
            print(f"- Họ tên: {fullname}")
            print(f"- Ngày sinh: {birthday_str}")
            print(f"- Thư mục ảnh: {existing_person[1]}")

            print("\nBạn có muốn:")
            print("1. Nhập lại thông tin khác")
            print("2. Thoát chương trình")
            choice = input("Lựa chọn (1 hoặc 2): ").strip()
            if choice == "2":
                return
            continue
        break

    # Tạo tên thư mục từ tên và ngày sinh
    folder_name = get_folder_name(fullname, birthday_timestamp)
    save_dir = os.path.join("datasets", "new_persons", folder_name)

    # Kiểm tra thư mục đã tồn tại
    if os.path.exists(save_dir):
        print(f"\n⚠️ Thư mục {save_dir} đã tồn tại!")
        print("Vui lòng kiểm tra lại thông tin.")
        return

    os.makedirs(save_dir, exist_ok=True)

    # Cho phép người dùng chọn số ảnh
    while True:
        try:
            print("\nNhập số lượng ảnh muốn chụp (khuyến nghị 10-20 ảnh): ")
            total_images = int(input().strip())
            if total_images > 0:
                break
            print("Số lượng ảnh phải lớn hơn 0!")
        except ValueError:
            print("Vui lòng nhập một số nguyên!")

    # Thêm thông tin vào database
    try:
        current_time = int(time.time())
        sql = """INSERT INTO nv5_vi_checkin_person
                (fullname, birthday, foder_img, addtime, num_img, status)
                VALUES (%s, %s, %s, %s, %s, %s)"""
        values = (fullname, birthday_timestamp, save_dir, current_time, total_images, 0)
        cursor.execute(sql, values)
        connection.commit()
        person_id = cursor.lastrowid
        print(f"Đã thêm thông tin người dùng vào database với ID: {person_id}")
    except mysql.connector.Error as error:
        print(f"Lỗi thêm dữ liệu: {error}")
        if os.path.exists(save_dir):
            os.rmdir(save_dir)
        return

    # Biến đếm số ảnh đã chụp
    count = 0

    print("\nChọn chế độ chụp:")
    print("1. Chụp thủ công (nhấn SPACE để chụp)")
    print("2. Chụp tự động (3 giây/ảnh)")
    while True:
        try:
            mode = int(input("Chọn chế độ (1 hoặc 2): ").strip())
            if mode in [1, 2]:
                break
            print("Vui lòng chọn 1 hoặc 2!")
        except ValueError:
            print("Vui lòng nhập số!")

    print("\nHướng dẫn:")
    if mode == 1:
        print("- Nhấn SPACE để chụp ảnh")
    else:
        print("- Hệ thống sẽ tự động chụp sau mỗi 3 giây khi phát hiện khuôn mặt")
    print("- Nhấn Q để thoát")
    print(f"- Cần chụp {total_images} ảnh với các góc độ khác nhau")
    print("\nGợi ý các góc chụp:")
    print("- Nhìn thẳng")
    print("- Nghiêng trái/phải 45 độ")
    print("- Ngước lên/cúi xuống nhẹ")
    print("- Thay đổi biểu cảm (cười, nghiêm túc)")
    print("- Thay đổi khoảng cách với camera")
    print("\nĐang mở camera...")

    # Thêm biến cho chụp tự động
    last_capture_time = time.time()
    auto_capture_interval = 3  # Thời gian giữa các lần chụp (giây)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Phát hiện khuôn mặt
        bboxes, landmarks = detector.detect(image=frame)

        # Vẽ khung và landmarks cho mỗi khuôn mặt
        face_detected = False
        for i in range(len(bboxes)):
            x1, y1, x2, y2, score = bboxes[i]
            if score > 0.5:
                face_detected = True
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                for point in landmarks[i]:
                    cv2.circle(frame, tuple(map(int, point)), 2, (0, 0, 255), -1)

        # Hiển thị số ảnh đã chụp và chế độ
        cv2.putText(frame, f"Da chup: {count}/{total_images}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        mode_text = "CHE DO: TU DONG" if mode == 2 else "CHE DO: THU CONG"
        cv2.putText(frame, mode_text, (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Nếu đang ở chế độ tự động, hiển thị đếm ngược
        if mode == 2 and face_detected:
            time_left = int(auto_capture_interval - (time.time() - last_capture_time))
            cv2.putText(frame, f"Chup sau: {time_left}s", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Hiển thị frame
        cv2.imshow("Capture Face", frame)

        # Xử lý chụp ảnh
        should_capture = False
        key = cv2.waitKey(1) & 0xFF

        if mode == 1:  # Chế độ thủ công
            if key == 32:  # SPACE
                should_capture = True
        else:  # Chế độ tự động
            current_time = time.time()
            if face_detected and (current_time - last_capture_time) >= auto_capture_interval:
                should_capture = True
                last_capture_time = current_time

        # Thoát nếu nhấn Q
        if key == ord('q'):
            break

        # Xử lý việc chụp ảnh
        if should_capture:
            if len(bboxes) == 0:
                print("Không phát hiện được khuôn mặt!")
                continue

            if len(bboxes) > 1:
                print("Phát hiện nhiều khuôn mặt! Vui lòng chỉ để một khuôn mặt trong khung hình.")
                continue

            # Lưu ảnh
            img_name = os.path.join(save_dir, f"{count+1}.jpg")
            cv2.imwrite(img_name, frame)
            print(f"Đã chụp ảnh {count+1}")
            count += 1

            if count >= total_images:
                print("\nĐã chụp đủ số ảnh!")
                break

    # Giải phóng tài nguyên
    cap.release()
    cv2.destroyAllWindows()

    # Cập nhật số lượng ảnh thực tế vào database
    if count > 0:
        try:
            cursor.execute("""
                UPDATE nv5_vi_checkin_person
                SET num_img = %s
                WHERE id = %s
            """, (count, person_id))
            connection.commit()
            print(f"\nĐã cập nhật số lượng ảnh ({count}) vào CSDL")
        except mysql.connector.Error as error:
            print(f"Lỗi cập nhật dữ liệu: {error}")

        print(f"Đã lưu {count} ảnh vào thư mục: {save_dir}")
        print("Tiếp theo, hãy chạy file 2.add_persons.py để thêm người mới vào hệ thống")
    else:
        print("\nKhông có ảnh nào được lưu!")
        # Xóa thư mục rỗng và dữ liệu trong database
        if os.path.exists(save_dir):
            os.rmdir(save_dir)
        try:
            cursor.execute("DELETE FROM nv5_vi_checkin_person WHERE id = %s", (person_id,))
            connection.commit()
        except mysql.connector.Error as error:
            print(f"Lỗi xóa dữ liệu: {error}")

    # Đóng kết nối database
    if connection.is_connected():
        cursor.close()
        connection.close()

if __name__ == "__main__":
    capture_faces()
