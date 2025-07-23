/* Dashboard JavaScript for Kale Email API Platform */

let currentView = 'dashboard';
let userStats = {};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    if (!KaleAPI.checkAuthentication()) {
        return;
    }
    
    loadUserInfo();
    loadDashboardStats();
    initializeCharts();
    
    // Auto-refresh every 5 minutes
    setInterval(loadDashboardStats, 5 * 60 * 1000);
});

// Load user information
function loadUserInfo() {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    if (user.username) {
        document.getElementById('user-info').textContent = `Welcome, ${user.username}`;
        document.getElementById('api-endpoint').textContent = `https://kale.kanopus.org/${user.username}/{template_id}`;
    }
}

// Load dashboard statistics
async function loadDashboardStats() {
    try {
        const stats = await KaleAPI.apiRequest('/dashboard/stats');
        userStats = stats;
        
        // Update stat cards
        document.getElementById('total-emails').textContent = KaleAPI.formatNumber(stats.total_emails_sent);
        document.getElementById('emails-today').textContent = KaleAPI.formatNumber(stats.emails_sent_today);
        document.getElementById('total-templates').textContent = KaleAPI.formatNumber(stats.total_templates);
        document.getElementById('api-keys-count').textContent = KaleAPI.formatNumber(stats.api_keys_count || 0);
        
        // Update charts
        updateEmailChart();
        updateRecentActivity();
        
    } catch (error) {
        console.error('Failed to load dashboard stats:', error);
        KaleAPI.showNotification('Failed to load dashboard data', 'error');
    }
}

// Initialize charts
function initializeCharts() {
    const ctx = document.getElementById('emailChart');
    if (ctx) {
        window.emailChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Emails Sent',
                    data: [],
                    borderColor: '#4f46e5',
                    backgroundColor: 'rgba(79, 70, 229, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
}

// Update email chart
function updateEmailChart() {
    if (window.emailChart && userStats.email_history) {
        const labels = userStats.email_history.map(item => new Date(item.date).toLocaleDateString());
        const data = userStats.email_history.map(item => item.count);
        
        window.emailChart.data.labels = labels;
        window.emailChart.data.datasets[0].data = data;
        window.emailChart.update();
    }
}

// Update recent activity
function updateRecentActivity() {
    const container = document.getElementById('recent-activity');
    if (!container || !userStats.recent_activity) return;
    
    if (userStats.recent_activity.length === 0) {
        container.innerHTML = '<p class="text-gray-500">No recent activity</p>';
        return;
    }
    
    const html = userStats.recent_activity.map(activity => `
        <div class="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
            <div class="flex-shrink-0">
                <div class="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center">
                    <svg class="w-4 h-4 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                    </svg>
                </div>
            </div>
            <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-gray-900">${activity.description}</p>
                <p class="text-sm text-gray-500">${KaleAPI.formatDate(activity.timestamp)}</p>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

// View switching functions
function showDashboard() {
    hideAllViews();
    document.getElementById('dashboard-view').classList.remove('hidden');
    currentView = 'dashboard';
    updateNavigation();
}

function showTemplates() {
    hideAllViews();
    document.getElementById('templates-view').classList.remove('hidden');
    currentView = 'templates';
    updateNavigation();
    loadTemplates();
}

function showSMTP() {
    hideAllViews();
    document.getElementById('smtp-view').classList.remove('hidden');
    currentView = 'smtp';
    updateNavigation();
    loadSMTPConfig();
}

function showAPIKeys() {
    hideAllViews();
    document.getElementById('api-keys-view').classList.remove('hidden');
    currentView = 'api-keys';
    updateNavigation();
    loadAPIKeys();
}

function hideAllViews() {
    document.querySelectorAll('[id$="-view"]').forEach(view => {
        view.classList.add('hidden');
    });
}

function updateNavigation() {
    // Update navigation active states
    document.querySelectorAll('nav a').forEach(link => {
        link.classList.remove('text-indigo-600', 'border-b-2', 'border-indigo-600');
        link.classList.add('text-gray-900');
    });
    
    const activeLink = document.querySelector(`nav a[href="#${currentView}"]`);
    if (activeLink) {
        activeLink.classList.remove('text-gray-900');
        activeLink.classList.add('text-indigo-600', 'border-b-2', 'border-indigo-600');
    }
}

// Templates functions
async function loadTemplates() {
    try {
        const templates = await KaleAPI.apiRequest('/templates/');
        displayTemplates(templates);
    } catch (error) {
        console.error('Failed to load templates:', error);
        KaleAPI.showNotification('Failed to load templates', 'error');
    }
}

function displayTemplates(templates) {
    const container = document.getElementById('templates-list');
    if (!container) return;
    
    if (templates.length === 0) {
        container.innerHTML = `
            <div class="col-span-full text-center py-12">
                <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                </svg>
                <h3 class="mt-2 text-sm font-medium text-gray-900">No templates</h3>
                <p class="mt-1 text-sm text-gray-500">Get started by creating your first email template.</p>
                <div class="mt-6">
                    <button onclick="showCreateTemplate()" class="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg">
                        Create Template
                    </button>
                </div>
            </div>
        `;
        return;
    }
    
    const html = templates.map(template => `
        <div class="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow">
            <div class="flex justify-between items-start mb-4">
                <h3 class="text-lg font-semibold text-gray-900">${template.name}</h3>
                <span class="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">${template.category || 'General'}</span>
            </div>
            <p class="text-gray-600 mb-4">${template.description || 'No description'}</p>
            <div class="flex items-center justify-between">
                <span class="text-sm text-gray-500">ID: ${template.template_id}</span>
                <div class="flex space-x-2">
                    <button onclick="editTemplate('${template.template_id}')" 
                            class="text-indigo-600 hover:text-indigo-800 text-sm">
                        Edit
                    </button>
                    <button onclick="deleteTemplate('${template.template_id}')" 
                            class="text-red-600 hover:text-red-800 text-sm">
                        Delete
                    </button>
                </div>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

// Template modal functions
function showCreateTemplate() {
    document.getElementById('template-modal').classList.remove('hidden');
    document.getElementById('template-form').reset();
}

function hideCreateTemplate() {
    document.getElementById('template-modal').classList.add('hidden');
}

async function saveTemplate(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const templateData = {
        template_id: formData.get('template-id') || document.getElementById('template-id').value,
        name: formData.get('template-name') || document.getElementById('template-name').value,
        category: formData.get('template-category') || document.getElementById('template-category').value,
        subject: formData.get('template-subject') || document.getElementById('template-subject').value,
        description: formData.get('template-description') || document.getElementById('template-description').value,
        html_content: formData.get('template-html') || document.getElementById('template-html').value
    };
    
    try {
        await KaleAPI.apiRequest('/templates/', {
            method: 'POST',
            body: JSON.stringify(templateData)
        });
        
        KaleAPI.showNotification('Template created successfully!', 'success');
        hideCreateTemplate();
        loadTemplates();
        
    } catch (error) {
        console.error('Failed to create template:', error);
        KaleAPI.showNotification(error.message || 'Failed to create template', 'error');
    }
}

// SMTP configuration functions
async function loadSMTPConfig() {
    try {
        const config = await KaleAPI.apiRequest('/email/smtp');
        if (config) {
            populateSMTPForm(config);
        }
    } catch (error) {
        console.error('Failed to load SMTP config:', error);
        // It's OK if no config exists yet
    }
}

function populateSMTPForm(config) {
    document.getElementById('smtp-host').value = config.smtp_host || '';
    document.getElementById('smtp-port').value = config.smtp_port || 587;
    document.getElementById('smtp-username').value = config.smtp_username || '';
    document.getElementById('from-email').value = config.from_email || '';
    document.getElementById('from-name').value = config.from_name || '';
    document.getElementById('use-tls').checked = config.use_tls !== false;
}

async function saveSMTPConfig(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const smtpData = {
        smtp_host: formData.get('smtp-host') || document.getElementById('smtp-host').value,
        smtp_port: parseInt(formData.get('smtp-port') || document.getElementById('smtp-port').value),
        smtp_username: formData.get('smtp-username') || document.getElementById('smtp-username').value,
        smtp_password: formData.get('smtp-password') || document.getElementById('smtp-password').value,
        from_email: formData.get('from-email') || document.getElementById('from-email').value,
        from_name: formData.get('from-name') || document.getElementById('from-name').value,
        use_tls: document.getElementById('use-tls').checked
    };
    
    try {
        await KaleAPI.apiRequest('/email/smtp', {
            method: 'POST',
            body: JSON.stringify(smtpData)
        });
        
        KaleAPI.showNotification('SMTP configuration saved successfully!', 'success');
        
    } catch (error) {
        console.error('Failed to save SMTP config:', error);
        KaleAPI.showNotification(error.message || 'Failed to save SMTP configuration', 'error');
    }
}

async function testSMTPConfig() {
    try {
        await KaleAPI.apiRequest('/email/smtp/test', {
            method: 'POST'
        });
        
        KaleAPI.showNotification('SMTP connection test successful!', 'success');
        
    } catch (error) {
        console.error('SMTP test failed:', error);
        KaleAPI.showNotification(error.message || 'SMTP connection test failed', 'error');
    }
}

// API Keys functions
async function loadAPIKeys() {
    try {
        const apiKeys = await KaleAPI.apiRequest('/user/api-keys');
        displayAPIKeys(apiKeys);
    } catch (error) {
        console.error('Failed to load API keys:', error);
        KaleAPI.showNotification('Failed to load API keys', 'error');
    }
}

function displayAPIKeys(apiKeys) {
    const container = document.getElementById('api-keys-list');
    if (!container) return;
    
    if (apiKeys.length === 0) {
        container.innerHTML = `
            <div class="text-center py-12">
                <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"></path>
                </svg>
                <h3 class="mt-2 text-sm font-medium text-gray-900">No API keys</h3>
                <p class="mt-1 text-sm text-gray-500">Create your first API key to start using the API.</p>
                <div class="mt-6">
                    <button onclick="createAPIKey()" class="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg">
                        Create API Key
                    </button>
                </div>
            </div>
        `;
        return;
    }
    
    const html = apiKeys.map(key => `
        <div class="bg-white rounded-lg shadow-lg p-6">
            <div class="flex justify-between items-start">
                <div class="flex-1">
                    <h3 class="text-lg font-semibold text-gray-900">${key.name}</h3>
                    <p class="text-sm text-gray-500 mt-1">Created: ${KaleAPI.formatDate(key.created_at)}</p>
                    ${key.last_used ? `<p class="text-sm text-gray-500">Last used: ${KaleAPI.formatDate(key.last_used)}</p>` : ''}
                    <div class="mt-4">
                        <code class="bg-gray-100 px-2 py-1 rounded text-sm">${key.api_key_preview || 'kale_****...'}</code>
                        <button onclick="KaleAPI.copyToClipboard('${key.api_key || key.api_key_full}')" 
                                class="ml-2 text-indigo-600 hover:text-indigo-800 text-sm">
                            Copy
                        </button>
                    </div>
                </div>
                <button onclick="deleteAPIKey(${key.id})" 
                        class="text-red-600 hover:text-red-800 ml-4">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                    </svg>
                </button>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

async function createAPIKey() {
    const name = prompt('Enter a name for your API key:');
    if (!name) return;
    
    try {
        const newKey = await KaleAPI.apiRequest('/user/api-keys', {
            method: 'POST',
            body: JSON.stringify({ key_name: name })
        });
        
        // Show the new API key (this is the only time it will be shown in full)
        alert(`Your new API key (save this now, it won't be shown again):\n\n${newKey.api_key}`);
        
        KaleAPI.showNotification('API key created successfully!', 'success');
        loadAPIKeys();
        
    } catch (error) {
        console.error('Failed to create API key:', error);
        KaleAPI.showNotification(error.message || 'Failed to create API key', 'error');
    }
}

async function deleteAPIKey(keyId) {
    if (!confirm('Are you sure you want to delete this API key? This action cannot be undone.')) {
        return;
    }
    
    try {
        await KaleAPI.apiRequest(`/user/api-keys/${keyId}`, {
            method: 'DELETE'
        });
        
        KaleAPI.showNotification('API key deleted successfully!', 'success');
        loadAPIKeys();
        
    } catch (error) {
        console.error('Failed to delete API key:', error);
        KaleAPI.showNotification(error.message || 'Failed to delete API key', 'error');
    }
}

// Template editing functions
async function editTemplate(templateId) {
    // This would open the template in edit mode
    KaleAPI.showNotification('Template editing will be implemented soon', 'info');
}

async function deleteTemplate(templateId) {
    if (!confirm('Are you sure you want to delete this template? This action cannot be undone.')) {
        return;
    }
    
    try {
        await KaleAPI.apiRequest(`/templates/${templateId}`, {
            method: 'DELETE'
        });
        
        KaleAPI.showNotification('Template deleted successfully!', 'success');
        loadTemplates();
        
    } catch (error) {
        console.error('Failed to delete template:', error);
        KaleAPI.showNotification(error.message || 'Failed to delete template', 'error');
    }
}
