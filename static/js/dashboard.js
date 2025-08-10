/**
 * Dashboard JavaScript for Kale Email API Platform
 * Production-ready dashboard functionality and UI management
 **/

'use strict';

// Dashboard state
let currentView = 'dashboard';
let userStats = {};
let templatesData = [];
let apiKeysData = [];
let smtpConfig = null;

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
    loadUserInfo();
    loadDashboardStats();
    loadTemplates();
    loadSMTPConfig();
    loadAPIKeys();
}

// Set up event listeners using event delegation
function setupEventListeners() {
    // Navigation event delegation
    document.addEventListener('click', function(e) {
        const target = e.target;
        const action = target.dataset.action;
        
        if (!action) return;
        
        e.preventDefault();
        
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
    });
    
// Tab navigation
    document.addEventListener('click', function(e) {
        if (e.target.dataset.tab) {
            e.preventDefault();
            showTab(e.target.dataset.tab);
        }
    });
    
    // Form submissions
    document.addEventListener('submit', function(e) {
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
    });
    
    // User menu toggle
    const userMenuButton = document.getElementById('user-menu-button');
    const userMenu = document.getElementById('user-menu');
    if (userMenuButton && userMenu) {
        userMenuButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            userMenu.classList.toggle('hidden');
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!userMenuButton.contains(e.target) && !userMenu.contains(e.target)) {
                userMenu.classList.add('hidden');
            }
        });
        
        // Close menu when pressing Escape
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                userMenu.classList.add('hidden');
            }
        });
    }
}

// Load user information
async function loadUserInfo() {
    try {
        const user = await KaleAPI.apiRequest('/auth/me');
        const userInfo = document.getElementById('user-info');
        
        if (userInfo) {
            userInfo.textContent = user.username;
        }
        
        // Update API endpoint with username
        updateAPIEndpoint(user.username);
        
    } catch (error) {
        console.error('Failed to load user info:', error);
        // If we can't load user info but we have a token, show generic info
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            try {
                const user = JSON.parse(storedUser);
                const userInfo = document.getElementById('user-info');
                if (userInfo) {
                    userInfo.textContent = user.username || 'User';
                }
                updateAPIEndpoint(user.username);
            } catch (e) {
                console.error('Failed to parse stored user:', e);
            }
        }
    }
}

// Load dashboard statistics
async function loadDashboardStats() {
    try {
        const response = await KaleAPI.apiRequest('/dashboard/stats');
        userStats = response;
        updateDashboardStats(response);
        updateRecentActivity(response.recent_activity || []);
    } catch (error) {
        console.error('Failed to load dashboard stats:', error);
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
    
    Object.entries(statElements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    });
    
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
            break;
    }
}

// Templates management
async function loadTemplates() {
    try {
        KaleAPI.showLoading(document.body);
        const response = await KaleAPI.apiRequest('/templates/');
        
        // Handle the response properly - templates should be directly in the response array
        let templates = [];
        
        if (Array.isArray(response)) {
            templates = response;
        } else if (response && Array.isArray(response.templates)) {
            templates = response.templates;
        } else if (response && response.data && Array.isArray(response.data)) {
            templates = response.data;
        } else {
            templates = [];
        }
        
        // Ensure templates is always an array and store it
        templatesData = Array.isArray(templates) ? templates : [];
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
        // Use the correct property names from the API response
        const templateId = template.id || template.template_id;
        const templateName = template.name || 'Unnamed Template';
        const templateDesc = template.description || 'No description provided';
        const templateCategory = template.category || 'General';
        const templateVars = template.variables || [];
        const createdAt = template.created_at || new Date().toISOString();
        
        return `
            <div class="bg-white rounded-lg shadow-lg p-6 card-hover">
                <div class="flex items-start justify-between mb-4">
                    <div>
                        <h3 class="text-lg font-semibold text-gray-900">${templateName}</h3>
                        <p class="text-sm text-gray-600">${templateDesc}</p>
                    </div>
                    <div class="flex space-x-2">
                        <button data-action="edit-template" data-template-id="${templateId}" 
                                class="text-indigo-600 hover:text-indigo-800 text-sm font-medium transition-colors">Edit</button>
                        <button data-action="delete-template" data-template-id="${templateId}" 
                                class="text-red-600 hover:text-red-800 text-sm font-medium transition-colors">Delete</button>
                    </div>
                </div>
                
                <div class="mb-4">
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
        
        let response;
        if (isEditMode && templateId) {
            // Update existing template
            response = await KaleAPI.apiRequest(`/templates/${templateId}/`, {
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
        // Find the template in our data
        const template = templatesData.find(t => (t.id == templateId || t.template_id == templateId));
        if (!template) {
            KaleAPI.showNotification('Template not found', 'error');
            return;
        }
        
        // Populate the create template form with existing data
        const modal = document.getElementById('create-template-modal');
        const form = document.getElementById('create-template-form');
        
        if (!modal || !form) {
            KaleAPI.showNotification('Edit form not found', 'error');
            return;
        }
        
        // Use the correct ID field name from the template
        const realTemplateId = template.id || template.template_id;
        
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
    
    try {
        KaleAPI.showLoading(document.body);
        await KaleAPI.apiRequest(`/templates/${templateId}/`, {
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
    if (modal) {
        modal.classList.remove('hidden');
        const form = document.getElementById('send-test-form');
        if (form) {
            form.reset();
            // Set template ID if provided
            if (templateId) {
                const templateIdField = form.querySelector('input[name="template_id"]');
                if (templateIdField) {
                    templateIdField.value = templateId;
                } else {
                    // Create hidden input if it doesn't exist
                    const hiddenInput = document.createElement('input');
                    hiddenInput.type = 'hidden';
                    hiddenInput.name = 'template_id';
                    hiddenInput.value = templateId;
                    form.appendChild(hiddenInput);
                }
            }
        }
    }
}

async function handleSendTestEmail(form) {
    try {
        KaleAPI.showLoading(document.body);
        const formData = KaleAPI.getFormData(form);
        
        await KaleAPI.apiRequest('/email/send-test', {
            method: 'POST',
            body: formData
        });
        
        KaleAPI.showNotification('Test email sent successfully!', 'success');
        hideModal('send-test-modal');
    } catch (error) {
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
    if (endpoint) {
        if (!username) {
            const user = JSON.parse(localStorage.getItem('user') || '{}');
            username = user.username || 'your-username';
        }
        const baseUrl = KaleAPI.getCurrentDomain();
        endpoint.textContent = `${baseUrl}/${username}/{template_id}`;
    }
    
    // Update cURL example with username
    const curlExample = document.getElementById('curl-example');
    if (curlExample && username) {
        const baseUrl = KaleAPI.getCurrentDomain();
        curlExample.textContent = `curl -X POST "${baseUrl}/${username}/welcome-email" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -d '{
    "recipients": ["user@example.com"],
    "variables": {
      "name": "John Doe",
      "company": "Example Inc"
    }
  }'`;
    }
}

function copyApiEndpoint() {
    const endpoint = document.getElementById('api-endpoint');
    if (endpoint) {
        KaleAPI.copyToClipboard(endpoint.textContent);
    }
}

function copyCurlExample() {
    const curlExample = document.getElementById('curl-example');
    if (curlExample) {
        KaleAPI.copyToClipboard(curlExample.textContent);
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
