// Global variables
const API_BASE_URL = window.location.origin;
let currentSection = 'dashboard';

// Initialize when DOM is loaded
document.addEventListener("DOMContentLoaded", function () {
    initializeElements();
    setupEventListeners();
    checkAuthentication();
    updateDateTime();
    setInterval(updateDateTime, 1000);

    // Load dashboard data
    loadDashboardData();
});

function initializeElements() {
    // Initialize any required elements
    console.log('Dashboard initialized');
}

function setupEventListeners() {
    // Mobile menu toggle
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const sidebar = document.getElementById('sidebar');

    if (mobileMenuToggle && sidebar) {
        mobileMenuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('active');
        });

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function(e) {
            if (window.innerWidth <= 1200 &&
                !sidebar.contains(e.target) &&
                !mobileMenuToggle.contains(e.target)) {
                sidebar.classList.remove('active');
            }
        });
    }

    // Menu item clicks
    document.querySelectorAll('.menu-item').forEach(item => {
        item.addEventListener('click', function() {
            if (this.classList.contains('logout')) {
                handleLogout();
                return;
            }

            const section = this.getAttribute('data-section');
            if (section) {
                switchSection(section);
                // Close mobile menu after selection
                if (window.innerWidth <= 1200) {
                    sidebar.classList.remove('active');
                }
            }
        });
    });

    // Student search
    const studentSearch = document.getElementById('student-search');
    if (studentSearch) {
        studentSearch.addEventListener('input', debounce(searchStudents, 300));
    }

    // MSSV search
    const mssvInput = document.getElementById('mssv-input');
    if (mssvInput) {
        mssvInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchByMSSV();
            }
        });
    }
}

function checkAuthentication() {
    // Check if user is authenticated
    fetch(`${API_BASE_URL}/api/check-session`, {
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success || !data.logged_in) {
            // Not authenticated, redirect to home (will show login)
            window.location.href = '/';
        }
    })
    .catch(error => {
        console.error('Auth check failed:', error);
        // Redirect to home on error
        window.location.href = '/';
    });
}

function updateDateTime() {
    const now = new Date();
    const dateElement = document.getElementById('current-date');
    const timeElement = document.getElementById('current-time');

    if (dateElement) {
        dateElement.textContent = now.toLocaleDateString('vi-VN', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    if (timeElement) {
        timeElement.textContent = now.toLocaleTimeString('vi-VN');
    }
}

function switchSection(sectionName) {
    // Update active menu item
    document.querySelectorAll('.menu-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');

    // Hide all sections
    document.querySelectorAll('.dashboard-section, .student-section, .checkin-section, .access-logs-section').forEach(section => {
        section.classList.remove('active');
    });

    // Show selected section
    const targetSection = document.getElementById(`${sectionName}-section`);
    if (targetSection) {
        targetSection.classList.add('active');
    }

    // Update page title
    const titles = {
        'dashboard': 'Trang chủ',
        'student': 'Quản lý sinh viên',
        'checkin': 'Ghi nhận ra/vào',
        'access-logs': 'Lịch sử ra/vào'
    };

    document.getElementById('page-title').textContent = titles[sectionName] || 'Trang chủ';
    currentSection = sectionName;

    // Load section data
    switch(sectionName) {
        case 'dashboard':
            loadDashboardData();
            break;
        case 'student':
            loadStudents();
            break;
        case 'checkin':
            // Initialize checkin section
            break;
        case 'access-logs':
            loadAccessLogs();
            break;
    }
}

async function loadDashboardData() {
    try {
        // Load statistics
        await loadStatistics();
        await loadRecentActivity();
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showStatus('Lỗi tải dữ liệu dashboard', 'error');
    }
}

async function loadStatistics() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/students`, {
            credentials: 'include'
        });

        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                const totalStudents = result.data.students.length;
                document.getElementById('total-students').textContent = totalStudents;

                // Update student count in student section
                const studentCountElement = document.getElementById('student-count');
                if (studentCountElement) {
                    studentCountElement.textContent = totalStudents;
                }
            }
        }

        // Load access logs for today's statistics
        const logsResponse = await fetch(`${API_BASE_URL}/api/access-logs`, {
            credentials: 'include'
        });

        if (logsResponse.ok) {
            const logsResult = await logsResponse.json();
            if (logsResult.success) {
                const today = new Date().toDateString();
                const todayLogs = logsResult.data.filter(log =>
                    new Date(log.access_time).toDateString() === today
                );

                const checkins = todayLogs.filter(log => log.access_type === 'entry').length;
                const checkouts = todayLogs.filter(log => log.access_type === 'exit').length;

                document.getElementById('checkins-today').textContent = checkins;
                document.getElementById('checkouts-today').textContent = checkouts;

                // Calculate students currently inside (simplified)
                const studentsInside = checkins - checkouts;
                document.getElementById('students-inside').textContent = Math.max(0, studentsInside);
            }
        }
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

async function loadRecentActivity() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/access-logs?limit=10`, {
            credentials: 'include'
        });

        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                const recentLogs = result.data || [];
                displayRecentActivity(recentLogs);
            } else {
                throw new Error(result.message || 'API returned error');
            }
        } else {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
    } catch (error) {
        console.error('Error loading recent activity:', error);
        document.getElementById('recent-activity').innerHTML = `
            <div class="loading-message">
                <i class="fas fa-exclamation-triangle"></i> Lỗi tải dữ liệu: ${error.message}
            </div>
        `;
    }
}

function displayRecentActivity(logs) {
    const container = document.getElementById('recent-activity');

    if (!logs || logs.length === 0) {
        container.innerHTML = `
            <div class="loading-message">
                <i class="fas fa-info-circle"></i> Chưa có hoạt động nào
            </div>
        `;
        return;
    }

    const html = logs.map(log => {
        const time = new Date(log.access_time).toLocaleString('vi-VN');
        const statusClass = log.access_type === 'entry' ? 'status-in' : 'status-out';
        const actionText = log.access_type === 'entry' ? 'vào' : 'ra';

        return `
            <div class="log-item">
                <div class="log-status ${statusClass}"></div>
                <div class="log-details">
                    <div class="log-time">${time}</div>
                    <div class="log-message">
                        <strong>${log.student_name || 'N/A'} (${log.student_code || 'N/A'})</strong>
                        ${actionText} ký túc xá
                    </div>
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = html;
}

async function loadStudents() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/students`, {
            credentials: 'include'
        });

        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                displayStudents(result.data.students);
            }
        }
    } catch (error) {
        console.error('Error loading students:', error);
        document.getElementById('students-tbody').innerHTML = `
            <tr>
                <td colspan="6" class="loading-message">
                    <i class="fas fa-exclamation-triangle"></i> Lỗi tải dữ liệu
                </td>
            </tr>
        `;
    }
}

function displayStudents(students) {
    const tbody = document.getElementById('students-tbody');

    if (students.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="loading-message">
                    <i class="fas fa-info-circle"></i> Chưa có sinh viên nào
                </td>
            </tr>
        `;
        return;
    }

    const html = students.map(student => `
        <tr>
            <td>${student.student_code}</td>
            <td>${student.full_name}</td>
            <td>${student.room_number || 'N/A'}</td>
            <td>${student.class_name || 'N/A'}</td>
            <td>
                <span class="badge badge-success">Hoạt động</span>
            </td>
            <td>
                <button class="action-btn edit-btn" onclick="editStudent(${student.id})">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="action-btn delete-btn" onclick="deleteStudent(${student.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');

    tbody.innerHTML = html;
}

async function loadAccessLogs() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/access-logs`, {
            credentials: 'include'
        });

        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                displayAccessLogs(result.data || []);
            } else {
                throw new Error(result.message || 'API returned error');
            }
        } else {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
    } catch (error) {
        console.error('Error loading access logs:', error);
        document.getElementById('access-logs-tbody').innerHTML = `
            <tr>
                <td colspan="6" class="loading-message">
                    <i class="fas fa-exclamation-triangle"></i> Lỗi tải dữ liệu: ${error.message}
                </td>
            </tr>
        `;
    }
}

function displayAccessLogs(logs) {
    const tbody = document.getElementById('access-logs-tbody');

    if (!logs || logs.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="loading-message">
                    <i class="fas fa-info-circle"></i> Chưa có lịch sử ra/vào
                </td>
            </tr>
        `;
        return;
    }

    const html = logs.map(log => {
        const time = new Date(log.access_time).toLocaleString('vi-VN');
        const typeText = log.access_type === 'entry' ? 'Vào' : 'Ra';
        const typeClass = log.access_type === 'entry' ? 'badge-success' : 'badge-warning';

        return `
            <tr>
                <td>${time}</td>
                <td>${log.student_name || 'N/A'}</td>
                <td>${log.student_code || 'N/A'}</td>
                <td>${log.room_number || 'N/A'}</td>
                <td>
                    <span class="badge ${typeClass}">${typeText}</span>
                </td>
                <td>
                    <span class="badge badge-success">Thành công</span>
                </td>
            </tr>
        `;
    }).join('');

    tbody.innerHTML = html;
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function showStatus(message, type = 'info') {
    const statusElement = document.getElementById('statusMessage');
    statusElement.textContent = message;
    statusElement.className = `status-message ${type}`;
    statusElement.style.display = 'block';

    setTimeout(() => {
        statusElement.style.display = 'none';
    }, 3000);
}

// Action functions
function refreshRecentActivity() {
    loadRecentActivity();
    showStatus('Đã làm mới hoạt động gần đây', 'success');
}

function refreshAccessLogs() {
    loadAccessLogs();
    showStatus('Đã làm mới lịch sử ra/vào', 'success');
}

function openStudentManagement() {
    openStudentModal();
}

function openFaceRecognition() {
    // Implement face recognition functionality
    showStatus('Chức năng nhận diện khuôn mặt đang được phát triển', 'info');
}

function searchByMSSV() {
    const mssv = document.getElementById('mssv-input').value.trim();
    if (!mssv) {
        showStatus('Vui lòng nhập mã số sinh viên', 'warning');
        return;
    }

    // Implement MSSV search
    showStatus(`Đang tìm kiếm sinh viên: ${mssv}`, 'info');
}

function searchStudents() {
    const query = document.getElementById('student-search').value.trim();
    // Implement student search
}

function editStudent(id) {
    openStudentModal(id);
}

async function deleteStudent(id) {
    if (confirm('Bạn có chắc chắn muốn xóa sinh viên này?')) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/students/${id}`, {
                method: 'DELETE',
                credentials: 'include'
            });

            const result = await response.json();

            if (result.success) {
                showStatus('Xóa sinh viên thành công', 'success');

                // Reload student list if we're on student section
                if (currentSection === 'student') {
                    loadStudents();
                }

                // Reload dashboard stats
                loadStatistics();
            } else {
                showStatus('Lỗi: ' + result.message, 'error');
            }
        } catch (error) {
            showStatus('Lỗi kết nối server', 'error');
        }
    }
}

function handleLogout() {
    if (confirm('Bạn có chắc chắn muốn đăng xuất?')) {
        fetch(`${API_BASE_URL}/api/logout`, {
            method: 'POST',
            credentials: 'include'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Clear localStorage
                localStorage.removeItem('dormitory_token');
                localStorage.removeItem('dormitory_user');

                // Redirect to home page (will show login)
                window.location.href = '/';
            } else {
                showStatus('Lỗi đăng xuất: ' + data.message, 'error');
            }
        })
        .catch(error => {
            // Force redirect even if API fails
            localStorage.removeItem('dormitory_token');
            localStorage.removeItem('dormitory_user');
            window.location.href = '/';
        });
    }
}

// Modal functions
function openStudentModal(studentId = null) {
    const modal = document.getElementById('studentModal');
    const modalTitle = document.getElementById('modalTitle');
    const form = document.getElementById('studentForm');

    // Reset form
    form.reset();
    document.getElementById('studentId').value = '';

    // Re-enable student code field (in case it was disabled from edit mode)
    document.getElementById('studentCode').disabled = false;

    if (studentId) {
        // Edit mode
        modalTitle.textContent = 'Sửa thông tin sinh viên';
        loadStudentData(studentId);
    } else {
        // Add mode
        modalTitle.textContent = 'Thêm sinh viên mới';
    }

    // Show modal
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeStudentModal() {
    const modal = document.getElementById('studentModal');
    modal.classList.remove('active');
    document.body.style.overflow = 'auto';
}

async function loadStudentData(studentId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/students/${studentId}`, {
            credentials: 'include'
        });

        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                const student = result.data;

                // Fill form with student data
                document.getElementById('studentId').value = student.id;
                document.getElementById('studentCode').value = student.student_code || '';
                document.getElementById('fullName').value = student.full_name || '';
                document.getElementById('birthDate').value = student.birth_date || '';
                document.getElementById('gender').value = student.gender || '';
                document.getElementById('className').value = student.class_name || '';
                document.getElementById('major').value = student.major || '';
                document.getElementById('roomNumber').value = student.room_number || '';
                document.getElementById('phone').value = student.phone || '';
                document.getElementById('email').value = student.email || '';

                // Disable student code field in edit mode
                document.getElementById('studentCode').disabled = true;
            }
        }
    } catch (error) {
        showStatus('Lỗi tải thông tin sinh viên', 'error');
    }
}

async function saveStudent() {
    const form = document.getElementById('studentForm');
    const formData = new FormData(form);
    const studentId = document.getElementById('studentId').value;

    // Validate required fields
    const studentCode = document.getElementById('studentCode').value.trim();
    const fullName = document.getElementById('fullName').value.trim();

    if (!studentCode || !fullName) {
        showStatus('Vui lòng nhập đầy đủ mã sinh viên và họ tên', 'warning');
        return;
    }

    // Prepare data
    const data = {
        student_code: studentCode,
        full_name: fullName,
        birth_date: formData.get('birth_date') || null,
        gender: formData.get('gender') || null,
        class_name: formData.get('class_name') || null,
        major: formData.get('major') || null,
        room_number: formData.get('room_number') || null,
        phone: formData.get('phone') || null,
        email: formData.get('email') || null
    };

    // Add captured images if any
    if (capturedImages.length > 0) {
        data.images_base64 = capturedImages;
    }

    try {
        const url = studentId ?
            `${API_BASE_URL}/api/students/${studentId}` :
            `${API_BASE_URL}/api/students`;

        const method = studentId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showStatus(studentId ? 'Cập nhật sinh viên thành công' : 'Thêm sinh viên thành công', 'success');
            closeStudentModal();

            // Reload student list if we're on student section
            if (currentSection === 'student') {
                loadStudents();
            }

            // Reload dashboard stats
            loadStatistics();
        } else {
            showStatus('Lỗi: ' + result.message, 'error');
        }
    } catch (error) {
        showStatus('Lỗi kết nối server', 'error');
    }
}

// Close modal when clicking outside
document.addEventListener('click', function(e) {
    const modal = document.getElementById('studentModal');
    if (e.target === modal) {
        closeStudentModal();
    }
});

// Close modal with Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeStudentModal();
    }
});

// Camera functionality
let cameraStream = null;
let capturedImages = [];

async function startCamera() {
    try {
        const video = document.getElementById('cameraVideo');
        const startBtn = document.getElementById('startCameraBtn');
        const captureBtn = document.getElementById('captureBtn');
        const stopBtn = document.getElementById('stopCameraBtn');

        // Request camera access
        cameraStream = await navigator.mediaDevices.getUserMedia({
            video: { width: 640, height: 480 }
        });

        video.srcObject = cameraStream;
        video.style.display = 'block';

        // Update button visibility
        startBtn.style.display = 'none';
        captureBtn.style.display = 'inline-flex';
        stopBtn.style.display = 'inline-flex';

        showStatus('Camera đã được bật', 'success');
    } catch (error) {
        showStatus('Không thể truy cập camera. Vui lòng kiểm tra quyền truy cập.', 'error');
    }
}

function captureImage() {
    const video = document.getElementById('cameraVideo');
    const canvas = document.getElementById('captureCanvas');
    const ctx = canvas.getContext('2d');

    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw video frame to canvas
    ctx.drawImage(video, 0, 0);

    // Convert to base64
    const imageData = canvas.toDataURL('image/jpeg', 0.8);

    // Add to captured images array
    capturedImages.push(imageData);

    // Display captured image
    displayCapturedImages();

    showStatus(`Đã chụp ảnh ${capturedImages.length}`, 'success');
}

function displayCapturedImages() {
    const container = document.getElementById('capturedImages');

    const html = capturedImages.map((imageData, index) => `
        <div class="captured-image">
            <img src="${imageData}" alt="Captured ${index + 1}">
            <button class="remove-btn" onclick="removeCapturedImage(${index})">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `).join('');

    container.innerHTML = html;
}

function removeCapturedImage(index) {
    capturedImages.splice(index, 1);
    displayCapturedImages();
    showStatus('Đã xóa ảnh', 'info');
}

function stopCamera() {
    const video = document.getElementById('cameraVideo');
    const startBtn = document.getElementById('startCameraBtn');
    const captureBtn = document.getElementById('captureBtn');
    const stopBtn = document.getElementById('stopCameraBtn');

    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }

    video.style.display = 'none';
    video.srcObject = null;

    // Update button visibility
    startBtn.style.display = 'inline-flex';
    captureBtn.style.display = 'none';
    stopBtn.style.display = 'none';

    showStatus('Camera đã được tắt', 'info');
}

// Reset camera when modal closes
function closeStudentModal() {
    const modal = document.getElementById('studentModal');
    modal.classList.remove('active');
    document.body.style.overflow = 'auto';

    // Stop camera and reset
    stopCamera();
    capturedImages = [];
    displayCapturedImages();
}

// Face Recognition System
let recognitionStream = null;
let recognitionInterval = null;
let isRecognizing = false;
let isProcessingRequest = false; // Flag để kiểm soát request
let lastRecognitionTime = 0;
const RECOGNITION_COOLDOWN = 1000; // 1 second between recognitions để tránh spam

async function startFaceRecognition() {
    try {
        const video = document.getElementById('recognitionVideo');
        const canvas = document.getElementById('recognitionCanvas');
        const placeholder = document.getElementById('cameraPlaceholder');
        const startBtn = document.getElementById('startRecognitionBtn');
        const stopBtn = document.getElementById('stopRecognitionBtn');
        const statusIndicator = document.querySelector('#recognitionStatus .status-indicator');

        // Request camera access
        recognitionStream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 640 },
                height: { ideal: 480 },
                facingMode: 'user'
            }
        });

        video.srcObject = recognitionStream;

        // Show video, hide placeholder
        video.style.display = 'block';
        canvas.style.display = 'block';
        placeholder.style.display = 'none';

        // Update buttons
        const restartBtn = document.getElementById('restartRecognitionBtn');
        startBtn.style.display = 'none';
        stopBtn.style.display = 'inline-flex';
        restartBtn.style.display = 'none';

        // Update status
        statusIndicator.className = 'status-indicator recognizing';
        statusIndicator.innerHTML = '<i class="fas fa-eye"></i> Đang nhận diện...';

        isRecognizing = true;
        isProcessingRequest = false; // Reset flag khi bắt đầu

        // Start recognition loop
        video.addEventListener('loadedmetadata', () => {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;

            recognitionInterval = setInterval(processRecognition, 1000); // Process every 1 second để tránh spam request
        });

        showStatus('Camera nhận diện đã được bật', 'success');

    } catch (error) {
        showStatus('Không thể truy cập camera. Vui lòng kiểm tra quyền truy cập.', 'error');

        const statusIndicator = document.querySelector('#recognitionStatus .status-indicator');
        statusIndicator.className = 'status-indicator error';
        statusIndicator.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Lỗi camera';
    }
}

async function processRecognition() {
    // **CHỈ XỬ LÝ KHI KHÔNG CÓ REQUEST ĐANG CHẠY**
    if (!isRecognizing || isProcessingRequest) return;

    const now = Date.now();
    if (now - lastRecognitionTime < RECOGNITION_COOLDOWN) return;

    try {
        // **SET FLAG ĐỂ NGĂN REQUEST KHÁC**
        isProcessingRequest = true;

        const video = document.getElementById('recognitionVideo');
        const canvas = document.getElementById('recognitionCanvas');
        const ctx = canvas.getContext('2d');

        // Draw current frame to canvas
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Convert to base64
        const frameData = canvas.toDataURL('image/jpeg', 0.8);

        // Get selected access type
        const accessType = document.querySelector('input[name="accessType"]:checked').value;

        // Send to recognition API
        const response = await fetch(`${API_BASE_URL}/api/recognize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                frame: frameData,
                auto_log_access: true,
                access_type: parseInt(accessType),
                gate_location: 'Cổng chính',
                device_id: 'FACE_RECOGNITION_CAM',
                device_name: 'Camera nhận diện khuôn mặt'
            })
        });

        const result = await response.json();

        if (result.success) {
            if (result.results && result.results.length > 0) {
                // Nhận diện thành công
                const student = result.results[0];

                // Display student info
                displayRecognizedStudent(student);

                // Draw bounding box on canvas
                drawBoundingBox(ctx, student.bbox, student.name, student.score);

                // Show success message and auto-hide after 3 seconds
                showAccessSuccess(accessType, student);

                // **DỪNG HOÀN TOÀN SAU KHI THÀNH CÔNG NHƯNG GIỮ ẢNH**

                // Hiển thị kết quả trong 3s rồi dừng hoàn toàn nhưng giữ ảnh
                setTimeout(() => {
                    stopFaceRecognitionKeepImage(true, student.name);
                }, 3000);

                lastRecognitionTime = now;
            } else {
                // Không nhận diện được - hiển thị thông báo
                displayRecognitionFailure(result);

                // Clear canvas overlay
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

                // **RESET FLAG ĐỂ CHO PHÉP REQUEST TIẾP THEO**
                isProcessingRequest = false;
            }
        } else {
            // Lỗi API
            displayRecognitionError(result.error || 'Lỗi không xác định');

            // Clear canvas overlay
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

            // **RESET FLAG ĐỂ CHO PHÉP REQUEST TIẾP THEO**
            isProcessingRequest = false;
        }

    } catch (error) {
        // **RESET FLAG KHI CÓ LỖI**
        isProcessingRequest = false;
    }
}



function drawBoundingBox(ctx, bbox, name, score) {
    const [x1, y1, x2, y2] = bbox;

    // Draw bounding box
    ctx.strokeStyle = '#00ff00';
    ctx.lineWidth = 3;
    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

    // Draw label background
    const label = `${name} (${(score * 100).toFixed(1)}%)`;
    ctx.font = '16px Arial';
    const textWidth = ctx.measureText(label).width;

    ctx.fillStyle = 'rgba(0, 255, 0, 0.8)';
    ctx.fillRect(x1, y1 - 25, textWidth + 10, 25);

    // Draw label text
    ctx.fillStyle = 'white';
    ctx.fillText(label, x1 + 5, y1 - 8);
}

function displayRecognitionFailure(result) {
    const container = document.getElementById('student-info-display');
    const statusIndicator = document.querySelector('#recognitionStatus .status-indicator');

    // Update status indicator
    statusIndicator.className = 'status-indicator error';

    if (result.faces_detected === 0) {
        // Không phát hiện khuôn mặt
        statusIndicator.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Không phát hiện khuôn mặt';

        container.innerHTML = `
            <div class="recognition-failure-card">
                <div class="failure-icon">
                    <i class="fas fa-user-times"></i>
                </div>
                <h4>Không phát hiện khuôn mặt</h4>
                <p>${result.message}</p>
                <div class="failure-tips">
                    <small>
                        <i class="fas fa-lightbulb"></i>
                        Đảm bảo khuôn mặt rõ ràng và đủ sáng
                    </small>
                </div>
            </div>
        `;
    } else if (result.recognized_faces === 0 && result.faces_detected > 0) {
        // Phát hiện khuôn mặt nhưng không nhận diện được
        statusIndicator.innerHTML = '<i class="fas fa-question-circle"></i> Không nhận diện được';

        container.innerHTML = `
            <div class="recognition-failure-card">
                <div class="failure-icon">
                    <i class="fas fa-user-question"></i>
                </div>
                <h4>Khuôn mặt không được nhận diện</h4>
                <p>${result.message}</p>
                <div class="failure-details">
                    <small>Phát hiện ${result.faces_detected} khuôn mặt</small>
                </div>
                <div class="failure-tips">
                    <small>
                        <i class="fas fa-info-circle"></i>
                        Khuôn mặt không có trong database hoặc độ chính xác thấp
                    </small>
                </div>
            </div>
        `;
    }

    // Show notification
    showStatus(result.message, 'warning');
}

function displayRecognitionError(errorMessage) {
    const container = document.getElementById('student-info-display');
    const statusIndicator = document.querySelector('#recognitionStatus .status-indicator');

    // Update status indicator
    statusIndicator.className = 'status-indicator error';
    statusIndicator.innerHTML = '<i class="fas fa-exclamation-circle"></i> Lỗi nhận diện';

    container.innerHTML = `
        <div class="recognition-failure-card">
            <div class="failure-icon">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <h4>Lỗi hệ thống</h4>
            <p>${errorMessage}</p>
            <div class="failure-tips">
                <small>
                    <i class="fas fa-redo"></i>
                    Vui lòng thử lại sau
                </small>
            </div>
        </div>
    `;

    // Show notification
    showStatus('Lỗi nhận diện: ' + errorMessage, 'error');
}

function displayRecognizedStudent(student) {
    const container = document.getElementById('student-info-display');
    const statusIndicator = document.querySelector('#recognitionStatus .status-indicator');

    // Kiểm tra xem sinh viên có trong database không
    const foundInDb = student.found_in_db !== false; // Default true nếu không có field này

    // Update status dựa trên kết quả tìm kiếm
    if (foundInDb) {
        statusIndicator.className = 'status-indicator success';
        statusIndicator.innerHTML = '<i class="fas fa-check-circle"></i> Nhận diện thành công';
    } else {
        statusIndicator.className = 'status-indicator warning';
        statusIndicator.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Nhận diện nhưng chưa có thông tin';
    }

    // **THÔNG TIN VÀO/RA TỪ API**
    const smartAccessType = student.access_type || 1; // Default vào
    const actionText = student.action_text || 'vào';
    const isEntry = smartAccessType === 1;
    const accessIcon = isEntry ? 'fa-sign-in-alt' : 'fa-sign-out-alt';
    const accessColor = isEntry ? '#28a745' : '#dc3545';
    const accessText = isEntry ? 'VÀO KTX' : 'RA KHỎI KTX';

    // Tạo card thông tin sinh viên với trạng thái database
    const studentCard = `
        <div class="student-info-card ${!foundInDb ? 'unknown-student' : ''}">
            ${!foundInDb ? `
                <div class="database-status-banner" style="background-color: #ffc107; color: #212529;">
                    <i class="fas fa-database"></i>
                    <span>CHƯA CÓ THÔNG TIN TRONG DATABASE</span>
                </div>
            ` : ''}

            ${student.access_logged ? `
                <div class="access-status-banner" style="background-color: ${accessColor};">
                    <i class="fas ${accessIcon}"></i>
                    <span>${accessText}</span>
                </div>
            ` : ''}

            <div class="student-info-header">
                <div class="student-avatar ${!foundInDb ? 'unknown-avatar' : ''}">
                    ${foundInDb ? student.student_code.substring(0, 2) : '?'}
                </div>
                <div class="student-basic-info">
                    <h4>${student.name}</h4>
                    <div class="student-code">${student.student_code}</div>
                    ${!foundInDb ? `
                        <div class="recognition-score">
                            <i class="fas fa-percentage"></i>
                            Độ chính xác: ${(student.score * 100).toFixed(1)}%
                        </div>
                    ` : ''}
                </div>
            </div>
            <div class="student-details">
                <div class="detail-item ${!foundInDb ? 'missing-info' : ''}">
                    <i class="fas fa-home"></i>
                    <span>Phòng: ${student.room_number || 'Chưa có thông tin'}</span>
                </div>
                <div class="detail-item ${!foundInDb ? 'missing-info' : ''}">
                    <i class="fas fa-graduation-cap"></i>
                    <span>Lớp: ${student.class_name || 'Chưa có thông tin'}</span>
                </div>
                <div class="detail-item ${!foundInDb ? 'missing-info' : ''}">
                    <i class="fas fa-birthday-cake"></i>
                    <span>Sinh: ${student.birth_date || 'Chưa có thông tin'}</span>
                </div>
                <div class="detail-item">
                    <i class="fas fa-robot"></i>
                    <span>Nhận diện khuôn mặt</span>
                </div>
                ${student.access_logged ? `
                    <div class="detail-item access-logged">
                        <i class="fas fa-check-circle" style="color: ${accessColor};"></i>
                        <span>Đã ghi nhận ${actionText} KTX</span>
                    </div>
                ` : ''}
                ${!foundInDb ? `
                    <div class="detail-item missing-info">
                        <i class="fas fa-info-circle"></i>
                        <span>Vui lòng cập nhật thông tin sinh viên trong hệ thống</span>
                    </div>
                ` : ''}
            </div>
        </div>
    `;

    container.innerHTML = studentCard;
}

function showAccessSuccess(accessType, student) {
    const message = document.getElementById('accessSuccessMessage');
    const text = document.getElementById('accessSuccessText');

    // **SỬ DỤNG THÔNG TIN TỪ API RESPONSE**
    const smartAccessType = student.access_type || accessType; // Ưu tiên từ API
    const actionText = student.action_text || (smartAccessType === 1 ? 'vào KTX' : 'ra khỏi KTX'); // Từ API hoặc fallback

    text.textContent = `${student.name} đã ${actionText} thành công!`;

    message.style.display = 'block';

    // Auto hide after 3 seconds
    setTimeout(() => {
        message.style.display = 'none';
    }, 3000);
}

function stopFaceRecognition(isAutoStop = false, studentName = '') {
    const video = document.getElementById('recognitionVideo');
    const canvas = document.getElementById('recognitionCanvas');
    const placeholder = document.getElementById('cameraPlaceholder');
    const startBtn = document.getElementById('startRecognitionBtn');
    const stopBtn = document.getElementById('stopRecognitionBtn');
    const restartBtn = document.getElementById('restartRecognitionBtn');
    const statusIndicator = document.querySelector('#recognitionStatus .status-indicator');

    isRecognizing = false;
    isProcessingRequest = false; // Reset flag khi dừng

    // Stop recognition interval
    if (recognitionInterval) {
        clearInterval(recognitionInterval);
        recognitionInterval = null;
    }

    // **DỪNG HOÀN TOÀN - TẮT CAMERA VÀ RESET VỀ TRẠNG THÁI BAN ĐẦU**

    // Stop camera stream
    if (recognitionStream) {
        recognitionStream.getTracks().forEach(track => track.stop());
        recognitionStream = null;
    }

    // Hide video, show placeholder
    video.style.display = 'none';
    canvas.style.display = 'none';
    placeholder.style.display = 'flex';
    video.srcObject = null;

    // Update buttons - chỉ hiển thị nút "Bắt đầu nhận diện"
    startBtn.style.display = 'inline-flex';
    stopBtn.style.display = 'none';
    restartBtn.style.display = 'none';

    // Update status
    if (isAutoStop && studentName) {
        statusIndicator.className = 'status-indicator success';
        statusIndicator.innerHTML = '<i class="fas fa-check-circle"></i> Hoàn thành nhận diện';
        showStatus(`Nhận diện thành công cho ${studentName}. Bấm "Bắt đầu nhận diện" để tiếp tục.`, 'success');

        // Giữ thông tin sinh viên hiển thị
    } else {
        statusIndicator.className = 'status-indicator waiting';
        statusIndicator.innerHTML = '<i class="fas fa-clock"></i> Chờ nhận diện';
        showStatus('Đã dừng nhận diện khuôn mặt', 'info');

        // Clear student info cho manual stop
        const container = document.getElementById('student-info-display');
        container.innerHTML = `
            <div class="empty-message">
                <i class="fas fa-user-slash"></i>
                <p>Chưa có thông tin sinh viên</p>
                <small>Vui lòng bắt đầu nhận diện khuôn mặt</small>
            </div>
        `;
    }
}

function stopFaceRecognitionKeepImage(isAutoStop = false, studentName = '') {
    const video = document.getElementById('recognitionVideo');
    const canvas = document.getElementById('recognitionCanvas');
    const placeholder = document.getElementById('cameraPlaceholder');
    const startBtn = document.getElementById('startRecognitionBtn');
    const stopBtn = document.getElementById('stopRecognitionBtn');
    const restartBtn = document.getElementById('restartRecognitionBtn');
    const statusIndicator = document.querySelector('#recognitionStatus .status-indicator');

    isRecognizing = false;
    isProcessingRequest = false; // Reset flag khi dừng

    // Stop recognition interval
    if (recognitionInterval) {
        clearInterval(recognitionInterval);
        recognitionInterval = null;
    }

    // **DỪNG NHƯNG GIỮ ẢNH CUỐI CÙNG**

    // Stop camera stream
    if (recognitionStream) {
        recognitionStream.getTracks().forEach(track => track.stop());
        recognitionStream = null;
    }

    // Giữ video và canvas hiển thị (không ẩn)
    video.style.display = 'block';
    canvas.style.display = 'block';
    placeholder.style.display = 'none';
    video.srcObject = null;

    // Update buttons - hiển thị nút "Bắt đầu nhận diện" để có thể nhận diện tiếp
    startBtn.style.display = 'inline-flex';
    stopBtn.style.display = 'none';
    restartBtn.style.display = 'none';

    // Update status
    if (isAutoStop && studentName) {
        statusIndicator.className = 'status-indicator success';
        statusIndicator.innerHTML = '<i class="fas fa-check-circle"></i> Hoàn thành nhận diện';
        showStatus(`Nhận diện thành công cho ${studentName}. Ảnh đã được giữ lại.`, 'success');

        // Giữ thông tin sinh viên hiển thị
    } else {
        statusIndicator.className = 'status-indicator waiting';
        statusIndicator.innerHTML = '<i class="fas fa-clock"></i> Chờ nhận diện';
        showStatus('Đã dừng nhận diện khuôn mặt', 'info');
    }
}

function restartFaceRecognition() {
    // Bắt đầu lại từ đầu - giống như bấm "Bắt đầu nhận diện"
    startFaceRecognition();
}

async function searchByMSSV() {
    const input = document.getElementById('mssv-input');
    const studentCode = input.value.trim();

    if (!studentCode) {
        showStatus('Vui lòng nhập mã sinh viên', 'error');
        return;
    }

    try {
        // Search for student by code
        const response = await fetch(`${API_BASE_URL}/api/students?search=${studentCode}`, {
            credentials: 'include'
        });

        const result = await response.json();

        if (result.success && result.data && result.data.length > 0) {
            const student = result.data.find(s => s.student_code === studentCode);

            if (student) {
                // Display student info
                displayManualStudent(student);

                // Create access log
                const accessType = document.querySelector('input[name="accessType"]:checked').value;
                await createManualAccessLog(student.student_code, accessType);

                // Show success message
                showAccessSuccess(accessType, { name: student.full_name, student_code: student.student_code });

                // Clear input
                input.value = '';
            } else {
                showStatus('Không tìm thấy sinh viên với mã này', 'error');
            }
        } else {
            showStatus('Không tìm thấy sinh viên với mã này', 'error');
        }

    } catch (error) {
        console.error('Error searching student:', error);
        showStatus('Lỗi kết nối server', 'error');
    }
}

function displayManualStudent(student) {
    const container = document.getElementById('student-info-display');
    const statusIndicator = document.querySelector('#recognitionStatus .status-indicator');

    // Update status
    statusIndicator.className = 'status-indicator success';
    statusIndicator.innerHTML = '<i class="fas fa-check-circle"></i> Tìm thấy sinh viên';

    // Create student info card
    const studentCard = `
        <div class="student-info-card">
            <div class="student-info-header">
                <div class="student-avatar">
                    ${student.student_code.substring(0, 2)}
                </div>
                <div class="student-basic-info">
                    <h4>${student.full_name}</h4>
                    <div class="student-code">${student.student_code}</div>
                </div>
            </div>
            <div class="student-details">
                <div class="detail-item">
                    <i class="fas fa-home"></i>
                    <span>Phòng: ${student.room_number || 'Chưa có'}</span>
                </div>
                <div class="detail-item">
                    <i class="fas fa-graduation-cap"></i>
                    <span>Lớp: ${student.class_name || 'Chưa có'}</span>
                </div>
                <div class="detail-item">
                    <i class="fas fa-birthday-cake"></i>
                    <span>Sinh: ${student.birth_date || 'Chưa có'}</span>
                </div>
                <div class="detail-item">
                    <i class="fas fa-keyboard"></i>
                    <span>Nhập thủ công</span>
                </div>
            </div>
        </div>
    `;

    container.innerHTML = studentCard;
}

async function createManualAccessLog(studentCode, accessType) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/access-logs`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                student_code: studentCode,
                access_type: parseInt(accessType),
                gate_location: 'Cổng chính',
                verification_method: 'Nhập thủ công',
                notes: 'Nhập mã sinh viên thủ công'
            })
        });

        const result = await response.json();

        if (result.success) {
            console.log('Access log created successfully');

            // Reload access logs if we're on that section
            if (currentSection === 'access-logs') {
                loadAccessLogs();
            }

            // Reload dashboard stats
            loadStatistics();
        }

    } catch (error) {
        console.error('Error creating access log:', error);
    }
}

// Auto-stop recognition when switching sections
function showSection(sectionName) {
    // Stop face recognition when leaving checkin section
    if (currentSection === 'checkin' && sectionName !== 'checkin') {
        stopFaceRecognition();
    }

    // Hide all sections
    document.querySelectorAll('.dashboard-section').forEach(section => {
        section.style.display = 'none';
    });

    // Show selected section
    document.getElementById(`${sectionName}-section`).style.display = 'block';

    // Update active nav item
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[onclick="showSection('${sectionName}')"]`).classList.add('active');

    currentSection = sectionName;

    // Load section-specific data
    switch (sectionName) {
        case 'dashboard':
            loadStatistics();
            loadRecentActivity();
            break;
        case 'student':
            loadStudents();
            break;
        case 'access-logs':
            loadAccessLogs();
            break;
        case 'checkin':
            // Reset recognition status when entering checkin section
            const statusIndicator = document.querySelector('#recognitionStatus .status-indicator');
            if (statusIndicator) {
                statusIndicator.className = 'status-indicator waiting';
                statusIndicator.innerHTML = '<i class="fas fa-clock"></i> Chờ nhận diện';
            }
            break;
    }
}

// Training Functions
function openTrainingModal() {
    const trainingModal = document.getElementById('trainingModal');
    if (trainingModal) {
        trainingModal.style.display = 'flex';

        // Reset modal state
        const trainingStatus = document.getElementById('trainingStatus');
        const confirmBtn = document.getElementById('confirmTrainingBtn');
        const cancelBtn = document.getElementById('cancelTrainingBtn');

        if (trainingStatus) trainingStatus.style.display = 'none';
        if (confirmBtn) {
            confirmBtn.style.display = 'inline-flex';
            confirmBtn.disabled = false;
        }
        if (cancelBtn) cancelBtn.style.display = 'inline-flex';
    }
}

function closeTrainingModal() {
    const trainingModal = document.getElementById('trainingModal');
    if (trainingModal) {
        trainingModal.style.display = 'none';
    }
}

async function confirmTraining() {
    try {
        const trainingStatus = document.getElementById('trainingStatus');
        const trainingStatusText = document.getElementById('trainingStatusText');
        const confirmBtn = document.getElementById('confirmTrainingBtn');
        const cancelBtn = document.getElementById('cancelTrainingBtn');
        const trainingMenu = document.querySelector('.training-menu');

        // Show loading state
        if (trainingStatus) trainingStatus.style.display = 'block';
        if (confirmBtn) confirmBtn.style.display = 'none';
        if (cancelBtn) cancelBtn.style.display = 'none';
        if (trainingStatusText) trainingStatusText.textContent = 'Đang khởi tạo training...';

        // Disable training menu
        if (trainingMenu) {
            trainingMenu.style.opacity = '0.6';
            trainingMenu.style.pointerEvents = 'none';
        }

        // Call training API
        const response = await fetch(`${API_BASE_URL}/api/training`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include'
        });

        const result = await response.json();

        if (result.success) {
            if (trainingStatusText) {
                trainingStatusText.textContent = 'Training hoàn thành thành công!';
            }

            // Show success message
            showStatus('✅ Training hoàn thành thành công! Hệ thống đã cập nhật dữ liệu nhận diện khuôn mặt', 'success');

            // Close modal after 2 seconds
            setTimeout(() => {
                closeTrainingModal();
                // Reload page to refresh data
                window.location.reload();
            }, 2000);

        } else {
            if (trainingStatusText) {
                trainingStatusText.textContent = `Training thất bại: ${result.error || result.message}`;
            }

            showStatus(`❌ Training thất bại: ${result.error || result.message}`, 'error');

            // Show buttons again after 3 seconds
            setTimeout(() => {
                if (confirmBtn) confirmBtn.style.display = 'inline-flex';
                if (cancelBtn) cancelBtn.style.display = 'inline-flex';
                if (trainingStatus) trainingStatus.style.display = 'none';
            }, 3000);
        }

    } catch (error) {
        console.error('Error during training:', error);

        const trainingStatusText = document.getElementById('trainingStatusText');
        const confirmBtn = document.getElementById('confirmTrainingBtn');
        const cancelBtn = document.getElementById('cancelTrainingBtn');
        const trainingStatus = document.getElementById('trainingStatus');

        if (trainingStatusText) {
            trainingStatusText.textContent = 'Lỗi kết nối server';
        }

        showStatus('❌ Lỗi kết nối server trong quá trình training', 'error');

        // Show buttons again after 3 seconds
        setTimeout(() => {
            if (confirmBtn) confirmBtn.style.display = 'inline-flex';
            if (cancelBtn) cancelBtn.style.display = 'inline-flex';
            if (trainingStatus) trainingStatus.style.display = 'none';
        }, 3000);

    } finally {
        // Restore training menu
        const trainingMenu = document.querySelector('.training-menu');
        if (trainingMenu) {
            trainingMenu.style.opacity = '1';
            trainingMenu.style.pointerEvents = 'auto';
        }
    }
}
