<br />

<div align="center"><a  href="#top"></a>

<img  src="https://scontent.fhan4-5.fna.fbcdn.net/v/t39.30808-6/311132686_10160574411287259_2334651095928618880_n.jpg?_nc_cat=103&ccb=1-7&_nc_sid=6ee11a&_nc_ohc=7Dr61rhBM_MQ7kNvwHR8lVa&_nc_oc=Adl9duhsI5y3tIe6V1XS7B0h14NIv7XdunCqKCBuF2jk8eaUhKtz1wAPBJIW34sYyD4&_nc_zt=23&_nc_ht=scontent.fhan4-5.fna&_nc_gid=5HZaSS_S17QlVY7V4XpCvw&oh=00_AfIew9R4oSEeo6ABAcbd6NxixGqn_6l_0P2LYL3YmBgyvg&oe=683B3A9F"  alt="Logo"  width="271"  height="209">

<h3 align="center">Hệ thống nhận diện sinh viên ra vào KTX thông qua nhận diện khuôn mặt</h3>

<p align="center">

Hệ thống sử dụng trí tuệ nhân tạo để nhận diện và so sánh khuôn mặt từ ảnh chân dung với hình ảnh thu được từ webcam hoặc video đầu vào, nhằm hỗ trợ quản lý và kiểm soát việc ra/vào của sinh viên tại Ký túc xá. Hệ thống hiện chỉ chạy được cục bộ thông qua Docker.

</div>

**Mục lục**

- [ℹ Thông tin về dự án](#ℹ-thông-tin-về-dự-án)
  - [👨‍💻 Thành viên nhóm](#-thành-viên-nhóm)
- [⚙️ Hướng dẫn cài đặt](#-Hướng-dẫn-cài-đặt)
  - [📝 Yêu Cầu Hệ Thống](#-Yêu-cầu-hệ-thống)
  - [🐳 Khởi Động Hệ Thống Bằng Docker](#-Khởi-động-hệ-thống-bằng-docker)
  - [📖 Hướng dẫn sử dụng](#-Hướng-dẫn-sử-dụng)
  - [🔒 Bảo mật và riêng tư](#-Bảo-mật-và-riêng-tư)

## Thông tin về dự án
Việc quản lý sinh viên ra vào Ký túc xá (KTX) là một nhiệm vụ quan trọng nhằm đảm bảo an ninh và trật tự trong khuôn viên trường học. Dự án của chúng tôi sử dụng Công nghệ Nhận diện Khuôn mặt ứng dụng AI để tự động xác minh và ghi nhận danh tính của sinh viên. Hệ thống hoạt động như sau:

- Sinh viên đăng ký tài khoản trên hệ thống và chụp ảnh chân dung của mình.
- Hệ thống sẽ ghi nhận sinh viên đã đăng kí thành công vào cơ sở dữ liệu.
- Khi sinh viên xuất hiện trước camera tại cổng KTX, hệ thống sẽ so sánh khuôn mặt thu được từ webcam/video với cơ sở dữ liệu ảnh đã lưu.
- Nếu phát hiện trùng khớp, hệ thống sẽ tự động ghi nhận và cho phép sinh viên vào/ra, đồng thời cập nhật vào nhật ký quản lý.

---

### Thành viên nhóm
Dự án được thực hiện bởi các thành viên:
* Tạ Quang Linh - [23020396](mailto:23020396@vnu.edu.vn)
* Ngô Nguyễn Khải Hưng - [23020382](mailto:23020382@vnu.edu.vn)
* Nguyễn Gia Khánh - [23020385](mailto:23020385@vnu.edu.vn)
* Lường Minh Trí - [23020440](mailto:23020440@vnu.edu.vn)

---

### Docker Hub Repository
- https://hub.docker.com/r/talinh/nhandiensvktx/tags

---

## ⚙️Hướng dẫn cài đặt

### 📝 Yêu Cầu Hệ Thống
Để cài đặt và vận hành hệ thống nhận diện sinh viên ra/vào KTX, bạn cần chuẩn bị:

- `Docker` hoặc `Docker Desktop` cài đặt sẵn trên máy.
- Kết nối mạng ổn định để tải `Docker images` và cập nhật hệ thống

💡 Lưu ý: Toàn bộ hệ thống đã được đóng gói trong `Docker`, giúp cài đặt và vận hành dễ dàng, không cần thiết lập môi trường thủ công phức tạp.
---
### 🐳 Khởi Động Hệ Thống Bằng Docker
Để có thể khởi chạy hệ thống cần làm theo các bước sau:

1️⃣ **Tải File Cấu Hình Docker**  
Tải file `docker-compose.yml` từ kho lưu trữ của hệ thống.

2️⃣ **Chuẩn Bị Thư Mục Làm Việc**  
Tạo một thư mục mới hoặc sử dụng thư mục hiện có để lưu file `docker-compose.yml`.

3️⃣ **Mở Terminal/Command Prompt**  
Mở Terminal (Linux/macOS) hoặc Command Prompt/PowerShell (Windows) và di chuyển đến thư mục đã lưu file `docker-compose.yml`.

4️⃣ **Khởi Động Ứng Dụng**
Chạy lệnh sau để Docker Compose khởi chạy hệ thống ở chế độ nền:
```bash
docker-compose up -d
```
Docker sẽ tự động tải về images cần thiết và khởi chạy các container của hệ thống.

5️⃣ **Truy Cập Ứng Dụng**

Sau khi khởi động thành công, mở trình duyệt và truy cập:
```bash
http://localhost:5001
```
6️⃣ Tắt Hệ Thống Khi Không Dùng
Để tắt hệ thống và dừng các container, chạy lệnh:
```bash
docker-compose down
```
---
### 📖Hướng dẫn sử dụng

1️⃣ **Đăng Ký Sinh Viên**  
- Sinh viên đăng ký tài khoản trên hệ thống và chụp ảnh chân dung của mình để hệ thống tạo hồ sơ nhận diện.

2️⃣ **Kích Hoạt Camera/Video Tại Cổng KTX**  
- Hệ thống sẽ bật webcam hoặc camera IP để giám sát cổng vào/ra ký túc xá.
- Camera sẽ gửi hình ảnh khuôn mặt về hệ thống để nhận diện real-time.

3️⃣ **Nhận Diện Khuôn Mặt và Xác Minh Danh Tính**  
- Hệ thống sử dụng AI để so sánh khuôn mặt thu được với cơ sở dữ liệu.
- Nếu khớp với hồ sơ sinh viên đã đăng ký, hệ thống sẽ cho phép vào/ra.

4️⃣ **Ghi Nhận Lịch Sử Ra/Vào**  
- Mỗi lần sinh viên ra/vào sẽ được ghi nhận kèm theo:  
  - Thời gian, tên sinh viên, mã số sinh viên, phòng, trạng thái xác minh.

5️⃣ **Dành Cho Admin (Quản Lý Hệ Thống)**  
- Admin có thể truy cập bảng điều khiển (Dashboard) để:  
  - Quản lý thông tin sinh viên (thêm, sửa, xóa).  
  - Xem lịch sử ra/vào ký túc xá.  
  - Quản lý cấu hình hệ thống.

💡 **Lưu ý:** Hệ thống yêu cầu cấp quyền truy cập camera. Vui lòng đảm bảo sinh viên đã đồng ý sử dụng.

---

### 🔒 Bảo Mật và Quyền Riêng Tư

- Hệ thống yêu cầu quyền truy cập **camera/webcam** để thực hiện nhận diện khuôn mặt.
- Tất cả dữ liệu (bao gồm ảnh chân dung, thông tin cá nhân sinh viên và lịch sử ra/vào) sẽ được lưu trữ an toàn trong **cơ sở dữ liệu nội bộ** của hệ thống, không chia sẻ với bên thứ ba.
- Việc thu thập và sử dụng dữ liệu chỉ nhằm mục đích quản lý nội bộ ký túc xá.
- Hệ thống yêu cầu sinh viên **đồng ý sử dụng dữ liệu cá nhân** trước khi đăng ký và sử dụng.
- Mọi quyền truy cập và quản trị hệ thống đều yêu cầu xác thực và phân quyền rõ ràng để đảm bảo an toàn dữ liệu.

💡 **Lưu ý:** Hãy đảm bảo thực hiện đầy đủ **chính sách bảo mật và quyền riêng tư** phù hợp với quy định của nhà trường và pháp luật hiện hành.


---
### 💡Notes
- Nếu có bất kỳ thắc mắc hoặc muốn đóng góp ý tưởng, vui lòng liên hệ với nhóm phát triển qua email.

[Link báo cáo](https://www.notion.so/T-i-li-u-thi-t-k-h-th-ng-nh-n-di-n-sinh-vi-n-ra-v-o-k-t-c-x-1f695f47bee48087aff8e10d29136c4b?pvs=4)