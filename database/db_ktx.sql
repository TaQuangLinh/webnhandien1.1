-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Máy chủ: 127.0.0.1
-- Thời gian đã tạo: Th5 29, 2025 lúc 07:14 AM
-- Phiên bản máy phục vụ: 11.7.2-MariaDB
-- Phiên bản PHP: 8.2.4

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Cơ sở dữ liệu: `db_ktx`
--

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `nv5_dormitory_access_logs`
--

DROP TABLE IF EXISTS `nv5_dormitory_access_logs`;
CREATE TABLE IF NOT EXISTS `nv5_dormitory_access_logs` (
  `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT,
  `student_id` int(11) UNSIGNED NOT NULL COMMENT 'ID sinh viên',
  `student_code` varchar(20) NOT NULL COMMENT 'Mã sinh viên (để tra cứu nhanh)',
  `access_type` tinyint(1) NOT NULL COMMENT '1: Vào ký túc xá, 2: Ra khỏi ký túc xá',
  `access_time` int(11) NOT NULL COMMENT 'Thời gian ra/vào (timestamp)',
  `gate_location` varchar(100) NOT NULL DEFAULT '' COMMENT 'Vị trí cổng (cổng chính, cổng phụ, cổng sau)',
  `verification_method` varchar(50) NOT NULL DEFAULT '' COMMENT 'Phương thức xác thực (thẻ sinh viên, khuôn mặt, vân tay, QR code)',
  `device_id` varchar(100) NOT NULL DEFAULT '' COMMENT 'ID thiết bị quét/nhận diện',
  `device_name` varchar(100) NOT NULL DEFAULT '' COMMENT 'Tên thiết bị',
  `ip_address` varchar(45) NOT NULL DEFAULT '' COMMENT 'Địa chỉ IP thiết bị',
  `photo_path` varchar(255) NOT NULL DEFAULT '' COMMENT 'Đường dẫn ảnh chụp khi ra/vào',
  `recognition_rate` float NOT NULL DEFAULT 0 COMMENT 'Tỷ lệ nhận diện (nếu dùng AI nhận diện khuôn mặt)',
  `card_number` varchar(50) NOT NULL DEFAULT '' COMMENT 'Số thẻ sinh viên (nếu dùng thẻ)',
  `latitude` varchar(20) NOT NULL DEFAULT '' COMMENT 'Vĩ độ GPS',
  `longitude` varchar(20) NOT NULL DEFAULT '' COMMENT 'Kinh độ GPS',
  `notes` varchar(255) NOT NULL DEFAULT '' COMMENT 'Ghi chú (lý do đặc biệt, cảnh báo...)',
  `status` tinyint(1) NOT NULL DEFAULT 1 COMMENT '0: Thất bại/Từ chối, 1: Thành công, 2: Nghi ngờ/Cần kiểm tra',
  `created_time` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `student_id` (`student_id`),
  KEY `student_code` (`student_code`),
  KEY `access_type` (`access_type`),
  KEY `access_time` (`access_time`),
  KEY `gate_location` (`gate_location`),
  KEY `verification_method` (`verification_method`),
  KEY `status` (`status`),
  KEY `device_id` (`device_id`)
) ENGINE=InnoDB AUTO_INCREMENT=82 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Lịch sử nhận diện ra vào ký túc xá';

--
-- Đang đổ dữ liệu cho bảng `nv5_dormitory_access_logs`
--

INSERT INTO `nv5_dormitory_access_logs` (`id`, `student_id`, `student_code`, `access_type`, `access_time`, `gate_location`, `verification_method`, `device_id`, `device_name`, `ip_address`, `photo_path`, `recognition_rate`, `card_number`, `latitude`, `longitude`, `notes`, `status`, `created_time`) VALUES
(1, 1, 'SV001', 1, 1748245155, 'Cổng chính', 'Thẻ sinh viên', 'DEVICE_001', 'Đầu đọc thẻ cổng chính', '192.168.1.100', 'uploads/access/sv001_in_001.jpg', 0, 'CARD001', '21.0285', '105.8542', 'Ra vào bình thường', 1, 1748245155),
(2, 1, 'SV001', 2, 1748246955, 'Cổng chính', 'Nhận diện khuôn mặt', 'DEVICE_002', 'Camera AI cổng chính', '192.168.1.101', 'uploads/access/sv001_out_001.jpg', 95.5, '', '21.0285', '105.8542', 'Nhận diện thành công', 1, 1748246955),
(3, 2, 'SV002', 1, 1748241555, 'Cổng phụ', 'QR Code', 'DEVICE_003', 'Máy quét QR cổng phụ', '192.168.1.102', 'uploads/access/sv002_in_001.jpg', 0, '', '21.0285', '105.8542', 'Sử dụng QR code trên điện thoại', 1, 1748241555);

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `nv5_dormitory_admin_accounts`
--

DROP TABLE IF EXISTS `nv5_dormitory_admin_accounts`;
CREATE TABLE IF NOT EXISTS `nv5_dormitory_admin_accounts` (
  `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL COMMENT 'Tên đăng nhập',
  `password` varchar(255) NOT NULL COMMENT 'Mật khẩu (đã mã hóa)',
  `full_name` varchar(100) NOT NULL COMMENT 'Họ tên quản trị viên',
  `email` varchar(100) NOT NULL DEFAULT '' COMMENT 'Email',
  `phone` varchar(20) NOT NULL DEFAULT '' COMMENT 'Số điện thoại',
  `role` varchar(50) NOT NULL DEFAULT 'admin' COMMENT 'Vai trò (admin, manager, staff)',
  `permissions` text DEFAULT NULL COMMENT 'Quyền hạn (JSON)',
  `last_login` int(11) NOT NULL DEFAULT 0 COMMENT 'Lần đăng nhập cuối',
  `last_ip` varchar(45) NOT NULL DEFAULT '' COMMENT 'IP đăng nhập cuối',
  `status` tinyint(1) NOT NULL DEFAULT 1 COMMENT '0: Khóa, 1: Hoạt động',
  `created_time` int(11) NOT NULL DEFAULT 0,
  `updated_time` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`),
  KEY `role` (`role`),
  KEY `status` (`status`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Tài khoản quản trị ký túc xá';

--
-- Đang đổ dữ liệu cho bảng `nv5_dormitory_admin_accounts`
--

INSERT INTO `nv5_dormitory_admin_accounts` (`id`, `username`, `password`, `full_name`, `email`, `phone`, `role`, `permissions`, `last_login`, `last_ip`, `status`, `created_time`, `updated_time`) VALUES
(1, 'admin', '123', 'Quản trị viên hệ thống', 'admin@dormitory.edu.vn', '0123456789', 'admin', '{\"manage_students\": true, \"manage_access\": true, \"view_reports\": true, \"manage_accounts\": true}', 1748409662, '127.0.0.1', 1, 1748248755, 1748409662),
(2, 'manager', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Quản lý ký túc xá', 'manager@dormitory.edu.vn', '0987654321', 'manager', '{\"manage_students\": true, \"view_reports\": true}', 0, '', 1, 1748248755, 1748248755);

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `nv5_dormitory_students`
--

DROP TABLE IF EXISTS `nv5_dormitory_students`;
CREATE TABLE IF NOT EXISTS `nv5_dormitory_students` (
  `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT,
  `student_code` varchar(20) NOT NULL COMMENT 'Mã sinh viên',
  `full_name` varchar(100) NOT NULL COMMENT 'Họ tên sinh viên',
  `birth_date` date DEFAULT NULL COMMENT 'Ngày sinh',
  `gender` tinyint(1) NOT NULL DEFAULT 1 COMMENT '1: Nam, 2: Nữ',
  `class_name` varchar(100) NOT NULL DEFAULT '' COMMENT 'Lớp học',
  `major` varchar(150) NOT NULL DEFAULT '' COMMENT 'Ngành học',
  `course` varchar(20) NOT NULL DEFAULT '' COMMENT 'Khóa học (VD: K65)',
  `faculty` varchar(150) NOT NULL DEFAULT '' COMMENT 'Khoa',
  `room_number` varchar(20) NOT NULL DEFAULT '' COMMENT 'Số phòng ở',
  `phone` varchar(20) NOT NULL DEFAULT '' COMMENT 'Số điện thoại',
  `email` varchar(100) NOT NULL DEFAULT '' COMMENT 'Email sinh viên',
  `id_card` varchar(20) NOT NULL DEFAULT '' COMMENT 'Số CMND/CCCD',
  `hometown` varchar(255) NOT NULL DEFAULT '' COMMENT 'Quê quán',
  `parent_name` varchar(100) NOT NULL DEFAULT '' COMMENT 'Tên phụ huynh',
  `parent_phone` varchar(20) NOT NULL DEFAULT '' COMMENT 'Số điện thoại phụ huynh',
  `emergency_contact` varchar(255) NOT NULL DEFAULT '' COMMENT 'Liên hệ khẩn cấp',
  `photo` varchar(255) NOT NULL DEFAULT '' COMMENT 'Ảnh sinh viên',
  `notes` text DEFAULT NULL COMMENT 'Ghi chú',
  `status` tinyint(1) NOT NULL DEFAULT 1 COMMENT '0: Không hoạt động, 1: Hoạt động',
  `created_time` int(11) NOT NULL DEFAULT 0,
  `updated_time` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `student_code` (`student_code`),
  KEY `full_name` (`full_name`),
  KEY `class_name` (`class_name`),
  KEY `room_number` (`room_number`),
  KEY `status` (`status`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Thông tin sinh viên ký túc xá';

--
-- Đang đổ dữ liệu cho bảng `nv5_dormitory_students`
--

INSERT INTO `nv5_dormitory_students` (`id`, `student_code`, `full_name`, `birth_date`, `gender`, `class_name`, `major`, `course`, `faculty`, `room_number`, `phone`, `email`, `id_card`, `hometown`, `parent_name`, `parent_phone`, `emergency_contact`, `photo`, `notes`, `status`, `created_time`, `updated_time`) VALUES
(1, 'SV001', 'Tạ Quang Linh', '2003-05-15', 1, 'CNTT01', 'Công nghệ thông tin', '', '', 'A101', '0123456789', 'an.nv@student.edu.vn', '123456789012', 'Hà Nội', 'Nguyễn Văn Bình', '0987654321', 'Nguyễn Thị Cúc - 0912345678', 'uploads/students/sv001.jpg', NULL, 1, 1748248755, 1748283028),
(2, 'SV002', 'Trần Thị Bình', '2003-08-20', 2, 'CNTT02', 'Công nghệ thông tin', 'K65', 'Công nghệ thông tin', 'B205', '0234567890', 'binh.tt@student.edu.vn', '234567890123', 'Hải Phòng', 'Trần Văn Dũng', '0876543210', 'Trần Thị Lan - 0823456789', 'uploads/students/sv002.jpg', NULL, 1, 1748248755, 1748248755),
(3, 'SV003', 'Lê Minh Cường', '2003-12-10', 1, 'KT01', 'Kế toán', 'K65', 'Kinh tế', 'A203', '0345678901', 'cuong.lm@student.edu.vn', '345678901234', 'Nam Định', 'Lê Văn Mạnh', '0765432109', 'Lê Thị Nga - 0734567890', 'uploads/students/sv003.jpg', NULL, 1, 1748248755, 1748248755),
(4, '17A100101216', 'Nguyễn Văn Lâm', '1999-10-02', 1, 'CN11', 'CNTT', '', '', 'A15', '0868378653', 'vanlam99qv1@gmaill.com', '', '', '', '', '', '', NULL, 0, 1748267411, 1748273314);

--
-- Các ràng buộc cho các bảng đã đổ
--

--
-- Các ràng buộc cho bảng `nv5_dormitory_access_logs`
--
ALTER TABLE `nv5_dormitory_access_logs`
  ADD CONSTRAINT `fk_access_student` FOREIGN KEY (`student_id`) REFERENCES `nv5_dormitory_students` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
