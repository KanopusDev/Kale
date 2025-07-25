/**
 * Main JavaScript for Kale Email API Platform
 * Production-ready core functionality and API communication
 */

'use strict';

// Global configuration
const API_BASE = '/api/v1';

// Global KaleAPI object for all pages
window.KaleAPI = {
    API_BASE: API_BASE,
    
    // Authentication methods
    checkAuthentication: function() {
        const token = localStorage.getItem('auth_token');
        if (!token) {
            return false;
        }
        
        try {
            // Validate token format
            const parts = token.split('.');
            if (parts.length !== 3) {
                throw new Error('Invalid token format');
            }
            
            const payload = JSON.parse(atob(parts[1]));
            const now = Math.floor(Date.now() / 1000);
            
            if (!payload.exp || payload.exp <= now) {
                throw new Error('Token expired');
            }
            
            return true;
        } catch (error) {
            this.clearAuthData();
            return false;
        }
    },
    
    logout: function() {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        localStorage.removeItem('refresh_token');
        sessionStorage.clear();
        window.location.href = '/login';
    },
    
    clearAuthData: function() {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        localStorage.removeItem('refresh_token');
    },
    
    getAuthHeaders: function() {
        const token = localStorage.getItem('auth_token');
        if (!token) {
            return {};
        }
        
        return {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    },
    
    // API request wrapper with error handling
    apiRequest: async function(endpoint, options = {}) {
        const url = endpoint.startsWith('http') ? endpoint : `${this.API_BASE}${endpoint}`;
        
        const defaultOptions = {
            method: 'GET',
            headers: this.getAuthHeaders(),
            ...options
        };
        
        // Merge headers properly
        if (options.headers) {
            defaultOptions.headers = { ...defaultOptions.headers, ...options.headers };
        }
        
        // Handle request body
        if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
            defaultOptions.body = JSON.stringify(options.body);
        } else if (options.body) {
            defaultOptions.body = options.body;
        }
        
        try {
            const response = await fetch(url, defaultOptions);
            
            // Handle different response types
            const contentType = response.headers.get('content-type');
            let data;
            
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else {
                data = await response.text();
            }
            
            if (!response.ok) {
                // Handle authentication errors
                if (response.status === 401) {
                    this.clearAuthData();
                    if (window.location.pathname !== '/login') {
                        window.location.href = '/login';
                    }
                    throw new Error('Authentication required');
                }
                
                // Handle validation errors (422)
                if (response.status === 422 && data) {
                    // FastAPI validation error format
                    if (data.detail && Array.isArray(data.detail)) {
                        const validationErrors = data.detail.map(err => {
                            if (err.loc && err.msg) {
                                const field = err.loc[err.loc.length - 1];
                                return `${field}: ${err.msg}`;
                            }
                            return err.msg || 'Validation error';
                        }).join(', ');
                        throw { detail: validationErrors, status: 422 };
                    } else if (data.detail) {
                        throw { detail: data.detail, status: 422 };
                    }
                }
                
                // Handle other HTTP errors - pass full error data for better handling
                const errorData = {
                    status: response.status,
                    statusText: response.statusText,
                    detail: data?.detail || data?.message || data,
                    response: data
                };
                
                throw errorData;
            }
            
            return data;
        } catch (error) {
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Network error - please check your connection');
            }
            throw error;
        }
    },
    
    // Notification system
    showNotification: function(message, type = 'info') {
        // Remove existing notifications
        const existingNotifications = document.querySelectorAll('.kale-notification');
        existingNotifications.forEach(notification => notification.remove());
        
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `kale-notification fixed top-4 right-4 z-50 max-w-sm p-4 rounded-lg shadow-lg transition-all duration-300 transform translate-x-full`;
        
        // Set notification style based on type
        switch (type) {
            case 'success':
                notification.classList.add('bg-green-500', 'text-white');
                break;
            case 'error':
                notification.classList.add('bg-red-500', 'text-white');
                break;
            case 'warning':
                notification.classList.add('bg-yellow-500', 'text-white');
                break;
            default:
                notification.classList.add('bg-blue-500', 'text-white');
        }
        
        // Set notification content
        notification.innerHTML = `
            <div class="flex items-center justify-between">
                <span class="font-medium">${message}</span>
                <button class="ml-4 text-white hover:text-gray-200" onclick="this.parentElement.parentElement.remove()">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        `;
        
        // Add to DOM
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    },
    
    // Utility functions
    formatDate: function(dateString) {
        if (!dateString) return 'N/A';
        
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            return 'Invalid Date';
        }
    },
    
    formatNumber: function(num) {
        if (num === null || num === undefined) return '0';
        
        if (typeof num !== 'number') {
            num = parseFloat(num);
            if (isNaN(num)) return '0';
        }
        
        return num.toLocaleString();
    },
    
    copyToClipboard: function(text, elementId = null) {
        if (elementId) {
            const element = document.getElementById(elementId);
            if (element) {
                text = element.textContent || element.value;
            }
        }
        
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text).then(() => {
                this.showNotification('Copied to clipboard!', 'success');
            }).catch(() => {
                this.fallbackCopyTextToClipboard(text);
            });
        } else {
            this.fallbackCopyTextToClipboard(text);
        }
    },
    
    fallbackCopyTextToClipboard: function(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            this.showNotification('Copied to clipboard!', 'success');
        } catch (error) {
            this.showNotification('Failed to copy to clipboard', 'error');
        }
        
        document.body.removeChild(textArea);
    },
    
    // Form validation utilities
    validateEmail: function(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },
    
    validatePassword: function(password) {
        // At least 8 characters, 1 uppercase, 1 lowercase, 1 number
        const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/;
        return passwordRegex.test(password);
    },
    
    validateUsername: function(username) {
        // 3-30 characters, alphanumeric and underscores only
        const usernameRegex = /^[a-zA-Z0-9_]{3,30}$/;
        return usernameRegex.test(username);
    },
    
    // UI utilities
    showLoading: function(element) {
        if (!element) return;
        
        const loader = document.createElement('div');
        loader.className = 'kale-loader fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        loader.innerHTML = `
            <div class="bg-white rounded-lg p-6 flex items-center space-x-3">
                <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                <span class="text-gray-700 font-medium">Loading...</span>
            </div>
        `;
        
        document.body.appendChild(loader);
    },
    
    hideLoading: function(element) {
        const loaders = document.querySelectorAll('.kale-loader');
        loaders.forEach(loader => loader.remove());
    },
    
    // Local storage utilities
    saveToStorage: function(key, data) {
        try {
            localStorage.setItem(key, JSON.stringify(data));
        } catch (error) {
            // Storage full or disabled
        }
    },
    
    getFromStorage: function(key) {
        try {
            const data = localStorage.getItem(key);
            return data ? JSON.parse(data) : null;
        } catch (error) {
            return null;
        }
    },
    
    // Form handling utilities
    getFormData: function(formElement) {
        const formData = new FormData(formElement);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        
        return data;
    },
    
    setFormData: function(formElement, data) {
        Object.entries(data).forEach(([key, value]) => {
            const field = formElement.querySelector(`[name="${key}"]`);
            if (field) {
                if (field.type === 'checkbox') {
                    field.checked = Boolean(value);
                } else {
                    field.value = value;
                }
            }
        });
    },
    
    // Debounce utility
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // API key validation
    validateApiKey: function(apiKey) {
        return apiKey && apiKey.length >= 32 && /^[a-zA-Z0-9]+$/.test(apiKey);
    },
    
    // Error handling
    handleApiError: function(error, context = '') {
        let message = 'An unexpected error occurred';
        
        console.error('API Error:', error, 'Context:', context);
        
        if (error && typeof error === 'object') {
            // Handle FastAPI validation errors (422)
            if (error.detail && Array.isArray(error.detail)) {
                const validationErrors = error.detail.map(err => {
                    if (err.loc && err.msg) {
                        const field = err.loc[err.loc.length - 1];
                        return `${field}: ${err.msg}`;
                    }
                    return err.msg || 'Validation error';
                }).join(', ');
                message = `Validation error: ${validationErrors}`;
            } else if (error.detail && typeof error.detail === 'string') {
                message = error.detail;
            } else if (error.message) {
                message = error.message;
            } else if (error.error) {
                message = error.error;
            } else if (error.status === 422) {
                message = 'Invalid data provided. Please check your input and try again.';
            } else {
                // Handle complex error objects by extracting useful information
                try {
                    if (error.response && error.response.data) {
                        message = JSON.stringify(error.response.data);
                    } else {
                        message = JSON.stringify(error);
                    }
                } catch {
                    message = 'Complex error - check console for details';
                }
            }
        } else if (typeof error === 'string') {
            message = error;
        }
        
        if (context) {
            message = `${context}: ${message}`;
        }
        
        this.showNotification(message, 'error');
        return message;
    },
    
    // Template utilities
    interpolateTemplate: function(template, variables) {
        return template.replace(/\{\{(\w+)\}\}/g, (match, key) => {
            return variables[key] || match;
        });
    },
    
    // URL utilities
    getCurrentDomain: function() {
        // For production, use the canonical domain
        // This checks if we're running in a development environment
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            // In development, check if we should use production domain for API endpoints
            // This allows testing against production domain while developing locally
            return 'https://kale.kanopus.org';
        }
        return window.location.origin;
    },
    
    buildApiUrl: function(username, templateId) {
        return `${this.getCurrentDomain()}/${username}/${templateId}`;
    }
};

// Legacy functions for backward compatibility
function getAuthHeaders() {
    return KaleAPI.getAuthHeaders();
}

function showNotification(message, type = 'info') {
    return KaleAPI.showNotification(message, type);
}

function formatDate(dateString) {
    return KaleAPI.formatDate(dateString);
}

function copyToClipboard(text, elementId = null) {
    return KaleAPI.copyToClipboard(text, elementId);
}

function logout() {
    return KaleAPI.logout();
}

// Initialize global event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Global copy button functionality
    document.addEventListener('click', function(e) {
        if (e.target.matches('[data-action="copy"], [data-action="copy"] *')) {
            const button = e.target.closest('[data-action="copy"]');
            if (button) {
                const copyTarget = button.dataset.copyTarget;
                const copyText = button.dataset.copyText;
                
                if (copyTarget) {
                    KaleAPI.copyToClipboard('', copyTarget);
                } else if (copyText) {
                    KaleAPI.copyToClipboard(copyText);
                }
            }
        }
    });
    
    // Global logout functionality
    document.addEventListener('click', function(e) {
        if (e.target.matches('[data-action="logout"], [data-action="logout"] *')) {
            e.preventDefault();
            KaleAPI.logout();
        }
    });
    
    // Enhanced form validation
    document.addEventListener('input', function(e) {
        if (e.target.matches('input[type="email"]')) {
            validateEmailField(e.target);
        } else if (e.target.matches('#smtp-password, input[name="password"][id="smtp-password"], input.smtp-password')) {
            // SMTP password fields should only check for presence, not complexity
            validateSMTPPasswordField(e.target);
        } else if (e.target.matches('input[type="password"]') && !e.target.matches('#smtp-password, input[name="password"][id="smtp-password"], input.smtp-password')) {
            validatePasswordField(e.target);
        }
    });
    
    // API key format validation
    document.addEventListener('input', function(e) {
        if (e.target.matches('input[data-type="api-key"]')) {
            validateApiKeyField(e.target);
        }
    });
});

// Field validation functions
function validateEmailField(field) {
    const isValid = KaleAPI.validateEmail(field.value);
    updateFieldValidation(field, isValid, 'Please enter a valid email address');
}

function validatePasswordField(field) {
    const isValid = KaleAPI.validatePassword(field.value);
    updateFieldValidation(field, isValid, 'Password must be at least 8 characters with uppercase, lowercase, and number');
}

function validateSMTPPasswordField(field) {
    // SMTP passwords should NOT be subject to complexity requirements
    // They are external service credentials that users cannot change
    const isValid = true; // Always valid - no password complexity requirements for SMTP
    
    // Only show error if the field is empty and required
    if (field.hasAttribute('required') && field.value.trim().length === 0) {
        updateFieldValidation(field, false, 'SMTP password is required');
    } else {
        updateFieldValidation(field, true, '');
    }
}

function validateApiKeyField(field) {
    const isValid = KaleAPI.validateApiKey(field.value);
    updateFieldValidation(field, isValid, 'Invalid API key format');
}

function updateFieldValidation(field, isValid, errorMessage) {
    const errorElement = field.parentElement.querySelector('.validation-error');
    
    if (isValid) {
        field.classList.remove('border-red-500');
        field.classList.add('border-green-500');
        if (errorElement) {
            errorElement.remove();
        }
    } else if (field.value) {
        field.classList.remove('border-green-500');
        field.classList.add('border-red-500');
        
        if (!errorElement) {
            const error = document.createElement('div');
            error.className = 'validation-error text-red-500 text-xs mt-1';
            error.textContent = errorMessage;
            field.parentElement.appendChild(error);
        }
    } else {
        field.classList.remove('border-red-500', 'border-green-500');
        if (errorElement) {
            errorElement.remove();
        }
    }
}

// Performance monitoring
window.addEventListener('load', function() {
    // Track page load performance
    if ('performance' in window) {
        const loadTime = window.performance.timing.loadEventEnd - window.performance.timing.navigationStart;
        if (loadTime > 3000) {
            // Page took more than 3 seconds to load
        }
    }
});

// Error tracking
window.addEventListener('error', function(e) {
    // Track JavaScript errors for monitoring
    const errorInfo = {
        message: e.message,
        filename: e.filename,
        lineno: e.lineno,
        colno: e.colno,
        timestamp: new Date().toISOString()
    };
    
    // In production, you might want to send this to an error tracking service
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = KaleAPI;
}
