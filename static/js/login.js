/**
 * Login JavaScript for Kale Email API Platform
 * Production-ready authentication functionality
 */

'use strict';

// Initialize login page
document.addEventListener('DOMContentLoaded', function() {
    // Ensure KaleAPI is loaded before proceeding
    if (typeof KaleAPI === 'undefined') {
        setTimeout(arguments.callee, 100);
        return;
    }
    
    // Only redirect if we have a valid token AND user data
    const token = localStorage.getItem('auth_token');
    const user = localStorage.getItem('user');
    
    // Prevent redirect loops by checking if we're already on login page
    if (token && user && window.location.pathname === '/login') {
        try {
            // Verify token is valid
            const payload = JSON.parse(atob(token.split('.')[1]));
            const now = Math.floor(Date.now() / 1000);
            
            if (payload.exp > now) {
                // Valid token exists, redirect to dashboard
                window.location.href = '/dashboard';
                return;
            } else {
                // Token expired, clear storage and stay on login page
                localStorage.removeItem('auth_token');
                localStorage.removeItem('user');
                localStorage.removeItem('refresh_token');
            }
        } catch (error) {
            // Invalid token, clear storage and stay on login page
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user');
            localStorage.removeItem('refresh_token');
        }
    }
    
    initializeLoginPage();
});

// Fallback function for form data extraction
function getFormDataFallback(formElement) {
    const formData = new FormData(formElement);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    return data;
}

// Main initialization function
function initializeLoginPage() {
    setupEventListeners();
    setupFormValidation();
    handleUrlParams();
}

// Set up event listeners
function setupEventListeners() {
    // Form submissions
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // Toggle password visibility
    const toggleButtons = document.querySelectorAll('[data-action="toggle-password"]');
    toggleButtons.forEach(button => {
        button.addEventListener('click', togglePasswordVisibility);
    });
    
    // Remember me functionality
    const rememberMeCheckbox = document.getElementById('remember-me');
    if (rememberMeCheckbox) {
        // Load saved email if remember me was checked
        const savedEmail = localStorage.getItem('remembered_email');
        if (savedEmail) {
            const emailField = document.getElementById('email');
            if (emailField) {
                emailField.value = savedEmail;
                rememberMeCheckbox.checked = true;
            }
        }
    }
}

// Set up form validation
function setupFormValidation() {
    // Real-time email validation
    const emailField = document.getElementById('email');
    if (emailField) {
        emailField.addEventListener('blur', function() {
            validateEmailField(this);
        });
        
        emailField.addEventListener('input', function() {
            clearFieldError(this);
        });
    }
    
    // Real-time password validation
    const passwordField = document.getElementById('password');
    if (passwordField) {
        passwordField.addEventListener('input', function() {
            clearFieldError(this);
        });
    }
}

// Handle URL parameters
function handleUrlParams() {
    const urlParams = new URLSearchParams(window.location.search);
    const redirectUrl = urlParams.get('redirect');
    const error = urlParams.get('error');
    
    if (error) {
        let errorMessage = 'Login failed';
        switch (error) {
            case 'expired':
                errorMessage = 'Your session has expired. Please log in again.';
                break;
            case 'unauthorized':
                errorMessage = 'You need to log in to access this page.';
                break;
            case 'invalid':
                errorMessage = 'Invalid credentials. Please try again.';
                break;
        }
        KaleAPI.showNotification(errorMessage, 'error');
    }
    
    // Store redirect URL for after login
    if (redirectUrl) {
        sessionStorage.setItem('login_redirect', redirectUrl);
    }
}

// Handle login form submission
async function handleLogin(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitButton = form.querySelector('button[type="submit"]');
    const originalButtonText = submitButton.textContent;
    
    try {
        // Disable submit button and show loading
        submitButton.disabled = true;
        submitButton.innerHTML = `
            <div class="flex items-center justify-center">
                <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Signing in...
            </div>
        `;
        
        // Get form data
        const formData = KaleAPI && KaleAPI.getFormData ? 
            KaleAPI.getFormData(form) : 
            getFormDataFallback(form);
        
        // Validate form
        if (!validateLoginForm(formData)) {
            return;
        }
        
        // Submit login request
        const response = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: formData.email,
                password: formData.password
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Login failed');
        }
        
        // Store authentication data
        localStorage.setItem('auth_token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        
        // Handle remember me
        const rememberMe = document.getElementById('remember-me');
        if (rememberMe && rememberMe.checked) {
            localStorage.setItem('remembered_email', formData.email);
        } else {
            localStorage.removeItem('remembered_email');
        }
        
        // Show success message
        KaleAPI.showNotification('Login successful! Redirecting...', 'success');
        
        // Redirect to appropriate page
        setTimeout(() => {
            const redirectUrl = sessionStorage.getItem('login_redirect');
            sessionStorage.removeItem('login_redirect');
            
            if (redirectUrl && redirectUrl !== '/login') {
                window.location.href = redirectUrl;
            } else if (data.user.is_admin) {
                window.location.href = '/admin';
            } else {
                window.location.href = '/dashboard';
            }
        }, 1000);
        
    } catch (error) {
        KaleAPI.showNotification(error.message, 'error');
        
        // Focus on password field for retry
        const passwordField = document.getElementById('password');
        if (passwordField) {
            passwordField.focus();
            passwordField.select();
        }
        
    } finally {
        // Re-enable submit button
        submitButton.disabled = false;
        submitButton.textContent = originalButtonText;
    }
}

// Validate login form
function validateLoginForm(formData) {
    let isValid = true;
    
    // Validate email
    const emailField = document.getElementById('email');
    if (!formData.email) {
        showFieldError(emailField, 'Email is required');
        isValid = false;
    } else if (!KaleAPI.validateEmail(formData.email)) {
        showFieldError(emailField, 'Please enter a valid email address');
        isValid = false;
    }
    
    // Validate password
    const passwordField = document.getElementById('password');
    if (!formData.password) {
        showFieldError(passwordField, 'Password is required');
        isValid = false;
    } else if (formData.password.length < 6) {
        showFieldError(passwordField, 'Password must be at least 6 characters');
        isValid = false;
    }
    
    return isValid;
}

// Field validation helper functions
function validateEmailField(field) {
    const isValid = field.value && KaleAPI.validateEmail(field.value);
    if (!isValid && field.value) {
        showFieldError(field, 'Please enter a valid email address');
    } else {
        clearFieldError(field);
    }
    return isValid;
}

function showFieldError(field, message) {
    clearFieldError(field);
    
    field.classList.add('border-red-500');
    
    const errorElement = document.createElement('div');
    errorElement.className = 'field-error text-red-500 text-xs mt-1';
    errorElement.textContent = message;
    
    field.parentElement.appendChild(errorElement);
}

function clearFieldError(field) {
    field.classList.remove('border-red-500');
    
    const existingError = field.parentElement.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
}

// Toggle password visibility
function togglePasswordVisibility(e) {
    e.preventDefault();
    
    const button = e.target.closest('[data-action="toggle-password"]');
    const targetId = button.dataset.target;
    const passwordField = document.getElementById(targetId);
    
    if (!passwordField) return;
    
    const isPassword = passwordField.type === 'password';
    passwordField.type = isPassword ? 'text' : 'password';
    
    // Update button icon/text
    const icon = button.querySelector('svg') || button;
    if (isPassword) {
        // Show "hide" icon
        icon.innerHTML = `
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L8.464 8.464m1.414 1.414l-1.414-1.414m4.242 4.242l1.414 1.414m-1.414-1.414l1.414 1.414"/>
        `;
        button.title = 'Hide password';
    } else {
        // Show "show" icon  
        icon.innerHTML = `
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
        `;
        button.title = 'Show password';
    }
}

// Auto-fill demo credentials for development
function fillDemoCredentials() {
    const emailField = document.getElementById('email');
    const passwordField = document.getElementById('password');
    
    if (emailField && passwordField) {
        emailField.value = 'demo@example.com';
        passwordField.value = 'demo123';
        
        KaleAPI.showNotification('Demo credentials filled', 'info');
    }
}

// Handle OAuth login (if implemented)
function handleOAuthLogin(provider) {
    KaleAPI.showNotification(`${provider} login coming soon`, 'info');
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Submit form on Ctrl+Enter
    if (e.ctrlKey && e.key === 'Enter') {
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.dispatchEvent(new Event('submit'));
        }
    }
});

// Export functions for testing/external use
window.LoginPage = {
    handleLogin,
    validateLoginForm,
    fillDemoCredentials,
    handleOAuthLogin
};
