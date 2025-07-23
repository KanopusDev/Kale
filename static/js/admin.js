/* Admin Dashboard JavaScript for Kale Email API Platform */

let currentAdminView = 'overview';
let adminStats = {};

// Initialize admin dashboard
document.addEventListener('DOMContentLoaded', function() {
    if (!KaleAPI.checkAuthentication()) {
        return;
    }
    
    loadAdminInfo();
    loadSystemHealth();
    loadAdminStats();
    initializeAdminCharts();
    
    // Auto-refresh every 30 seconds
    setInterval(() => {
        loadSystemHealth();
        loadAdminStats();
    }, 30 * 1000);
});

// Load admin information
function loadAdminInfo() {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    if (user.username) {
        document.getElementById('admin-info').textContent = `Admin: ${user.username}`;
    }
}

// Load admin statistics
async function loadAdminStats() {
    try {
        const stats = await KaleAPI.apiRequest('/dashboard/admin/stats');
        adminStats = stats;
        
        // Update stat cards
        document.getElementById('total-users').textContent = KaleAPI.formatNumber(stats.total_users);
        document.getElementById('verified-users').textContent = KaleAPI.formatNumber(stats.verified_users);
        document.getElementById('emails-today').textContent = KaleAPI.formatNumber(stats.emails_sent_today);
        document.getElementById('active-users-today').textContent = KaleAPI.formatNumber(stats.active_users_today);
        
        // Update last updated timestamp
        document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
        
        // Update charts
        updateAdminCharts();
        
    } catch (error) {
        console.error('Failed to load admin stats:', error);
        KaleAPI.showNotification('Failed to load admin statistics', 'error');
    }
}

// Load system health
async function loadSystemHealth() {
    try {
        const health = await KaleAPI.apiRequest('/api/admin/system-health');
        updateSystemHealth(health);
    } catch (error) {
        console.error('Failed to load system health:', error);
        KaleAPI.showNotification('Failed to load system health', 'error');
    }
}

// Update system health indicators
function updateSystemHealth(health) {
    // Database health
    const dbStatus = document.getElementById('db-status');
    const dbPoolSize = document.getElementById('db-pool-size');
    const dbActiveConnections = document.getElementById('db-active-connections');
    
    if (health.database) {
        dbStatus.className = `status-indicator ${health.database.status === 'healthy' ? 'status-healthy' : 'status-error'}`;
        dbPoolSize.textContent = health.database.connection_pool_size || '-';
        dbActiveConnections.textContent = health.database.active_connections || '-';
    }
    
    // Redis health
    const redisStatus = document.getElementById('redis-status');
    const redisClients = document.getElementById('redis-clients');
    const redisMemory = document.getElementById('redis-memory');
    
    if (health.redis) {
        redisStatus.className = `status-indicator ${health.redis.status === 'healthy' ? 'status-healthy' : 'status-error'}`;
        redisClients.textContent = health.redis.connected_clients || '-';
        redisMemory.textContent = health.redis.used_memory || '-';
    }
    
    // Email service health
    const emailStatus = document.getElementById('email-status');
    const emailQueueSize = document.getElementById('email-queue-size');
    const emailProcessingRate = document.getElementById('email-processing-rate');
    
    if (health.email) {
        emailStatus.className = `status-indicator ${health.email.status === 'healthy' ? 'status-healthy' : 'status-error'}`;
        emailQueueSize.textContent = health.email.queue_size || '0';
        emailProcessingRate.textContent = health.email.processing_rate || '-';
    }
}

// Initialize admin charts
function initializeAdminCharts() {
    // Email volume chart
    const emailVolumeCtx = document.getElementById('emailVolumeChart');
    if (emailVolumeCtx) {
        window.emailVolumeChart = new Chart(emailVolumeCtx, {
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
    
    // User growth chart
    const userGrowthCtx = document.getElementById('userGrowthChart');
    if (userGrowthCtx) {
        window.userGrowthChart = new Chart(userGrowthCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'New Users',
                    data: [],
                    backgroundColor: '#10b981',
                    borderColor: '#059669',
                    borderWidth: 1
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

// Update admin charts
function updateAdminCharts() {
    if (window.emailVolumeChart && adminStats.email_volume_trend) {
        const labels = adminStats.email_volume_trend.map(item => new Date(item.date).toLocaleDateString());
        const data = adminStats.email_volume_trend.map(item => item.count);
        
        window.emailVolumeChart.data.labels = labels;
        window.emailVolumeChart.data.datasets[0].data = data;
        window.emailVolumeChart.update();
    }
    
    if (window.userGrowthChart && adminStats.user_growth_trend) {
        const labels = adminStats.user_growth_trend.map(item => new Date(item.date).toLocaleDateString());
        const data = adminStats.user_growth_trend.map(item => item.count);
        
        window.userGrowthChart.data.labels = labels;
        window.userGrowthChart.data.datasets[0].data = data;
        window.userGrowthChart.update();
    }
}

// Admin view switching functions
function showOverview() {
    hideAllAdminViews();
    document.getElementById('overview-view').classList.remove('hidden');
    currentAdminView = 'overview';
    updateAdminNavigation();
}

function showUsers() {
    hideAllAdminViews();
    document.getElementById('users-view').classList.remove('hidden');
    currentAdminView = 'users';
    updateAdminNavigation();
    loadUsers();
}

function showEmails() {
    hideAllAdminViews();
    document.getElementById('emails-view').classList.remove('hidden');
    currentAdminView = 'emails';
    updateAdminNavigation();
    loadEmailLogs();
}

function showSystem() {
    hideAllAdminViews();
    document.getElementById('system-view').classList.remove('hidden');
    currentAdminView = 'system';
    updateAdminNavigation();
    loadSystemHealth();
}

function showAnalytics() {
    hideAllAdminViews();
    document.getElementById('analytics-view').classList.remove('hidden');
    currentAdminView = 'analytics';
    updateAdminNavigation();
    loadAnalytics();
}

function hideAllAdminViews() {
    document.querySelectorAll('[id$="-view"]').forEach(view => {
        view.classList.add('hidden');
    });
}

function updateAdminNavigation() {
    // Update navigation active states
    document.querySelectorAll('nav a').forEach(link => {
        link.classList.remove('text-indigo-600', 'border-b-2', 'border-indigo-600');
        link.classList.add('text-gray-900');
    });
    
    const activeLink = document.querySelector(`nav a[href="#${currentAdminView}"]`);
    if (activeLink) {
        activeLink.classList.remove('text-gray-900');
        activeLink.classList.add('text-indigo-600', 'border-b-2', 'border-indigo-600');
    }
}

// Users management functions
async function loadUsers() {
    try {
        const users = await KaleAPI.apiRequest('/dashboard/admin/users');
        displayUsers(users);
    } catch (error) {
        console.error('Failed to load users:', error);
        KaleAPI.showNotification('Failed to load users', 'error');
    }
}

function displayUsers(users) {
    const tbody = document.getElementById('users-table-body');
    if (!tbody) return;
    
    if (users.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="px-6 py-4 text-center text-gray-500">No users found</td>
            </tr>
        `;
        return;
    }
    
    const html = users.map(user => `
        <tr>
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                    <div class="flex-shrink-0 h-10 w-10">
                        <div class="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center">
                            <span class="text-sm font-medium text-indigo-800">${user.username.charAt(0).toUpperCase()}</span>
                        </div>
                    </div>
                    <div class="ml-4">
                        <div class="text-sm font-medium text-gray-900">${user.username}</div>
                        <div class="text-sm text-gray-500">${user.email}</div>
                    </div>
                </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    user.is_verified ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                }">
                    ${user.is_verified ? 'Verified' : 'Unverified'}
                </span>
                ${user.is_admin ? '<span class="ml-1 px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-purple-100 text-purple-800">Admin</span>' : ''}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                ${user.total_emails_sent || 0}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                ${user.last_active ? KaleAPI.formatDate(user.last_active) : 'Never'}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <button onclick="verifyUser(${user.id})" 
                        class="text-indigo-600 hover:text-indigo-900 mr-3"
                        ${user.is_verified ? 'disabled' : ''}>
                    ${user.is_verified ? 'Verified' : 'Verify'}
                </button>
                <button onclick="suspendUser(${user.id})" 
                        class="text-red-600 hover:text-red-900">
                    Suspend
                </button>
            </td>
        </tr>
    `).join('');
    
    tbody.innerHTML = html;
}

function refreshUsers() {
    loadUsers();
}

async function verifyUser(userId) {
    if (!confirm('Are you sure you want to verify this user?')) {
        return;
    }
    
    try {
        await KaleAPI.apiRequest(`/dashboard/admin/verify-user/${userId}`, {
            method: 'POST'
        });
        
        KaleAPI.showNotification('User verified successfully!', 'success');
        loadUsers();
        
    } catch (error) {
        console.error('Failed to verify user:', error);
        KaleAPI.showNotification(error.message || 'Failed to verify user', 'error');
    }
}

async function suspendUser(userId) {
    if (!confirm('Are you sure you want to suspend this user? This action can be undone.')) {
        return;
    }
    
    try {
        await KaleAPI.apiRequest(`/api/admin/users/${userId}/suspend`, {
            method: 'POST'
        });
        
        KaleAPI.showNotification('User suspended successfully!', 'success');
        loadUsers();
        
    } catch (error) {
        console.error('Failed to suspend user:', error);
        KaleAPI.showNotification(error.message || 'Failed to suspend user', 'error');
    }
}

// Email logs functions
async function loadEmailLogs() {
    try {
        const logs = await KaleAPI.apiRequest('/dashboard/admin/emails');
        displayEmailLogs(logs);
    } catch (error) {
        console.error('Failed to load email logs:', error);
        KaleAPI.showNotification('Failed to load email logs', 'error');
    }
}

function displayEmailLogs(logs) {
    const tbody = document.getElementById('emails-table-body');
    if (!tbody) return;
    
    if (logs.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="px-6 py-4 text-center text-gray-500">No email logs found</td>
            </tr>
        `;
        return;
    }
    
    const html = logs.map(log => `
        <tr>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                ${KaleAPI.formatDate(log.sent_at)}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                ${log.username || 'Unknown'}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                ${log.template_id}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                ${log.recipient_email}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    log.status === 'sent' ? 'bg-green-100 text-green-800' :
                    log.status === 'failed' ? 'bg-red-100 text-red-800' :
                    'bg-yellow-100 text-yellow-800'
                }">
                    ${log.status}
                </span>
            </td>
        </tr>
    `).join('');
    
    tbody.innerHTML = html;
}

function refreshEmailLogs() {
    loadEmailLogs();
}

// Analytics functions
async function loadAnalytics() {
    try {
        const analytics = await KaleAPI.apiRequest('/api/admin/analytics');
        displayAnalytics(analytics);
    } catch (error) {
        console.error('Failed to load analytics:', error);
        KaleAPI.showNotification('Failed to load analytics', 'error');
    }
}

function displayAnalytics(analytics) {
    // Update performance metrics
    document.getElementById('avg-response-time').textContent = `${analytics.avg_response_time || 0}ms`;
    document.getElementById('success-rate').textContent = `${analytics.success_rate || 0}%`;
    document.getElementById('error-rate').textContent = `${analytics.error_rate || 0}%`;
    document.getElementById('throughput').textContent = analytics.throughput || 0;
    
    // Initialize analytics charts
    initializeAnalyticsCharts(analytics);
}

function initializeAnalyticsCharts(analytics) {
    // API Usage Chart
    const apiUsageCtx = document.getElementById('apiUsageChart');
    if (apiUsageCtx && analytics.api_usage_by_endpoint) {
        new Chart(apiUsageCtx, {
            type: 'doughnut',
            data: {
                labels: analytics.api_usage_by_endpoint.map(item => item.endpoint),
                datasets: [{
                    data: analytics.api_usage_by_endpoint.map(item => item.count),
                    backgroundColor: [
                        '#4f46e5',
                        '#10b981',
                        '#f59e0b',
                        '#ef4444',
                        '#8b5cf6'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }
    
    // Template Usage Chart
    const templateUsageCtx = document.getElementById('templateUsageChart');
    if (templateUsageCtx && analytics.template_usage) {
        new Chart(templateUsageCtx, {
            type: 'bar',
            data: {
                labels: analytics.template_usage.map(item => item.template_id),
                datasets: [{
                    label: 'Usage Count',
                    data: analytics.template_usage.map(item => item.count),
                    backgroundColor: '#4f46e5'
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

// Logout function
function logout() {
    KaleAPI.logout();
}
