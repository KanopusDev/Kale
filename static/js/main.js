/* Main JavaScript for Kale Email API Platform */

// Global configuration
const API_BASE = '/api/v1';

// Global KaleAPI object for all pages
window.KaleAPI = {
    // Configuration
    API_BASE: API_BASE,
    
    // Authentication
    checkAuthentication: function() {
        const token = localStorage.getItem('token');
        const user = localStorage.getItem('user');
        
        if (!token || !user) {
            window.location.href = '/';
            return false;
        }
        
        return true;
    },
    
    logout: function() {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        this.showNotification('Logged out successfully', 'success');
        setTimeout(() => {
            window.location.href = '/';
        }, 1000);
    },
    
    // API helpers
    getAuthHeaders: function() {
        const token = localStorage.getItem('token');
        return {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    },
    
    apiRequest: async function(endpoint, options = {}) {
        const url = `${this.API_BASE}${endpoint}`;
        const config = {
            headers: this.getAuthHeaders(),
            ...options
        };
        
        try {
            const response = await fetch(url, config);
            
            // Handle 401 errors by redirecting to login
            if (response.status === 401) {
                this.logout();
                return;
            }
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'Request failed');
            }
            
            return data;
        } catch (error) {
            console.error('API Request Error:', error);
            throw error;
        }
    },
    
    // Utility functions
    showNotification: function(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transition-all duration-300 ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            type === 'warning' ? 'bg-yellow-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.classList.add('opacity-0', 'translate-x-full');
            setTimeout(() => {
                if (notification.parentNode) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 5000);
    },
    
    formatDate: function(dateString) {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    
    formatNumber: function(num) {
        return new Intl.NumberFormat().format(num);
    },
    
    copyToClipboard: function(text) {
        navigator.clipboard.writeText(text).then(() => {
            this.showNotification('Copied to clipboard!', 'success');
        }).catch(() => {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            this.showNotification('Copied to clipboard!', 'success');
        });
    },
    
    // Form validation
    validateEmail: function(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },
    
    validatePassword: function(password) {
        return password.length >= 8;
    },
    
    validateUsername: function(username) {
        const usernameRegex = /^[a-zA-Z0-9_-]+$/;
        return usernameRegex.test(username) && username.length >= 3 && username.length <= 50;
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

function formatNumber(num) {
    return KaleAPI.formatNumber(num);
}

function checkAuthentication() {
    return KaleAPI.checkAuthentication();
}

function logout() {
    return KaleAPI.logout();
}

async function apiRequest(endpoint, options = {}) {
    return await KaleAPI.apiRequest(endpoint, options);
}

function validateEmail(email) {
    return KaleAPI.validateEmail(email);
}

function validatePassword(password) {
    return KaleAPI.validatePassword(password);
}

function validateUsername(username) {
    return KaleAPI.validateUsername(username);
}

function copyToClipboard(text) {
    return KaleAPI.copyToClipboard(text);
}

// Loading states
function showLoading(element) {
    if (element) {
        element.disabled = true;
        element.innerHTML = `
            <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Loading...
        `;
    }
}

function hideLoading(element, originalText) {
    if (element) {
        element.disabled = false;
        element.innerHTML = originalText;
    }
}

// Local storage helpers
function saveToStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
    } catch (error) {
        console.error('Storage save error:', error);
    }
}

function getFromStorage(key) {
    try {
        const data = localStorage.getItem(key);
        return data ? JSON.parse(data) : null;
    } catch (error) {
        console.error('Storage read error:', error);
        return null;
    }
}

// Theme management
function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
}

function getTheme() {
    return localStorage.getItem('theme') || 'light';
}

// Copy to clipboard
function copyToClipboard(text) {
    return KaleAPI.copyToClipboard(text);
}

// Initialize common functionality
document.addEventListener('DOMContentLoaded', function() {
    // Set theme
    setTheme(getTheme());
    
    // Add click handlers for copy buttons
    document.querySelectorAll('[data-copy]').forEach(button => {
        button.addEventListener('click', function() {
            const text = this.dataset.copy;
            copyToClipboard(text);
        });
    });
    
    // Handle form submissions
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton && !submitButton.dataset.noLoading) {
                showLoading(submitButton);
            }
        });
    });
});
// Export for use in other scripts
window.KaleAPI = {
    apiRequest,
    showNotification,
    formatDate,
    formatNumber,
    checkAuthentication,
    logout,
    validateEmail,
    validatePassword,
    validateUsername,
    showLoading,
    hideLoading,
    saveToStorage,
    getFromStorage,
    copyToClipboard
};
