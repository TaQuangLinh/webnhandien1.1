window.addEventListener('DOMContentLoaded', function () {
    const particlesContainer = document.querySelector('.particles');
    const particleCount = 15;

    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.classList.add('particle');

        // Random position
        const posX = Math.random() * 100;
        const posY = Math.random() * 100;

        // Random size
        const size = Math.random() * 6 + 2;

        // Random animation delay
        const delay = Math.random() * 10;

        particle.style.left = posX + '%';
        particle.style.top = posY + '%';
        particle.style.width = size + 'px';
        particle.style.height = size + 'px';
        particle.style.animationDelay = delay + 's';
        particle.style.opacity = Math.random() * 0.5 + 0.3;

        particlesContainer.appendChild(particle);
    }
});

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('adminLoginForm');
    const successMessage = document.getElementById('successMessage');
    const errorMessage = document.getElementById('errorMessage');
    const forgotPasswordLink = document.getElementById('forgotPasswordLink');
    const togglePassword = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('password');

    // Kiểm tra kết nối API khi trang load
    checkAPIConnection();

    // Kiểm tra nếu đã đăng nhập
    checkExistingLogin();

    // Toggle password visibility
    togglePassword.addEventListener('click', function () {
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);

        // Change icon
        this.classList.toggle('fa-eye');
        this.classList.toggle('fa-eye-slash');
    });

    // Quên mật khẩu event
    forgotPasswordLink.addEventListener('click', function (e) {
        e.preventDefault();
        errorMessage.innerHTML = '<i class="fas fa-info-circle"></i> Vui lòng liên hệ quản trị viên hệ thống để lấy lại mật khẩu.';
        errorMessage.style.display = 'block';
        errorMessage.style.backgroundColor = '#e3f2fd';
        errorMessage.style.color = '#FF0000';
        errorMessage.style.borderLeftColor = '#FF0000';

        // Hide after 3 seconds
        setTimeout(function () {
            errorMessage.style.display = 'none';
            errorMessage.style.backgroundColor = '#fee';
            errorMessage.style.color = '#e74c3c';
            errorMessage.style.borderLeftColor = '#e74c3c';
            errorMessage.innerHTML = '<i class="fas fa-exclamation-circle"></i> Tên đăng nhập hoặc mật khẩu không chính xác!';
        }, 3000);
    });

    // Form submission
    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        // Form validation
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value.trim();

        if (!username || !password) {
            showError('Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu');
            return;
        }

        // Button loading state
        const submitButton = document.querySelector('.login-button');
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang xử lý...';
        submitButton.disabled = true;

        try {
            // Call API đăng nhập từ cùng server (relative URL)
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include', // Quan trọng: để nhận session cookies
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            });

            const data = await response.json();

            // Debug: Log toàn bộ response
            console.log('🔍 Login response:', data);

            if (data.success) {
                // Vẫn lưu token vào localStorage để backup (tùy chọn)
                if (data.data && data.data.token) {
                    localStorage.setItem('dormitory_token', data.data.token);
                    localStorage.setItem('dormitory_user', JSON.stringify(data.data.user));
                    console.log('✅ Token saved to localStorage');
                }

                // Success case
                errorMessage.style.display = 'none';
                successMessage.innerHTML = `
                    <i class="fas fa-check-circle"></i> Đăng nhập thành công! Đang chuyển hướng...
                    <br><small><a href="javascript:void(0)" onclick="window.location.replace('/index.html')" style="color: #007bff; text-decoration: underline;">Nhấn vào đây nếu không tự động chuyển</a></small>
                `;
                successMessage.style.display = 'block';

                // Debug: Log redirect URL
                const redirectUrl = (data.data && data.data.redirect_url) ? data.data.redirect_url : '/index.html';
                console.log('🔄 Redirecting to:', redirectUrl);

                // Redirect after 2 seconds - tăng thời gian để đảm bảo session được lưu
                setTimeout(function () {
                    console.log('🚀 Executing redirect...');
                    // Sử dụng replace để đảm bảo redirect và không lưu history
                    window.location.replace(redirectUrl);
                }, 2000);
            } else {
                // Error case
                console.log('❌ Login failed:', data.message);
                showError(data.message || 'Đăng nhập thất bại');
                resetButton(submitButton);
            }
        } catch (error) {
            console.error('Lỗi kết nối API:', error);
            showError('Không thể kết nối đến server. Vui lòng kiểm tra lại.');
            resetButton(submitButton);
        }
    });

    // Helper functions
    function showError(message) {
        errorMessage.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
        errorMessage.style.display = 'block';

        // Add shake animation to form
        form.classList.add('shake');
        setTimeout(() => form.classList.remove('shake'), 300);

        // Hide error after 5 seconds
        setTimeout(function () {
            errorMessage.style.display = 'none';
        }, 5000);
    }

    function resetButton(button) {
        button.innerHTML = 'Đăng nhập';
        button.disabled = false;
    }

    // Animation for input focus
    const inputs = document.querySelectorAll('input');
    inputs.forEach(input => {
        input.addEventListener('focus', function () {
            this.parentElement.querySelector('label').style.color = '#3a7bd5';
        });
    });

    // API Connection Check
    async function checkAPIConnection() {
        try {
            const response = await fetch('/api/test');
            const data = await response.json();

            if (data.success) {
                console.log('✅ API Connection: OK');
                showConnectionStatus('API đã sẵn sàng', 'success');
            } else {
                console.log('❌ API Connection: Failed');
                showConnectionStatus('API không phản hồi', 'error');
            }
        } catch (error) {
            console.log('❌ API Connection Error:', error);
            showConnectionStatus('Không thể kết nối API server', 'error');
        }
    }

    // Check existing login using session
    async function checkExistingLogin() {
        try {
            const response = await fetch('/api/check-session', {
                method: 'GET',
                credentials: 'include' // Quan trọng: để gửi session cookies
            });

            const data = await response.json();

            if (data.success && data.logged_in) {
                console.log('✅ Session still valid, redirecting...');
                showInfo('Bạn đã đăng nhập, đang chuyển hướng...');
                setTimeout(() => {
                    window.location.href = '/index.html';
                }, 1000);
            } else {
                console.log('❌ No valid session found');
                // Xóa localStorage cũ nếu có
                localStorage.removeItem('dormitory_token');
                localStorage.removeItem('dormitory_user');
            }
        } catch (error) {
            console.log('❌ Session check failed:', error);
            // Xóa localStorage cũ nếu có
            localStorage.removeItem('dormitory_token');
            localStorage.removeItem('dormitory_user');
        }
    }

    // Show connection status
    function showConnectionStatus(message, type) {
        const statusDiv = document.createElement('div');
        statusDiv.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            padding: 10px 15px;
            border-radius: 5px;
            color: white;
            font-size: 14px;
            z-index: 1000;
            background-color: ${type === 'success' ? '#28a745' : '#dc3545'};
        `;
        statusDiv.innerHTML = `<i class="fas fa-${type === 'success' ? 'check' : 'exclamation-triangle'}"></i> ${message}`;

        document.body.appendChild(statusDiv);

        setTimeout(() => {
            statusDiv.remove();
        }, 3000);
    }

    // Show info message
    function showInfo(message) {
        successMessage.innerHTML = `<i class="fas fa-info-circle"></i> ${message}`;
        successMessage.style.display = 'block';
    }
});

// Add shake animation and additional styles
document.head.insertAdjacentHTML('beforeend', `
    <style>
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
            20%, 40%, 60%, 80% { transform: translateX(5px); }
        }
        .shake {
            animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both;
        }

        /* Debug info styles */
        .debug-info {
            position: fixed;
            bottom: 10px;
            left: 10px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 12px;
            z-index: 1000;
        }

        /* Particles effect */
        .particles {
            position: absolute;
            width: 100%;
            height: 100%;
            z-index: 0;
            top: 0;
            left: 0;
        }

        .particle {
            position: absolute;
            width: 8px;
            height: 8px;
            background-color: rgba(255, 255, 255, 0.5);
            border-radius: 50%;
            animation: moveParticle 15s infinite linear;
        }

        @keyframes moveParticle {
            0% {
                transform: translate(0, 0);
                opacity: 0;
            }

            10% {
                opacity: 1;
            }

            90% {
                opacity: 1;
            }

            100% {
                transform: translate(100px, -100px);
                opacity: 0;
            }
        }
    </style>
`);



// Update API status
setTimeout(async () => {
    try {
        const response = await fetch('/api/test');
        const data = await response.json();
        document.getElementById('api-status').innerHTML =
            data.success ? 'API Status: ✅ Online' : 'API Status: ❌ Error';
    } catch (error) {
        document.getElementById('api-status').innerHTML = 'API Status: ❌ Offline';
    }
}, 1000);
