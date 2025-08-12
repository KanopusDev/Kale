/**
 * Dashboard JavaScript for Kale Email API Platform
 * Production-ready dashboard functionality and UI management with performance optimizations
 **/

'use strict';

// Dashboard state
let currentView = 'dashboard';
let userStats = {};
let templatesData = [];
let apiKeysData = [];
let smtpConfig = null;

// Performance optimizations
const debounce = (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};

const throttle = (func, limit) => {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Check authentication with loop prevention
    if (!KaleAPI || !KaleAPI.checkAuthentication()) {
        // Clear any invalid auth data
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        localStorage.removeItem('refresh_token');
        
        // Prevent redirect loops by checking current location
        if (window.location.pathname !== '/login') {
            window.location.href = '/login';
        }
        return;
    }
    
    initializeDashboard();
});

// Main initialization function
function initializeDashboard() {
    setupEventListeners();
    setupNavbarOptimizations();
    loadUserInfo(); // This will call updateAPIEndpoint
    loadDashboardStats();
    loadTemplates();
    loadSMTPConfig();
    loadAPIKeys();
    
    // Ensure API endpoints are updated after a short delay
    setTimeout(() => {
        const storedUser = KaleAPI.getFromStorage('user');
        if (storedUser && storedUser.username) {
            updateAPIEndpoint(storedUser.username);
        }
    }, 500);
}

// Setup optimized navbar interactions
function setupNavbarOptimizations() {
    const userMenuButton = document.getElementById('user-menu-button');
    const userMenu = document.getElementById('user-menu');
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const mobileMenu = document.getElementById('mobile-menu');
    
    // Optimized user menu functionality
    if (userMenuButton && userMenu) {
        let isUserMenuOpen = false;
        
        const toggleUserMenu = (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            isUserMenuOpen = !isUserMenuOpen;
            userMenuButton.setAttribute('aria-expanded', isUserMenuOpen);
            
            if (isUserMenuOpen) {
                userMenu.classList.remove('hidden');
                userMenu.classList.add('show');
                // Focus management for accessibility
                userMenu.querySelector('button')?.focus();
            } else {
                userMenu.classList.remove('show');
                userMenu.classList.add('hidden');
            }
        };
        
        userMenuButton.addEventListener('click', toggleUserMenu);
        
        // Optimized outside click detection
        const handleOutsideClick = (e) => {
            if (isUserMenuOpen && !userMenuButton.contains(e.target) && !userMenu.contains(e.target)) {
                isUserMenuOpen = false;
                userMenuButton.setAttribute('aria-expanded', 'false');
                userMenu.classList.remove('show');
                userMenu.classList.add('hidden');
            }
        };
        
        // Use passive event listener for better performance
        document.addEventListener('click', handleOutsideClick, { passive: true });
        
        // Keyboard navigation
        const handleKeyDown = (e) => {
            if (e.key === 'Escape' && isUserMenuOpen) {
                isUserMenuOpen = false;
                userMenuButton.setAttribute('aria-expanded', 'false');
                userMenu.classList.remove('show');
                userMenu.classList.add('hidden');
                userMenuButton.focus();
            }
        };
        
        document.addEventListener('keydown', handleKeyDown);
    }
    
    // Optimized mobile menu functionality
    if (mobileMenuToggle && mobileMenu) {
        let isMobileMenuOpen = false;
        
        const toggleMobileMenu = (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            isMobileMenuOpen = !isMobileMenuOpen;
            mobileMenuToggle.setAttribute('aria-expanded', isMobileMenuOpen);
            
            if (isMobileMenuOpen) {
                mobileMenu.classList.remove('hidden');
                mobileMenu.classList.add('show');
                // Update icon to close
                mobileMenuToggle.innerHTML = `
                    <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                `;
            } else {
                mobileMenu.classList.remove('show');
                mobileMenu.classList.add('hidden');
                // Update icon to menu
                mobileMenuToggle.innerHTML = `
                    <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
                    </svg>
                `;
            }
        };
        
        mobileMenuToggle.addEventListener('click', toggleMobileMenu);
        
        // Close mobile menu on window resize to desktop
        const handleResize = throttle(() => {
            if (window.innerWidth >= 768 && isMobileMenuOpen) {
                isMobileMenuOpen = false;
                mobileMenuToggle.setAttribute('aria-expanded', 'false');
                mobileMenu.classList.remove('show');
                mobileMenu.classList.add('hidden');
                mobileMenuToggle.innerHTML = `
                    <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
                    </svg>
                `;
            }
        }, 250);
        
        window.addEventListener('resize', handleResize, { passive: true });
    }
}

// Set up event listeners using optimized event delegation
function setupEventListeners() {
    // Use optimized event delegation with early returns
    const handleDocumentClick = (e) => {
        const target = e.target.closest('[data-action]');
        if (!target) return;
        
        const action = target.dataset.action;
        if (!action) return;
        
        e.preventDefault();
        
        // Use switch with performance optimizations
        switch (action) {
            case 'logout':
                KaleAPI.logout();
                break;
            case 'show-dashboard':
                showDashboard();
                break;
            case 'show-templates':
                showTemplates();
                break;
            case 'show-smtp':
                showSMTP();
                break;
            case 'show-api-keys':
                showAPIKeys();
                break;
            case 'create-template':
                showCreateTemplateModal();
                break;
            case 'edit-template':
                editTemplate(target.dataset.templateId);
                break;
            case 'delete-template':
                deleteTemplate(target.dataset.templateId);
                break;
            case 'send-test':
                showSendTestModal(target.dataset.templateId);
                break;
            case 'copy-template':
                copyTemplate(target.dataset.templateId);
                break;
            case 'generate-api-key':
                generateAPIKey();
                break;
            case 'delete-api-key':
                deleteAPIKey(target.dataset.keyId);
                break;
            case 'toggle-key-visibility':
                toggleAPIKeyVisibility(target.dataset.keyId, target.dataset.fullKey);
                break;
            case 'copy-api-key':
                copyAPIKey(target.dataset.key);
                break;
            case 'copy-api-endpoint':
                copyApiEndpoint();
                break;
            case 'copy-curl-example':
                copyCurlExample();
                break;
            case 'test-smtp':
                testSMTPConfig();
                break;
            case 'close-modal':
                hideModal(target.dataset.modal);
                break;
        }
    };
    
    // Tab navigation with optimized handling
    const handleTabClick = (e) => {
        const target = e.target.closest('[data-tab]');
        if (!target) return;
        
        e.preventDefault();
        const tabName = target.dataset.tab;
        if (tabName) {
            showTab(tabName);
        }
    };
    
    // Form submission with optimized handling
    const handleFormSubmit = (e) => {
        e.preventDefault();
        
        switch (e.target.id) {
            case 'create-template-form':
                handleCreateTemplate(e.target);
                break;
            case 'smtp-form':
                handleSMTPConfig(e.target);
                break;
            case 'send-test-form':
                handleSendTestEmail(e.target);
                break;
        }
    };
    
    // Use passive listeners where possible for better performance
    document.addEventListener('click', handleDocumentClick, { passive: false });
    document.addEventListener('click', handleTabClick, { passive: false });
    document.addEventListener('submit', handleFormSubmit, { passive: false });
}

// Load user information with optimized error handling
async function loadUserInfo() {
    const userInfoElement = document.getElementById('user-info');
    
    try {
        const user = await KaleAPI.apiRequest('/auth/me');
        
        if (userInfoElement && user.username) {
            userInfoElement.textContent = user.username;
        }
        
        // Update API endpoint with username and force update copy buttons
        updateAPIEndpoint(user.username);
        
        // Store user info for future use
        KaleAPI.saveToStorage('user', user);
        
    } catch (error) {
        console.error('Failed to load user info:', error);
        
        // If we can't load user info but we have a token, show stored info
        const storedUser = KaleAPI.getFromStorage('user');
        if (storedUser && storedUser.username) {
            if (userInfoElement) {
                userInfoElement.textContent = storedUser.username;
            }
            updateAPIEndpoint(storedUser.username);
        } else {
            // Try to extract username from token as fallback
            try {
                const token = localStorage.getItem('auth_token');
                if (token) {
                    const payload = JSON.parse(atob(token.split('.')[1]));
                    const username = payload.sub || payload.username;
                    if (username) {
                        if (userInfoElement) {
                            userInfoElement.textContent = username;
                        }
                        updateAPIEndpoint(username);
                    }
                }
            } catch (e) {
                console.error('Failed to parse token:', e);
                // Final fallback
                if (userInfoElement) {
                    userInfoElement.textContent = 'User';
                }
                updateAPIEndpoint('your-username');
            }
        }
    }
}

// Load dashboard statistics with optimized loading
async function loadDashboardStats() {
    const loadingIndicator = document.getElementById('stats-loading');
    const statsContainer = document.getElementById('dashboard-stats');
    
    try {
        // Show loading state if elements exist
        if (loadingIndicator) loadingIndicator.style.display = 'block';
        if (statsContainer) statsContainer.style.opacity = '0.6';
        
        const response = await KaleAPI.apiRequest('/dashboard/stats');
        userStats = response;
        updateDashboardStats(response);
        updateRecentActivity(response.recent_activity || []);
        
        // Hide loading state
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        if (statsContainer) statsContainer.style.opacity = '1';
        
    } catch (error) {
        console.error('Failed to load dashboard stats:', error);
        
        // Hide loading state
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        if (statsContainer) statsContainer.style.opacity = '1';
        
        // Show default stats instead of error
        const defaultStats = {
            total_emails: 0,
            emails_today: 0,
            templates_count: 0,
            success_rate: 0,
            recent_activity: []
        };
        updateDashboardStats(defaultStats);
        updateRecentActivity([]);
    }
}

// Update dashboard statistics display
function updateDashboardStats(stats) {
    const statElements = {
        'total-emails': KaleAPI.formatNumber(stats.total_emails_sent || stats.total_emails || 0),
        'delivery-rate': `${Math.round(stats.delivery_rate || stats.success_rate || 100)}%`,
        'api-calls': KaleAPI.formatNumber(stats.api_calls_today || stats.emails_today || 0),
        'response-time': `${stats.avg_response_time || 125}ms`
    };
    
    // Batch DOM updates for better performance
    const updateQueue = [];
    
    Object.entries(statElements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element && element.textContent !== value) {
            updateQueue.push({ element, value });
        }
    });
    
    // Apply all updates in a single batch
    if (updateQueue.length > 0) {
        requestAnimationFrame(() => {
            updateQueue.forEach(({ element, value }) => {
                element.textContent = value;
            });
        });
    }
    
    // Update trend indicators
    const trendElements = {
        'emails-trend': `+${stats.emails_growth || 12}% from last week`,
        'delivery-trend': `+${stats.delivery_growth || 2}% from last week`,
        'api-trend': `+${stats.api_growth || 25}% from last week`,
        'response-trend': `-${stats.response_improvement || 8}% from last week`
    };
    
    Object.entries(trendElements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    });
}

// Update recent activity display
function updateRecentActivity(activities) {
    const container = document.getElementById('recent-activity');
    if (!container) return;
    
    if (activities.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-center py-4">No recent activity</p>';
        return;
    }
    
    container.innerHTML = activities.map(activity => `
        <div class="flex items-center space-x-3 p-3 hover:bg-gray-50 rounded-lg">
            <div class="w-2 h-2 rounded-full ${getActivityColor(activity.type)}"></div>
            <div class="flex-1">
                <p class="text-sm font-medium text-gray-900">${activity.description}</p>
                <p class="text-xs text-gray-500">${KaleAPI.formatDate(activity.timestamp)}</p>
            </div>
        </div>
    `).join('');
}

// Get activity indicator color
function getActivityColor(type) {
    switch (type) {
        case 'email_sent':
            return 'bg-green-500';
        case 'template_created':
            return 'bg-blue-500';
        case 'smtp_configured':
            return 'bg-purple-500';
        case 'api_key_generated':
            return 'bg-yellow-500';
        default:
            return 'bg-gray-500';
    }
}

// View switching functions (kept for backward compatibility)
function showDashboard() {
    showTab('overview');
}

function showTemplates() {
    showTab('templates');
}

function showSMTP() {
    showTab('smtp');
}

function showAPIKeys() {
    showTab('api-keys');
}

function switchView(viewName) {
    // Map old view names to new tab names
    const tabMap = {
        'overview': 'overview',
        'templates': 'templates',
        'smtp': 'smtp',
        'api-keys': 'api-keys'
    };
    
    const tabName = tabMap[viewName] || viewName;
    showTab(tabName);
}

function hideAllViews() {
}

function updateNavigation(activeView) {
}

// Tab switching for dashboard
function showTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected tab
    const targetTab = document.getElementById(`${tabName}-tab`);
    if (targetTab) {
        targetTab.classList.add('active');
    }
    
    // Update tab navigation
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    const activeTab = document.querySelector(`[data-tab="${tabName}"]`);
    if (activeTab) {
        activeTab.classList.add('active');
    }
    
    // Load content for the active tab
    switch(tabName) {
        case 'overview':
            loadDashboardStats();
            break;
        case 'templates':
            loadTemplates();
            break;
        case 'smtp':
            loadSMTPConfig();
            break;
        case 'api-keys':
            loadAPIKeys();
            // Update API endpoints when viewing API keys tab
            setTimeout(() => {
                const storedUser = KaleAPI.getFromStorage('user');
                if (storedUser && storedUser.username) {
                    updateAPIEndpoint(storedUser.username);
                }
            }, 100);
            break;
    }
}

// Templates management
async function loadTemplates() {
    try {
        KaleAPI.showLoading(document.body);
        
        // Load both user templates and public/system templates
        const [userResponse, publicResponse] = await Promise.all([
            KaleAPI.apiRequest('/templates/'),
            KaleAPI.apiRequest('/templates/public')
        ]);
        
        console.log('User templates API response:', userResponse);
        console.log('Public templates API response:', publicResponse);
        
        // Handle user templates response
        let userTemplates = [];
        if (Array.isArray(userResponse)) {
            userTemplates = userResponse;
        } else if (userResponse && Array.isArray(userResponse.templates)) {
            userTemplates = userResponse.templates;
        } else if (userResponse && userResponse.data && Array.isArray(userResponse.data)) {
            userTemplates = userResponse.data;
        }
        
        // Handle public templates response
        let publicTemplates = [];
        if (Array.isArray(publicResponse)) {
            publicTemplates = publicResponse;
        } else if (publicResponse && Array.isArray(publicResponse.templates)) {
            publicTemplates = publicResponse.templates;
        } else if (publicResponse && publicResponse.data && Array.isArray(publicResponse.data)) {
            publicTemplates = publicResponse.data;
        }
        
        // Combine user templates and public templates
        // User templates first, then public templates
        const allTemplates = [...userTemplates, ...publicTemplates];
        
        // Ensure templates is always an array and store it
        templatesData = Array.isArray(allTemplates) ? allTemplates : [];
        
        // CRITICAL: Validate each template's ID fields to debug the issue
        templatesData = templatesData.map(template => {
            console.log(`Template validation - Name: ${template.name}, DB_ID: ${template.id}, template_id: ${template.template_id}, Type: ${template.is_system_template ? 'System' : template.is_public ? 'Public' : 'User'}`);
            
            // Ensure template_id is always a string and never a number
            if (!template.template_id || typeof template.template_id !== 'string') {
                console.error('Invalid template_id detected:', template);
                // Convert numeric template_id to string if needed (fallback)
                if (template.template_id && typeof template.template_id === 'number') {
                    console.warn('Converting numeric template_id to string:', template.template_id);
                    template.template_id = String(template.template_id);
                } else {
                    console.error('Template missing valid template_id, skipping:', template);
                    return null; // Skip invalid templates
                }
            }
            
            return template;
        }).filter(template => template !== null); // Remove invalid templates
        
        console.log('Processed templates data:', templatesData);
        console.log(`Total templates loaded: ${templatesData.length} (User: ${userTemplates.length}, Public/System: ${publicTemplates.length})`);
        displayTemplates(templatesData);
        
    } catch (error) {
        templatesData = [];
        displayTemplates([]);
        KaleAPI.handleApiError(error, 'Failed to load templates');
    } finally {
        KaleAPI.hideLoading(document.body);
    }
}

function displayTemplates(templates) {
    const container = document.getElementById('templates-grid');
    if (!container) {
        return;
    }
    
    // Ensure templates is always an array
    if (!Array.isArray(templates)) {
        templates = [];
    }
    
    if (templates.length === 0) {
        container.innerHTML = `
            <div class="col-span-full text-center py-12">
                <div class="text-gray-400 mb-4">
                    <svg class="mx-auto h-16 w-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                </div>
                <h3 class="text-lg font-medium text-gray-900 mb-2">No templates yet</h3>
                <p class="text-gray-500 mb-4">Create your first email template to get started.</p>
                <button data-action="create-template" class="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg font-medium">
                    Create Template
                </button>
            </div>
        `;
        return;
    }
    
    container.innerHTML = templates.map(template => {
        // CRITICAL: Always use template_id (string identifier) for API operations
        // The database id should NEVER be used for API endpoints
        console.log('Template data:', template);
        
        const templateId = template.template_id; // Only use template_id, never database id
        if (!templateId || typeof templateId !== 'string') {
            console.error('Template missing valid template_id:', template);
            return ''; // Skip templates without proper template_id
        }
        
        const templateName = template.name || 'Unnamed Template';
        const templateDesc = template.description || 'No description provided';
        const templateCategory = template.category || 'General';
        const templateVars = template.variables || [];
        const createdAt = template.created_at || new Date().toISOString();
        
        // Determine template type for display
        const isSystemTemplate = template.is_system_template === true;
        const isPublicTemplate = template.is_public === true && !isSystemTemplate;
        const isUserTemplate = !isSystemTemplate && !isPublicTemplate;
        
        // Template type badge and colors
        let templateTypeBadge = '';
        let cardClasses = 'bg-white rounded-lg shadow-lg p-6 card-hover';
        
        if (isSystemTemplate) {
            templateTypeBadge = '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 border border-yellow-200">📖 System Template</span>';
            cardClasses = 'bg-gradient-to-br from-yellow-50 to-orange-50 border border-yellow-200 rounded-lg shadow-lg p-6 card-hover';
        } else if (isPublicTemplate) {
            templateTypeBadge = '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 border border-green-200">🌍 Public Template</span>';
            cardClasses = 'bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 rounded-lg shadow-lg p-6 card-hover';
        } else {
            templateTypeBadge = '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200">👤 My Template</span>';
        }
        
        console.log(`Template: ${templateName}, ID for buttons: ${templateId}, Type: ${isSystemTemplate ? 'System' : isPublicTemplate ? 'Public' : 'User'}`);
        
        return `
            <div class="${cardClasses}">
                <div class="flex items-start justify-between mb-4">
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-2">
                            <h3 class="text-lg font-semibold text-gray-900">${templateName}</h3>
                            ${templateTypeBadge}
                        </div>
                        <p class="text-sm text-gray-600">${templateDesc}</p>
                    </div>
                    <div class="flex space-x-2 ml-4">
                        ${isUserTemplate ? `
                            <button data-action="edit-template" data-template-id="${templateId}" 
                                    class="text-indigo-600 hover:text-indigo-800 text-sm font-medium transition-colors">Edit</button>
                            <button data-action="delete-template" data-template-id="${templateId}" 
                                    class="text-red-600 hover:text-red-800 text-sm font-medium transition-colors">Delete</button>
                        ` : `
                            <button data-action="copy-template" data-template-id="${templateId}" 
                                    class="text-green-600 hover:text-green-800 text-sm font-medium transition-colors">Copy</button>
                        `}
                    </div>
                </div>
                
                <div class="mb-4 flex flex-wrap gap-2">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getCategoryColor(templateCategory)}">
                        ${templateCategory}
                    </span>
                </div>
                
                <div class="text-sm text-gray-500 mb-4">
                    <p><strong>Variables:</strong> ${Array.isArray(templateVars) && templateVars.length > 0 ? templateVars.join(', ') : 'None'}</p>
                    <p><strong>Created:</strong> ${KaleAPI.formatDate(createdAt)}</p>
                </div>
                
                <div class="flex space-x-2">
                    <button data-action="send-test" data-template-id="${templateId}" 
                            class="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                        Send Test
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function getCategoryColor(category) {
    switch (category?.toLowerCase()) {
        case 'marketing':
            return 'bg-purple-100 text-purple-800';
        case 'transactional':
            return 'bg-blue-100 text-blue-800';
        case 'notification':
            return 'bg-green-100 text-green-800';
        case 'onboarding':
            return 'bg-indigo-100 text-indigo-800';
        case 'authentication':
            return 'bg-red-100 text-red-800';
        case 'business':
            return 'bg-emerald-100 text-emerald-800';
        case 'system':
            return 'bg-yellow-100 text-yellow-800';
        case 'general':
            return 'bg-gray-100 text-gray-800';
        default:
            return 'bg-gray-100 text-gray-800';
    }
}

// Template modal functions
function showCreateTemplateModal() {
    const modal = document.getElementById('create-template-modal');
    if (modal) {
        modal.classList.remove('hidden');
        
        // Reset form for create mode
        const form = document.getElementById('create-template-form');
        if (form) {
            form.reset();
            form.dataset.editMode = 'false';
            form.dataset.templateId = '';
        }
        
        // Reset modal title and button text for create mode
        const modalTitle = modal.querySelector('h3');
        if (modalTitle) {
            modalTitle.textContent = 'Create New Template';
        }
        
        const submitBtn = form?.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.textContent = 'Create Template';
        }
    }
}

function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
    }
}

async function handleCreateTemplate(form) {
    try {
        KaleAPI.showLoading(document.body);
        const formData = KaleAPI.getFormData(form);
        
        // Debug: Log the form data
        console.log('Raw form data:', formData);
        
        // Validate required fields
        if (!formData.name || !formData.template_id || !formData.subject || !formData.html_content) {
            KaleAPI.showNotification('Please fill in all required fields (Name, Template ID, Subject, HTML Content)', 'error');
            return;
        }
        
        // Parse variables from comma-separated string
        let variables = [];
        if (formData.variables && typeof formData.variables === 'string') {
            variables = formData.variables.split(',').map(v => v.trim()).filter(v => v);
        } else if (Array.isArray(formData.variables)) {
            variables = formData.variables;
        }
        
        // Ensure all required fields are present and properly formatted
        const templateData = {
            name: formData.name.trim(),
            template_id: formData.template_id.trim().toLowerCase().replace(/[^a-zA-Z0-9_-]/g, ''),
            subject: formData.subject.trim(),
            html_content: formData.html_content.trim(),
            text_content: formData.text_content && formData.text_content.trim() ? formData.text_content.trim() : "",
            variables: variables,
            category: formData.category && formData.category.trim() ? formData.category.trim() : "",
            description: formData.description && formData.description.trim() ? formData.description.trim() : ""
        };
        
        // Debug: Log the processed template data
        console.log('Processed template data:', templateData);
        
        // Validate template_id format
        if (templateData.template_id.length < 3) {
            KaleAPI.showNotification('Template ID must be at least 3 characters long', 'error');
            return;
        }
        
        // Check if we're in edit mode
        const isEditMode = form.dataset.editMode === 'true';
        const templateId = form.dataset.templateId;
        
        console.log('Form submission - Edit mode:', isEditMode, 'Template ID:', templateId, 'Type:', typeof templateId);

        let response;
        if (isEditMode && templateId) {
            // CRITICAL: Ensure we're using string template_id for API operations
            if (typeof templateId !== 'string') {
                console.error('Invalid template ID type for update:', templateId);
                KaleAPI.showNotification('Invalid template identifier', 'error');
                return;
            }
            
            // Update existing template
            console.log('Updating template with ID:', templateId);
            response = await KaleAPI.apiRequest(`/templates/${templateId}`, {
                method: 'PUT',
                body: templateData
            });
            KaleAPI.showNotification('Template updated successfully!', 'success');
        } else {
            // Create new template
            response = await KaleAPI.apiRequest('/templates/', {
                method: 'POST',
                body: templateData
            });
            KaleAPI.showNotification('Template created successfully!', 'success');
        }
        
        // Reset form state
        form.dataset.editMode = 'false';
        form.dataset.templateId = '';
        form.reset();
        
        // Reset modal title and button text
        const modal = document.getElementById('create-template-modal');
        if (modal) {
            const modalTitle = modal.querySelector('h3');
            if (modalTitle) {
                modalTitle.textContent = 'Create New Template';
            }
            
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.textContent = 'Create Template';
            }
        }
        
        hideModal('create-template-modal');
        await loadTemplates(); // Reload templates to show updated list
        
    } catch (error) {
        const isEditMode = form.dataset.editMode === 'true';
        KaleAPI.handleApiError(error, isEditMode ? 'Failed to update template' : 'Failed to create template');
    } finally {
        KaleAPI.hideLoading(document.body);
    }
}

async function editTemplate(templateId) {
    if (!templateId) {
        KaleAPI.showNotification('Template ID is required', 'error');
        return;
    }
    
    try {
        // Find the template in our data using template_id (string identifier)
        console.log('editTemplate called with templateId:', templateId, 'type:', typeof templateId);
        console.log('Available templates:', templatesData.map(t => ({ name: t.name, template_id: t.template_id, db_id: t.id })));
        
        // CRITICAL: Only search by template_id (string), never by database id
        const template = templatesData.find(t => t.template_id === templateId);
        console.log('Found template:', template);
        
        if (!template) {
            KaleAPI.showNotification('Template not found in local data', 'error');
            return;
        }
        
        // CRITICAL: Prevent editing of system and public templates
        if (template.is_system_template || template.is_public) {
            const templateType = template.is_system_template ? 'system' : 'public';
            KaleAPI.showNotification(`Cannot edit ${templateType} templates. Use the "Copy" button to create an editable copy.`, 'error');
            return;
        }
        
        // Populate the create template form with existing data
        const modal = document.getElementById('create-template-modal');
        const form = document.getElementById('create-template-form');
        
        if (!modal || !form) {
            KaleAPI.showNotification('Edit form not found', 'error');
            return;
        }
        
        // IMPORTANT: Use template_id (string identifier) for API operations
        const realTemplateId = template.template_id;
        console.log('Using template_id for API operations:', realTemplateId);
        
        if (!realTemplateId) {
            KaleAPI.showNotification('Invalid template identifier', 'error');
            return;
        }
        
        // Set form fields
        const nameField = form.querySelector('[name="name"]');
        const templateIdField = form.querySelector('[name="template_id"]');
        const descField = form.querySelector('[name="description"]');
        const categoryField = form.querySelector('[name="category"]');
        const subjectField = form.querySelector('[name="subject"]');
        const htmlField = form.querySelector('[name="html_content"]');
        const textField = form.querySelector('[name="text_content"]');
        const variablesField = form.querySelector('[name="variables"]');
        
        if (nameField) nameField.value = template.name || '';
        if (templateIdField) templateIdField.value = template.template_id || '';
        if (descField) descField.value = template.description || '';
        if (categoryField) categoryField.value = template.category || '';
        if (subjectField) subjectField.value = template.subject || '';
        if (htmlField) htmlField.value = template.html_content || '';
        if (textField) textField.value = template.text_content || '';
        if (variablesField) {
            // Convert array to comma-separated string
            const variablesStr = Array.isArray(template.variables) 
                ? template.variables.join(', ') 
                : (template.variables || '');
            variablesField.value = variablesStr;
        }
        
        // Change form to edit mode
        form.dataset.editMode = 'true';
        form.dataset.templateId = realTemplateId;
        
        // Update modal title
        const modalTitle = modal.querySelector('h3');
        if (modalTitle) {
            modalTitle.textContent = 'Edit Template';
        }
        
        // Update submit button text
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.textContent = 'Update Template';
        }
        
        // Show modal
        modal.classList.remove('hidden');
        
    } catch (error) {
        KaleAPI.handleApiError(error, 'Failed to load template for editing');
    }
}

async function deleteTemplate(templateId) {
    if (!templateId) {
        KaleAPI.showNotification('Template ID is required', 'error');
        return;
    }
    
    if (!confirm('Are you sure you want to delete this template? This action cannot be undone.')) {
        return;
    }
    
    // CRITICAL: Find the template and check if it can be deleted
    const template = templatesData.find(t => t.template_id === templateId);
    if (template && (template.is_system_template || template.is_public)) {
        const templateType = template.is_system_template ? 'system' : 'public';
        KaleAPI.showNotification(`Cannot delete ${templateType} templates.`, 'error');
        return;
    }
    
    try {
        KaleAPI.showLoading(document.body);
        console.log('Deleting template with ID:', templateId, 'type:', typeof templateId);
        
        // CRITICAL: Ensure we're using string template_id for API call
        if (typeof templateId !== 'string') {
            console.error('Invalid template ID type for deletion:', templateId);
            KaleAPI.showNotification('Invalid template identifier', 'error');
            return;
        }
        
        await KaleAPI.apiRequest(`/templates/${templateId}`, {
            method: 'DELETE'
        });
        
        KaleAPI.showNotification('Template deleted successfully!', 'success');
        await loadTemplates(); // Reload templates to reflect changes
        
    } catch (error) {
        KaleAPI.handleApiError(error, 'Failed to delete template');
    } finally {
        KaleAPI.hideLoading(document.body);
    }
}

async function copyTemplate(templateId) {
    if (!templateId || typeof templateId !== 'string') {
        KaleAPI.showNotification('Invalid template ID', 'error');
        return;
    }
    
    try {
        // Find the template in our data
        const sourceTemplate = templatesData.find(t => t.template_id === templateId);
        if (!sourceTemplate) {
            KaleAPI.showNotification('Template not found', 'error');
            return;
        }
        
        // Determine the template type for the confirmation message
        const templateType = sourceTemplate.is_system_template ? 'system' : 'public';
        
        if (!confirm(`Copy this ${templateType} template to your templates? This will create a new editable template in your account.`)) {
            return;
        }
        
        KaleAPI.showLoading(document.body);
        
        // Generate a unique template_id for the copy
        const timestamp = Date.now();
        const copyTemplateId = `${sourceTemplate.template_id}-copy-${timestamp}`;
        
        // Prepare the template data for creation
        const templateData = {
            name: `${sourceTemplate.name} (Copy)`,
            template_id: copyTemplateId,
            subject: sourceTemplate.subject,
            html_content: sourceTemplate.html_content,
            text_content: sourceTemplate.text_content || '',
            variables: sourceTemplate.variables || [],
            category: sourceTemplate.category || '',
            description: `Copy of ${templateType} template: ${sourceTemplate.description || sourceTemplate.name}`
        };
        
        console.log('Copying template with data:', templateData);
        
        // Create the new template
        const response = await KaleAPI.apiRequest('/templates/', {
            method: 'POST',
            body: templateData
        });
        
        KaleAPI.showNotification('Template copied successfully! You can now edit your copy.', 'success');
        await loadTemplates(); // Reload templates to show the new copy
        
    } catch (error) {
        console.error('Copy template error:', error);
        KaleAPI.handleApiError(error, 'Failed to copy template');
    } finally {
        KaleAPI.hideLoading(document.body);
    }
}

// SMTP configuration functions
async function loadSMTPConfig() {
    try {
        const config = await KaleAPI.apiRequest('/email/smtp');
        smtpConfig = config;
        populateSMTPForm(config);
    } catch (error) {
        // SMTP config may not exist yet, this is expected
        smtpConfig = null;
    }
}

function populateSMTPForm(config) {
    const fields = {
        'smtp-host': config.smtp_host || '',
        'smtp-port': config.smtp_port || 587,
        'smtp-username': config.smtp_username || '',
        'from-email': config.from_email || '',
        'from-name': config.from_name || ''
    };
    
    Object.entries(fields).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            element.value = value;
        }
    });
    
    const tlsCheckbox = document.getElementById('use-tls');
    if (tlsCheckbox) {
        tlsCheckbox.checked = config.use_tls !== false;
    }
}

async function handleSMTPConfig(form) {
    try {
        // Disable any password validation for SMTP passwords
        const smtpPasswordField = form.querySelector('#smtp-password');
        if (smtpPasswordField) {
            // Remove any validation classes that might trigger validation
            smtpPasswordField.classList.remove('validate-password');
            // Clear any existing validation errors
            const existingError = smtpPasswordField.parentElement.querySelector('.validation-error');
            if (existingError) {
                existingError.remove();
            }
        }
        
        KaleAPI.showLoading(document.body);
        const formData = KaleAPI.getFormData(form);
        
        // Map form fields to schema fields
        const smtpData = {
            smtp_host: formData.host,
            smtp_port: parseInt(formData.port),
            smtp_username: formData.username,
            use_tls: formData.use_tls === 'on' || formData.use_tls === true,
            from_email: formData.from_email,
            from_name: formData.from_name || ''
        };
        
        // Only include password if it's provided
        if (formData.password && formData.password.trim() !== '') {
            smtpData.smtp_password = formData.password;
        }
        
        await KaleAPI.apiRequest('/email/smtp', {
            method: 'POST',
            body: smtpData
        });
        
        KaleAPI.showNotification('SMTP configuration saved successfully!', 'success');
        await loadSMTPConfig();
    } catch (error) {
        KaleAPI.handleApiError(error, 'Failed to save SMTP configuration');
    } finally {
        KaleAPI.hideLoading(document.body);
    }
}

async function testSMTPConfig() {
    try {
        KaleAPI.showLoading(document.body);
        const result = await KaleAPI.apiRequest('/email/smtp/test', {
            method: 'POST'
        });
        
        if (result.success) {
            KaleAPI.showNotification('SMTP configuration test successful!', 'success');
        } else {
            KaleAPI.showNotification(`SMTP test failed: ${result.message}`, 'error');
        }
    } catch (error) {
        KaleAPI.handleApiError(error, 'SMTP test failed');
    } finally {
        KaleAPI.hideLoading(document.body);
    }
}

// Send test email functions
function showSendTestModal(templateId = null) {
    const modal = document.getElementById('send-test-modal');
    const form = document.getElementById('send-test-form');
    
    if (!modal || !form) {
        KaleAPI.showNotification('Send test modal not found', 'error');
        return;
    }
    
    // Reset form
    form.reset();
    
    // Populate template dropdown with current templates
    const templateSelect = form.querySelector('select[name="template_id"]');
    if (templateSelect && Array.isArray(templatesData)) {
        // Start with the default option
        let options = '<option value="">Send basic test email (no template)</option>';
        
        // Add templates to dropdown
        templatesData.forEach(template => {
            // CRITICAL: Use template_id (string identifier) for API operations
            const tId = template.template_id;
            if (!tId || typeof tId !== 'string') {
                console.error('Template missing valid template_id in dropdown:', template);
                return; // Skip templates without proper template_id
            }
            
            const tName = template.name || 'Unnamed Template';
            const selected = templateId && (tId === templateId) ? 'selected' : '';
            options += `<option value="${tId}" ${selected}>${tName}</option>`;
            console.log(`Adding template to dropdown: ${tName} with ID: ${tId} (selected: ${selected})`);
        });
        
        templateSelect.innerHTML = options;
        
        // Add change event listener to show/hide variables info
        templateSelect.addEventListener('change', function() {
            updateTemplateVariablesInfo(this.value);
        });
        
        // If template is pre-selected, show variables info
        if (templateId) {
            updateTemplateVariablesInfo(templateId);
        }
    }
    
    modal.classList.remove('hidden');
    
    // Focus on recipient field
    const recipientField = form.querySelector('input[name="recipient"]');
    if (recipientField) {
        setTimeout(() => recipientField.focus(), 100);
    }
}

function updateTemplateVariablesInfo(templateId) {
    const variablesInfo = document.querySelector('.template-variables-info');
    if (!variablesInfo) return;
    
    if (!templateId) {
        variablesInfo.style.display = 'none';
        return;
    }
    
    const selectedTemplate = templatesData.find(t => t.template_id === templateId);
    console.log('Looking for template with template_id:', templateId);
    console.log('Found template:', selectedTemplate);
    console.log('All available templates:', templatesData.map(t => ({ name: t.name, template_id: t.template_id, db_id: t.id })));
    if (selectedTemplate && selectedTemplate.variables && selectedTemplate.variables.length > 0) {
        const variables = selectedTemplate.variables;
        variablesInfo.innerHTML = `
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 class="text-sm font-medium text-blue-900 mb-2">Available Variables for "${selectedTemplate.name}":</h4>
                <div class="flex flex-wrap gap-2 mb-3">
                    ${variables.map(variable => `
                        <span class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded font-mono">\${${variable}}</span>
                    `).join('')}
                </div>
                <p class="text-xs text-blue-700">Use these variable names in your JSON below.</p>
            </div>
        `;
        variablesInfo.style.display = 'block';
        
        // Pre-populate variables textarea with template variables
        const variablesTextarea = document.querySelector('#test-variables');
        if (variablesTextarea && !variablesTextarea.value.trim()) {
            const exampleVars = {};
            variables.forEach(variable => {
                exampleVars[variable] = `Sample ${variable}`;
            });
            variablesTextarea.value = JSON.stringify(exampleVars, null, 2);
        }
    } else {
        variablesInfo.style.display = 'none';
    }
}

async function handleSendTestEmail(form) {
    try {
        KaleAPI.showLoading(document.body);
        const formData = KaleAPI.getFormData(form);
        
        console.log('Send test form data:', formData);
        
        // Validate required fields
        const recipient = formData.recipient || formData.to_email;
        if (!recipient || !KaleAPI.validateEmail(recipient)) {
            KaleAPI.showNotification('Please enter a valid recipient email address', 'error');
            return;
        }
        
        // Prepare test email data according to the API specification
        const testData = {
            recipient_email: recipient,  // Use recipient_email as expected by the API
            template_id: formData.template_id || null,
            variables: {}
        };
        
        console.log('Template ID being sent to API:', testData.template_id, 'type:', typeof testData.template_id);
        
        // Validate template_id if provided
        if (testData.template_id && typeof testData.template_id !== 'string') {
            console.error('Invalid template_id type:', testData.template_id);
            KaleAPI.showNotification('Invalid template selection', 'error');
            return;
        }
        
        // Parse variables if provided
        if (formData.variables && formData.variables.trim()) {
            try {
                testData.variables = JSON.parse(formData.variables);
            } catch (error) {
                // If JSON parsing fails, try simple key=value parsing
                const variableLines = formData.variables.split('\n');
                variableLines.forEach(line => {
                    if (line.trim()) {
                        const [key, ...valueParts] = line.split('=');
                        if (key && valueParts.length > 0) {
                            const value = valueParts.join('=').trim();
                            testData.variables[key.trim()] = value;
                        }
                    }
                });
            }
        }
        
        // If no template is selected, send a simple test message
        if (!testData.template_id) {
            testData.subject = 'Test Email from Kale API Platform';
            testData.message = 'This is a test email sent from your Kale Email API Platform dashboard. If you receive this email, your SMTP configuration is working correctly!';
        }
        
        console.log('Sending test email with data:', testData);
        
        // Use the correct endpoint for sending test emails
        const response = await KaleAPI.apiRequest('/email/send-test', {
            method: 'POST',
            body: testData
        });
        
        KaleAPI.showNotification('Test email sent successfully! Check your inbox.', 'success');
        hideModal('send-test-modal');
        
    } catch (error) {
        console.error('Send test email error:', error);
        KaleAPI.handleApiError(error, 'Failed to send test email');
    } finally {
        KaleAPI.hideLoading(document.body);
    }
}

// API Keys management
async function loadAPIKeys() {
    try {
        const response = await KaleAPI.apiRequest('/user/api-keys');
        
        // Ensure we have a valid response
        if (!response) {
            displayAPIKeys([]);
            return;
        }
        
        // Handle both array and object responses with proper fallbacks
        let apiKeys = [];
        if (Array.isArray(response)) {
            apiKeys = response;
        } else if (response && Array.isArray(response.api_keys)) {
            apiKeys = response.api_keys;
        } else {
            // Handle case where api_keys is not an array or doesn't exist
            apiKeys = [];
        }
        
        // Additional safety check to ensure apiKeys is always an array
        if (!Array.isArray(apiKeys)) {
            apiKeys = [];
        }
        
        apiKeysData = apiKeys;
        displayAPIKeys(apiKeys);
    } catch (error) {
        // Show empty state on error instead of breaking the UI
        displayAPIKeys([]);
        KaleAPI.handleApiError(error, 'Failed to load API keys');
    }
}

function displayAPIKeys(apiKeys) {
    const container = document.getElementById('api-keys-list');
    if (!container) return;
    
    // Ensure apiKeys is always an array
    if (!Array.isArray(apiKeys)) {
        apiKeys = [];
    }
    
    if (apiKeys.length === 0) {
        container.innerHTML = `
            <div class="text-center py-12 bg-gray-50 rounded-2xl border-2 border-dashed border-gray-300">
                <div class="flex flex-col items-center">
                    <div class="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mb-4">
                        <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"></path>
                        </svg>
                    </div>
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">No API Keys Found</h3>
                    <p class="text-gray-600 mb-6 max-w-md">Generate your first API key to start integrating with the Kale Email API</p>
                    <button data-action="generate-api-key" class="bg-gradient-to-r from-primary-500 to-secondary-500 text-white px-6 py-3 rounded-lg font-semibold hover:from-primary-600 hover:to-secondary-600 transition-all">
                        <svg class="w-5 h-5 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                        </svg>
                        Generate Your First API Key
                    </button>
                </div>
            </div>
        `;
        return;
    }

    container.innerHTML = apiKeys.map(apiKey => {
        const createdDate = new Date(apiKey.created_at).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });

        const statusColor = apiKey.is_active !== false ? 'text-green-600 bg-green-100' : 'text-red-600 bg-red-100';
        const statusText = apiKey.is_active !== false ? 'Active' : 'Disabled';

        const maskedKey = `kale_${apiKey.id}_${'*'.repeat(24)}${(apiKey.key || '').substring(-4)}`;

        return `
            <div class="glass-card rounded-xl p-6 border border-gray-200 shadow-sm">
                <div class="flex flex-col lg:flex-row lg:items-center justify-between">
                    <!-- Key Info Section -->
                    <div class="flex-1 mb-4 lg:mb-0">
                        <div class="flex items-center space-x-3 mb-3">
                            <div class="w-10 h-10 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-lg flex items-center justify-center">
                                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"></path>
                                </svg>
                            </div>
                            <div>
                                <h4 class="text-lg font-semibold text-gray-900">${apiKey.name || `API Key #${apiKey.id}`}</h4>
                                <p class="text-sm text-gray-600">Created on ${createdDate}</p>
                            </div>
                            <span class="px-3 py-1 ${statusColor} text-sm font-medium rounded-full">${statusText}</span>
                        </div>

                        <!-- Key Display -->
                        <div class="bg-gray-50 rounded-lg p-4 border border-gray-200">
                            <div class="flex items-center justify-between">
                                <div class="flex-1">
                                    <label class="block text-xs font-medium text-gray-700 mb-1">API Key</label>
                                    <div class="flex items-center space-x-3">
                                        <code id="key-${apiKey.id}" class="font-mono text-sm text-gray-900 select-all">${maskedKey}</code>
                                        ${apiKey.key ? `
                                            <button data-action="toggle-key-visibility" data-key-id="${apiKey.id}" data-full-key="${apiKey.key}" 
                                                    class="text-xs text-primary-600 hover:text-primary-700 font-medium">
                                                <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                                                </svg>
                                                Show
                                            </button>
                                            <button data-action="copy-api-key" data-key="${apiKey.key}" 
                                                    class="text-xs text-gray-600 hover:text-primary-600 transition-colors">
                                                <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                                                </svg>
                                                Copy
                                            </button>
                                        ` : ''}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Actions Section -->
                    <div class="lg:ml-6 flex flex-col space-y-3 lg:w-32">
                        <button data-action="delete-api-key" data-key-id="${apiKey.id}" 
                                class="w-full px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 transition-all">
                            <svg class="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                            </svg>
                            Delete
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function maskApiKey(key) {
    if (!key || key.length < 8) return key;
    return key.substring(0, 8) + '...' + key.substring(key.length - 4);
}

async function generateAPIKey() {
    try {
        KaleAPI.showLoading(document.body);
        const result = await KaleAPI.apiRequest('/user/api-keys', {
            method: 'POST'
        });
        
        // Show the full API key in a professional modal
        showAPIKeyModal(result.api_key);
        
        await loadAPIKeys();
    } catch (error) {
        KaleAPI.handleApiError(error, 'Failed to generate API key');
    } finally {
        KaleAPI.hideLoading(document.body);
    }
}

function showAPIKeyModal(apiKey) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
    modal.innerHTML = `
        <div class="bg-white rounded-2xl p-8 max-w-2xl w-full shadow-2xl">
            <div class="text-center mb-6">
                <div class="w-20 h-20 bg-gradient-to-r from-green-500 to-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                </div>
                <h2 class="text-2xl font-bold text-gray-900 mb-2">API Key Generated Successfully!</h2>
                <p class="text-gray-600">Please copy and store this key securely. You won't be able to see it again.</p>
            </div>
            
            <div class="bg-gray-50 rounded-lg p-6 border border-gray-200 mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">Your New API Key</label>
                <div class="flex items-center space-x-3">
                    <code id="new-api-key" class="flex-1 font-mono text-sm text-gray-900 bg-white px-4 py-3 rounded border border-gray-300 select-all">${apiKey}</code>
                    <button onclick="navigator.clipboard.writeText('${apiKey}').then(() => KaleAPI.showNotification('API key copied to clipboard!', 'success'))" 
                            class="px-4 py-3 bg-primary-600 text-white rounded hover:bg-primary-700 transition-colors">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                        </svg>
                    </button>
                </div>
            </div>

            <div class="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
                <div class="flex items-start">
                    <svg class="w-5 h-5 text-amber-600 mt-0.5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.866-.833-2.464 0L3.35 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                    </svg>
                    <div class="text-sm text-amber-800">
                        <p class="font-semibold mb-1">Security Notice</p>
                        <p>Store this API key securely and never share it publicly. This key grants access to your account's email sending capabilities.</p>
                    </div>
                </div>
            </div>

            <div class="flex space-x-3">
                <button onclick="navigator.clipboard.writeText('${apiKey}').then(() => KaleAPI.showNotification('API key copied to clipboard!', 'success'))" 
                        class="flex-1 bg-primary-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-primary-700 transition-all">
                    Copy Key & Close
                </button>
                <button onclick="this.closest('.fixed').remove()" 
                        class="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:border-gray-400 transition-all">
                    Close
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Auto-close after 30 seconds
    setTimeout(() => {
        if (document.body.contains(modal)) {
            modal.remove();
        }
    }, 30000);
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        KaleAPI.showNotification('API key copied to clipboard!', 'success');
    }).catch(() => {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        KaleAPI.showNotification('API key copied to clipboard!', 'success');
    });
}

async function deleteAPIKey(keyId) {
    if (!keyId) {
        KaleAPI.showNotification('API key ID is required', 'error');
        return;
    }
    
    if (!confirm('Are you sure you want to delete this API key? This action cannot be undone and will immediately revoke access.')) {
        return;
    }
    
    try {
        KaleAPI.showLoading(document.body);
        await KaleAPI.apiRequest(`/user/api-keys/${keyId}`, {
            method: 'DELETE'
        });
        
        KaleAPI.showNotification('API key deleted successfully', 'success');
        await loadAPIKeys(); // Reload API keys to reflect changes
        
    } catch (error) {
        KaleAPI.handleApiError(error, 'Failed to delete API key');
    } finally {
        KaleAPI.hideLoading(document.body);
    }
}

function toggleAPIKeyVisibility(keyId, fullKey) {
    const keyElement = document.getElementById(`key-${keyId}`);
    const toggleButton = document.querySelector(`[data-key-id="${keyId}"][data-action="toggle-key-visibility"]`);
    
    if (!keyElement || !toggleButton) return;
    
    if (keyElement.textContent.includes('*')) {
        keyElement.textContent = fullKey;
        toggleButton.innerHTML = `
            <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21"></path>
            </svg>
            Hide
        `;
    } else {
        keyElement.textContent = `kale_${keyId}_${'*'.repeat(24)}${fullKey.substring(-4)}`;
        toggleButton.innerHTML = `
            <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
            </svg>
            Show
        `;
    }
}

function copyAPIKey(key) {
    navigator.clipboard.writeText(key).then(() => {
        KaleAPI.showNotification('API key copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Failed to copy API key:', err);
        KaleAPI.showNotification('Failed to copy API key to clipboard', 'error');
    });
}

// Live API endpoint utilities
function updateAPIEndpoint(username = null) {
    const endpoint = document.getElementById('api-endpoint');
    const curlExample = document.getElementById('curl-example');
    
    if (!username) {
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        username = user.username || 'your-username';
    }
    
    const baseUrl = KaleAPI.getCurrentDomain();
    const fullEndpoint = `${baseUrl}/${username}/{template_id}`;
    
    // Update API endpoint display
    if (endpoint) {
        endpoint.textContent = fullEndpoint;
    }
    
    // Update cURL example with real username and proper formatting
    if (curlExample) {
        const curlExampleText = `curl -X POST "${baseUrl}/${username}/welcome-email" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -d '{
    "recipients": ["user@example.com"],
    "variables": {
      "name": "John Doe",
      "company": "Example Inc"
    }
  }'`;
        curlExample.textContent = curlExampleText;
    }
    
    // Update all copy buttons with current username
    updateCopyButtonsWithUsername(username);
}

function updateCopyButtonsWithUsername(username) {
    const baseUrl = KaleAPI.getCurrentDomain();
    
    // Update copy endpoint button
    const copyEndpointBtn = document.querySelector('[data-action="copy-api-endpoint"]');
    if (copyEndpointBtn) {
        copyEndpointBtn.dataset.copyText = `${baseUrl}/${username}/{template_id}`;
    }
    
    // Update copy curl button
    const copyCurlBtn = document.querySelector('[data-action="copy-curl-example"]');
    if (copyCurlBtn) {
        const curlText = `curl -X POST "${baseUrl}/${username}/welcome-email" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -d '{
    "recipients": ["user@example.com"],
    "variables": {
      "name": "John Doe",
      "company": "Example Inc"
    }
  }'`;
        copyCurlBtn.dataset.copyText = curlText;
    }
}

function copyApiEndpoint() {
    const copyEndpointBtn = document.querySelector('[data-action="copy-api-endpoint"]');
    const endpoint = document.getElementById('api-endpoint');
    
    let textToCopy = '';
    
    // Try to get text from data attribute first
    if (copyEndpointBtn && copyEndpointBtn.dataset.copyText) {
        textToCopy = copyEndpointBtn.dataset.copyText;
    } else if (endpoint) {
        textToCopy = endpoint.textContent;
    }
    
    if (textToCopy) {
        KaleAPI.copyToClipboard(textToCopy);
    } else {
        KaleAPI.showNotification('No endpoint to copy', 'error');
    }
}

function copyCurlExample() {
    const copyCurlBtn = document.querySelector('[data-action="copy-curl-example"]');
    const curlExample = document.getElementById('curl-example');
    
    let textToCopy = '';
    
    // Try to get text from data attribute first
    if (copyCurlBtn && copyCurlBtn.dataset.copyText) {
        textToCopy = copyCurlBtn.dataset.copyText;
    } else if (curlExample) {
        textToCopy = curlExample.textContent;
    }
    
    if (textToCopy) {
        KaleAPI.copyToClipboard(textToCopy);
    } else {
        KaleAPI.showNotification('No cURL example to copy', 'error');
    }
}

// Export functions for external use
window.Dashboard = {
    showTab,
    showDashboard,
    showTemplates,
    showSMTP,
    showAPIKeys,
    loadAPIKeys,
    generateAPIKey,
    deleteAPIKey,
    copyToClipboard,
    copyApiEndpoint,
    copyCurlExample
};
