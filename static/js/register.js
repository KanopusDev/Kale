/**
 * Register Page JavaScript for Kale Email API Platform
 * Production-ready registration functionality
 */

'use strict';

// Initialize register page
document.addEventListener('DOMContentLoaded', function() {
    // Ensure KaleAPI is loaded before proceeding
    if (typeof KaleAPI === 'undefined') {
        setTimeout(arguments.callee, 100);
        return;
    }
    
    initializeRegisterPage();
});

function initializeRegisterPage() {
    // Only redirect if we have a valid token AND user data
    const token = localStorage.getItem('auth_token');
    const user = localStorage.getItem('user');
    
    if (token && user) {
        try {
            // Verify token is valid
            const payload = JSON.parse(atob(token.split('.')[1]));
            const now = Math.floor(Date.now() / 1000);
            
            if (payload.exp > now) {
                window.location.href = '/dashboard';
                return;
            } else {
                // Token expired, clear storage
                localStorage.removeItem('auth_token');
                localStorage.removeItem('user');
            }
        } catch (error) {
            // Invalid token, clear storage
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user');
        }
    }
    
    // Initialize form handlers
    initializeRegisterForm();
    initializeUIElements();
}

function initializeRegisterForm() {
    const registerForm = document.getElementById('register-form');
    if (!registerForm) return;
    
    registerForm.addEventListener('submit', handleRegistration);
    
    // Real-time validation with proper error handling
    const firstNameField = registerForm.querySelector('#firstName');
    const lastNameField = registerForm.querySelector('#lastName');
    const usernameField = registerForm.querySelector('#username');
    const emailField = registerForm.querySelector('#email');
    const passwordField = registerForm.querySelector('#password');
    const confirmPasswordField = registerForm.querySelector('#confirmPassword');
    
    // First name validation
    if (firstNameField) {
        firstNameField.addEventListener('blur', function() { 
            validateRequiredField(this, 'First name is required'); 
        });
        firstNameField.addEventListener('input', function(e) { 
            clearFieldError(e); 
        });
    }
    
    // Last name validation
    if (lastNameField) {
        lastNameField.addEventListener('blur', function() { 
            validateRequiredField(this, 'Last name is required'); 
        });
        lastNameField.addEventListener('input', function(e) { 
            clearFieldError(e); 
        });
    }
    
    // Username validation
    if (usernameField) {
        usernameField.addEventListener('blur', validateUsername);
        usernameField.addEventListener('input', function(e) { 
            clearFieldError(e); 
        });
    }
    
    // Email validation
    if (emailField) {
        emailField.addEventListener('blur', validateEmail);
        emailField.addEventListener('input', function(e) { 
            clearFieldError(e); 
        });
    }
    
    // Password validation
    if (passwordField) {
        passwordField.addEventListener('input', validatePassword);
    }
    
    // Confirm password validation
    if (confirmPasswordField) {
        confirmPasswordField.addEventListener('input', validatePasswordConfirmation);
    }
}

function initializeUIElements() {
    // Password visibility toggles
    const passwordToggles = document.querySelectorAll('[data-password-toggle]');
    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const targetId = this.dataset.passwordToggle;
            const passwordField = document.getElementById(targetId);
            
            if (passwordField) {
                const type = passwordField.getAttribute('type') === 'password' ? 'text' : 'password';
                passwordField.setAttribute('type', type);
                
                // Update toggle icon
                const icon = this.querySelector('svg');
                if (icon) {
                    icon.style.transform = type === 'text' ? 'scale(0.9)' : 'scale(1)';
                }
            }
        });
    });
    
    // Clear any existing error messages
    clearErrorMessages();
}

async function handleRegistration(event) {
    event.preventDefault();
    
    const form = event.target;
    const submitButton = form.querySelector('button[type="submit"]');
    
    // Get form data
    const formData = new FormData(form);
    const firstName = formData.get('firstName')?.trim() || '';
    const lastName = formData.get('lastName')?.trim() || '';
    const username = formData.get('username')?.trim() || '';
    const email = formData.get('email')?.trim() || '';
    const password = formData.get('password') || '';
    const confirmPassword = formData.get('confirmPassword') || '';
    
    // Validate all fields
    if (!validateAllFields(firstName, lastName, username, email, password, confirmPassword)) {
        return;
    }
    
    // Show loading state
    KaleAPI.showLoading(submitButton);
    clearErrorMessages();
    
    try {
        // Prepare registration data
        const registrationData = {
            username: username,
            email: email,
            password: password
        };
        
        // Make registration request
        const response = await fetch('/api/v1/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(registrationData)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Registration failed');
        }
        
        // Show success message
        KaleAPI.showNotification('Registration successful! Please log in.', 'success');
        
        // Redirect to login page after a short delay
        setTimeout(() => {
            window.location.href = '/login';
        }, 2000);
        
    } catch (error) {
        showRegistrationError(error.message || 'Registration failed. Please try again.');
    } finally {
        KaleAPI.hideLoading(submitButton);
    }
}

function validateAllFields(firstName, lastName, username, email, password, confirmPassword) {
    let isValid = true;
    
    // Validate first name
    if (!firstName) {
        showFieldError('firstName', 'First name is required');
        isValid = false;
    }
    
    // Validate last name
    if (!lastName) {
        showFieldError('lastName', 'Last name is required');
        isValid = false;
    }
    
    // Validate username
    if (!username) {
        showFieldError('username', 'Username is required');
        isValid = false;
    } else if (!KaleAPI.validateUsername(username)) {
        showFieldError('username', 'Username must be 3-20 characters and contain only letters, numbers, and underscores');
        isValid = false;
    }
    
    // Validate email
    if (!email) {
        showFieldError('email', 'Email is required');
        isValid = false;
    } else if (!KaleAPI.validateEmail(email)) {
        showFieldError('email', 'Please enter a valid email address');
        isValid = false;
    }
    
    // Validate password
    if (!password) {
        showFieldError('password', 'Password is required');
        isValid = false;
    } else if (!KaleAPI.validatePassword(password)) {
        showFieldError('password', 'Password must be at least 12 characters with uppercase, lowercase, number, and special character');
        isValid = false;
    }
    
    // Validate password confirmation
    if (!confirmPassword) {
        showFieldError('confirmPassword', 'Please confirm your password');
        isValid = false;
    } else if (password !== confirmPassword) {
        showFieldError('confirmPassword', 'Passwords do not match');
        isValid = false;
    }
    
    return isValid;
}

function validateRequiredField(field, message) {
    const value = field.value.trim();
    
    if (!value) {
        showFieldError(field.id, message);
    } else {
        clearFieldError({ target: field });
    }
}

function validateUsername(event) {
    const username = event.target.value.trim();
    const field = event.target;
    
    if (username && !KaleAPI.validateUsername(username)) {
        showFieldError(field.id, 'Username must be 3-20 characters and contain only letters, numbers, and underscores');
    } else {
        clearFieldError(event);
    }
}

function validateEmail(event) {
    const email = event.target.value.trim();
    const field = event.target;
    
    if (email && !KaleAPI.validateEmail(email)) {
        showFieldError(field.id, 'Please enter a valid email address');
    } else {
        clearFieldError(event);
    }
}

function validatePassword(event) {
    const password = event.target.value;
    const field = event.target;
    
    if (password && !KaleAPI.validatePassword(password)) {
        showFieldError(field.id, 'Password must be at least 12 characters with uppercase, lowercase, number, and special character');
    } else {
        clearFieldError(event);
    }
    
    // Also validate confirmation if it exists
    const confirmField = document.getElementById('confirmPassword');
    if (confirmField && confirmField.value) {
        validatePasswordConfirmation({ target: confirmField });
    }
}

function validatePasswordConfirmation(event) {
    const confirmPassword = event.target.value;
    const password = document.getElementById('password').value;
    const field = event.target;
    
    if (confirmPassword && password !== confirmPassword) {
        showFieldError(field.id, 'Passwords do not match');
    } else {
        clearFieldError(event);
    }
}

function showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    if (!field) return;
    
    // Remove existing error
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
    
    // Add error styling to field
    field.classList.add('border-red-500', 'focus:border-red-500');
    field.classList.remove('border-gray-300', 'focus:border-indigo-500');
    
    // Create error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error text-red-600 text-sm mt-1';
    errorDiv.textContent = message;
    
    // Insert error message after the field
    field.parentNode.appendChild(errorDiv);
}

function clearFieldError(event) {
    const field = event.target;
    
    // Remove error styling
    field.classList.remove('border-red-500', 'focus:border-red-500');
    field.classList.add('border-gray-300', 'focus:border-indigo-500');
    
    // Remove error message
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
}

function showRegistrationError(message) {
    // Remove any existing error messages
    clearErrorMessages();
    
    // Create error message element
    const errorDiv = document.createElement('div');
    errorDiv.className = 'bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg text-sm';
    errorDiv.id = 'registration-error';
    errorDiv.textContent = message;
    
    // Insert error message before the form
    const form = document.getElementById('register-form');
    if (form) {
        form.parentNode.insertBefore(errorDiv, form);
    }
    
    // Auto-remove error after 10 seconds
    setTimeout(clearErrorMessages, 10000);
}

function clearErrorMessages() {
    const existingError = document.getElementById('registration-error');
    if (existingError) {
        existingError.remove();
    }
    
    // Also clear field errors
    const fieldErrors = document.querySelectorAll('.field-error');
    fieldErrors.forEach(error => error.remove());
}
