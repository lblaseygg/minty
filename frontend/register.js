document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.getElementById('register-form');
    const errorMessage = document.getElementById('error-message');
    const successMessage = document.getElementById('success-message');

    registerForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Clear previous messages
        clearMessages();
        
        // Get form data
        const username = document.getElementById('username').value.trim();
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm-password').value;
        
        // Validate form data
        if (!validateForm(username, email, password, confirmPassword)) {
            return;
        }
        
        // Show loading state
        const submitButton = registerForm.querySelector('button[type="submit"]');
        const originalText = submitButton.textContent;
        submitButton.textContent = 'Creating Account...';
        submitButton.disabled = true;
        
        try {
            // Send registration request
            const response = await fetch('http://localhost:5001/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: username,
                    email: email,
                    password: password
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Registration successful
                showMessage('Account created successfully! Redirecting to login...', 'success');
                
                // Redirect to login page after a short delay
                setTimeout(() => {
                    window.location.href = 'login.html';
                }, 2000);
                
            } else {
                // Registration failed
                showMessage(data.error || 'Registration failed. Please try again.', 'error');
            }
            
        } catch (error) {
            console.error('Registration error:', error);
            showMessage('Network error. Please check your connection and try again.', 'error');
        } finally {
            // Reset button state
            submitButton.textContent = originalText;
            submitButton.disabled = false;
        }
    });
    
    function validateForm(username, email, password, confirmPassword) {
        // Username validation
        if (username.length < 3) {
            showMessage('Username must be at least 3 characters long.', 'error');
            return false;
        }
        
        if (username.length > 50) {
            showMessage('Username must be less than 50 characters.', 'error');
            return false;
        }
        
        // Email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            showMessage('Please enter a valid email address.', 'error');
            return false;
        }
        
        // Password validation
        if (password.length < 6) {
            showMessage('Password must be at least 6 characters long.', 'error');
            return false;
        }
        
        // Password confirmation
        if (password !== confirmPassword) {
            showMessage('Passwords do not match.', 'error');
            return false;
        }
        
        // Password strength (optional)
        const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/;
        if (!passwordRegex.test(password)) {
            showMessage('Password should contain at least one uppercase letter, one lowercase letter, and one number.', 'error');
            return false;
        }
        
        return true;
    }
    
    function showMessage(message, type) {
        const messageElement = type === 'error' ? errorMessage : successMessage;
        messageElement.textContent = message;
        messageElement.classList.add('show');
        
        // Auto-hide success messages after 5 seconds
        if (type === 'success') {
            setTimeout(() => {
                messageElement.classList.remove('show');
            }, 5000);
        }
    }
    
    function clearMessages() {
        errorMessage.classList.remove('show');
        successMessage.classList.remove('show');
    }
    
    // Real-time password confirmation validation
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm-password');
    
    function validatePasswordMatch() {
        const password = passwordInput.value;
        const confirmPassword = confirmPasswordInput.value;
        
        if (confirmPassword && password !== confirmPassword) {
            confirmPasswordInput.setCustomValidity('Passwords do not match');
        } else {
            confirmPasswordInput.setCustomValidity('');
        }
    }
    
    passwordInput.addEventListener('input', validatePasswordMatch);
    confirmPasswordInput.addEventListener('input', validatePasswordMatch);
    
    // Username availability check (optional - you can implement this later)
    const usernameInput = document.getElementById('username');
    let usernameTimeout;
    
    usernameInput.addEventListener('input', function() {
        clearTimeout(usernameTimeout);
        const username = this.value.trim();
        
        if (username.length >= 3) {
            usernameTimeout = setTimeout(async () => {
                try {
                    // You can implement a username availability endpoint
                    // const response = await fetch(`http://localhost:5001/auth/check-username?username=${username}`);
                    // const data = await response.json();
                    // if (!data.available) {
                    //     this.setCustomValidity('Username is already taken');
                    // } else {
                    //     this.setCustomValidity('');
                    // }
                } catch (error) {
                    console.error('Username check error:', error);
                }
            }, 500);
        }
    });
}); 