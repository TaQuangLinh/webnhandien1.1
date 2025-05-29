import os
import time
import cv2
from face_detection.scrfd.detector import SCRFD

def capture_faces():
    # Khởi tạo detector
    detector = SCRFD(model_file="face_detection/scrfd/weights/scrfd_2.5g_bnkps.onnx")

    # Mở camera
    cap = cv2.VideoCapture(1)

    # Tạo thư mục để lưu ảnh
    print("\nNhập tên người cần thêm (không dấu): ")
    person_name = input().strip()
    if not person_name:
        print("Tên không được để trống!")
        return

    # Cho phép người dùng chọn số ảnh và chế độ chụp
    while True:
        try:
            print("\nChọn chế độ chụp:")
            print("1. Chụp thủ công (nhấn SPACE để chụp)")
            print("2. Chụp tự động (tự động chụp khi phát hiện khuôn mặt)")
            mode = int(input("Chọn chế độ (1 hoặc 2): ").strip())
            if mode not in [1, 2]:
                print("Vui lòng chọn 1 hoặc 2!")
                continue

            print("\nNhập số lượng ảnh muốn chụp:")
            print("- Khuyến nghị: 15-20 ảnh cho độ chính xác cao")
            print("- Tối thiểu: 10 ảnh")
            print("- Tối đa: 30 ảnh")
            total_images = int(input().strip())
            if 10 <= total_images <= 30:
                break
            print("Số lượng ảnh phải từ 10-30!")
        except ValueError:
            print("Vui lòng nhập số nguyên!")

    save_dir = os.path.join("datasets", "new_persons", person_name)
    os.makedirs(save_dir, exist_ok=True)

    # Biến đếm và cài đặt
    count = 0
    auto_capture_delay = 1.0  # Delay giữa các lần chụp tự động
    last_capture_time = time.time()

    print("\nHướng dẫn chụp ảnh chất lượng:")
    print("1. Ánh sáng:")
    print("   - Đảm bảo khuôn mặt được chiếu sáng đều")
    print("   - Tránh ngược sáng hoặc tối quá")

    print("\n2. Góc chụp (cần đủ các góc):")
    print("   - Nhìn thẳng (3-4 ảnh)")
    print("   - Nghiêng trái 45° (2-3 ảnh)")
    print("   - Nghiêng phải 45° (2-3 ảnh)")
    print("   - Ngước lên/cúi xuống nhẹ (2-3 ảnh)")

    print("\n3. Biểu cảm:")
    print("   - Mặt nghiêm túc (3-4 ảnh)")
    print("   - Cười nhẹ (2-3 ảnh)")
    print("   - Các biểu cảm khác (2-3 ảnh)")

    print("\n4. Phụ kiện:")
    print("   - Có/không đeo kính")
    print("   - Thay đổi kiểu tóc nếu có")

    input("\nNhấn Enter để bắt đầu...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Phát hiện khuôn mặt
        bboxes, landmarks = detector.detect(image=frame)

        # Vẽ khung và landmarks cho mỗi khuôn mặt
        for i in range(len(bboxes)):
            x1, y1, x2, y2, score = bboxes[i]
            # Chỉ vẽ nếu độ tin cậy > 0.5
            if score > 0.5:
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)

                # Vẽ 5 điểm landmarks
                for point in landmarks[i]:
                    cv2.circle(frame, tuple(map(int, point)), 2, (0, 0, 255), -1)

        # Hiển thị số ảnh đã chụp
        cv2.putText(frame, f"Da chup: {count}/{total_images}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Hiển thị frame
        cv2.imshow("Capture Face", frame)

        # Xử lý phím bấm
        key = cv2.waitKey(1) & 0xFF

        # Nhấn SPACE để chụp ảnh
        if key == 32:  # SPACE
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
            time.sleep(0.5)  # Đợi 0.5s giữa các lần chụp

            if count >= total_images:
                print("\nĐã chụp đủ số ảnh!")
                break

        # Nhấn Q để thoát
        elif key == ord('q'):
            break

    # Giải phóng tài nguyên
    cap.release()
    cv2.destroyAllWindows()

    if count > 0:
        print(f"\nĐã lưu {count} ảnh vào thư mục: {save_dir}")
        print("Tiếp theo, hãy chạy file add_persons.py để thêm người mới vào hệ thống")
    else:
        print("\nKhông có ảnh nào được lưu!")
        # Xóa thư mục rỗng
        if os.path.exists(save_dir):
            os.rmdir(save_dir)

if __name__ == "__main__":
    capture_faces()
