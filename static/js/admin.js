/**
 * Admin Dashboard JavaScript for Kale Email API Platform
 * Production-ready admin functionality for monitoring and management
 */

'use strict';

// Admin state management
let currentTab = 'overview';
let adminStats = {};
let usersData = [];
let emailLogsData = [];
let systemHealthData = {};
let analyticsData = {};
let charts = {};

// Initialize admin dashboard
document.addEventListener('DOMContentLoaded', function() {
    if (!KaleAPI.checkAuthentication()) {
        window.location.href = '/login';
        return;
    }
    
    initializeAdminDashboard();
});

// Main initialization function
function initializeAdminDashboard() {
    setupEventListeners();
    loadAdminInfo();
    loadOverviewData();
    updateLastUpdated();
}

// Set up all event listeners
function setupEventListeners() {
    // Tab navigation
    document.querySelectorAll('[data-tab]').forEach(button => {
        button.addEventListener('click', handleTabClick);
    });
    
    // Logout functionality
    document.querySelectorAll('[data-action="logout"]').forEach(button => {
        button.addEventListener('click', KaleAPI.logout);
    });
    
    // Email logs refresh
    const refreshButton = document.querySelector('[data-action="refresh-email-logs"]');
    if (refreshButton) {
        refreshButton.addEventListener('click', refreshEmailLogs);
    }
    
    // User menu toggle
    const userMenuButton = document.getElementById('user-menu-button');
    const userMenu = document.getElementById('user-menu');
    if (userMenuButton && userMenu) {
        userMenuButton.addEventListener('click', function(e) {
            e.stopPropagation();
            userMenu.classList.toggle('hidden');
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function() {
            userMenu.classList.add('hidden');
        });
    }
    
    // Email status filter
    const statusFilter = document.getElementById('email-status-filter');
    if (statusFilter) {
        statusFilter.addEventListener('change', handleStatusFilterChange);
    }
    
    // Auto-refresh data every 30 seconds
    setInterval(refreshDashboardData, 30000);
}

// Handle tab clicks
function handleTabClick(e) {
    const tabName = e.target.dataset.tab;
    if (tabName) {
        switchTab(tabName);
    }
}

// Switch between admin tabs
function switchTab(tabName) {
    if (currentTab === tabName) return;
    
    // Update navigation
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // Hide all tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
        content.style.display = 'none';
    });
    
    // Show selected tab content
    const targetTab = document.getElementById(`${tabName}-tab`) || document.getElementById(`${tabName}-view`);
    if (targetTab) {
        targetTab.classList.add('active');
        targetTab.style.display = 'block';
    }
    
    currentTab = tabName;
    
    // Load tab-specific data
    loadTabData(tabName);
}

// Load data for specific tab
async function loadTabData(tabName) {
    try {
        KaleAPI.showLoading(document.body);
        
        switch (tabName) {
            case 'overview':
                await loadOverviewData();
                break;
            case 'users':
                await loadUsersData();
                break;
            case 'emails':
                await loadEmailLogsData();
                break;
            case 'system':
                await loadSystemHealthData();
                break;
            case 'analytics':
                await loadAnalyticsData();
                break;
        }
    } catch (error) {
        KaleAPI.showNotification('Failed to load tab data', 'error');
    } finally {
        KaleAPI.hideLoading(document.body);
    }
}

// Load admin user information
async function loadAdminInfo() {
    try {
        const user = await KaleAPI.apiRequest('/auth/me');
        if (user && user.is_admin) {
            const adminInfo = document.getElementById('admin-info');
            if (adminInfo) {
                adminInfo.textContent = `Admin: ${user.username}`;
            }
        } else {
            KaleAPI.showNotification('Admin access required', 'error');
            setTimeout(() => window.location.href = '/dashboard', 1500);
        }
    } catch (error) {
        KaleAPI.showNotification('Failed to load admin info', 'error');
        window.location.href = '/login';
    }
}

// Load overview dashboard data
async function loadOverviewData() {
    try {
        const stats = await KaleAPI.apiRequest('/admin/stats/');
        adminStats = stats;
        updateOverviewStats(stats);
        
        // Load charts data
        const analyticsData = await KaleAPI.apiRequest('/admin/analytics?days=7');
        updateOverviewCharts(analyticsData);
    } catch (error) {
        KaleAPI.showNotification('Failed to load overview data', 'error');
    }
}

// Update overview statistics display
function updateOverviewStats(stats) {
    const elements = {
        'total-users': stats.total_users || 0,
        'verified-users': stats.verified_users || 0,
        'emails-today': stats.emails_today || 0,
        'active-users-today': stats.active_users_today || 0
    };
    
    Object.entries(elements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = KaleAPI.formatNumber(value);
        }
    });
}

// Update overview charts
function updateOverviewCharts(data) {
    // Email Volume Chart
    updateEmailVolumeChart(data.email_volume || []);
    
    // User Growth Chart
    updateUserGrowthChart(data.user_growth || []);
}

// Update email volume chart
function updateEmailVolumeChart(data) {
    const ctx = document.getElementById('emailVolumeChart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (charts.emailVolume) {
        charts.emailVolume.destroy();
    }
    
    charts.emailVolume = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(item => KaleAPI.formatDate(item.date)),
            datasets: [{
                label: 'Emails Sent',
                data: data.map(item => item.count),
                borderColor: '#4f46e5',
                backgroundColor: 'rgba(79, 70, 229, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Update user growth chart
function updateUserGrowthChart(data) {
    const ctx = document.getElementById('userGrowthChart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (charts.userGrowth) {
        charts.userGrowth.destroy();
    }
    
    charts.userGrowth = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(item => KaleAPI.formatDate(item.date)),
            datasets: [{
                label: 'New Users',
                data: data.map(item => item.count),
                backgroundColor: '#06b6d4',
                borderRadius: 4,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Load users management data
async function loadUsersData() {
    try {
        const users = await KaleAPI.apiRequest('/admin/users');
        usersData = users.users || [];
        displayUsersTable(usersData);
    } catch (error) {
        KaleAPI.showNotification('Failed to load users data', 'error');
    }
}

// Display users in table
function displayUsersTable(users) {
    const tbody = document.getElementById('users-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = users.map(user => `
        <tr class="hover:bg-gray-50">
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">${user.username}</div>
                <div class="text-sm text-gray-500">${user.email}</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${user.is_verified ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}">
                    ${user.is_verified ? 'Verified' : 'Unverified'}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                ${user.email_count || 0}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                ${user.last_login ? KaleAPI.formatDate(user.last_login) : 'Never'}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <button data-action="view-user" data-user-id="${user.id}" 
                        class="text-indigo-600 hover:text-indigo-900 mr-3">View</button>
                <button data-action="verify-user" data-user-id="${user.id}" 
                        class="text-green-600 hover:text-green-900 mr-3 ${user.is_verified ? 'hidden' : ''}">Verify</button>
                <button data-action="suspend-user" data-user-id="${user.id}" 
                        class="text-red-600 hover:text-red-900">Suspend</button>
            </td>
        </tr>
    `).join('');
    
    // Add event listeners for user actions
    tbody.querySelectorAll('[data-action]').forEach(button => {
        button.addEventListener('click', handleUserAction);
    });
}

// Handle user actions
async function handleUserAction(e) {
    e.preventDefault();
    const action = e.target.dataset.action;
    const userId = e.target.dataset.userId;
    
    try {
        switch (action) {
            case 'view-user':
                await viewUserDetails(userId);
                break;
            case 'verify-user':
                await verifyUser(userId);
                break;
            case 'suspend-user':
                await suspendUser(userId);
                break;
        }
    } catch (error) {
        KaleAPI.showNotification(`Failed to ${action.replace('-', ' ')}`, 'error');
    }
}

// View user details
async function viewUserDetails(userId) {
    try {
        const user = await KaleAPI.apiRequest(`/admin/users/${userId}`);
        // This would open a modal or navigate to user details page
        KaleAPI.showNotification(`Viewing details for ${user.username}`, 'info');
    } catch (error) {
        KaleAPI.showNotification('Failed to load user details', 'error');
    }
}

// Verify user
async function verifyUser(userId) {
    try {
        await KaleAPI.apiRequest(`/admin/users/${userId}/verify`, { method: 'POST' });
        KaleAPI.showNotification('User verified successfully', 'success');
        await loadUsersData(); // Reload users list
    } catch (error) {
        KaleAPI.showNotification('Failed to verify user', 'error');
    }
}

// Suspend user
async function suspendUser(userId) {
    if (!confirm('Are you sure you want to suspend this user?')) {
        return;
    }
    
    try {
        await KaleAPI.apiRequest(`/admin/users/${userId}/suspend`, { method: 'POST' });
        KaleAPI.showNotification('User suspended successfully', 'success');
        await loadUsersData(); // Reload users list
    } catch (error) {
        KaleAPI.showNotification('Failed to suspend user', 'error');
    }
}

// Load email logs data
async function loadEmailLogsData() {
    try {
        const logs = await KaleAPI.apiRequest('/admin/email-logs');
        emailLogsData = logs.logs || [];
        displayEmailLogsTable(emailLogsData);
    } catch (error) {
        KaleAPI.showNotification('Failed to load email logs', 'error');
    }
}

// Display email logs in table
function displayEmailLogsTable(logs) {
    const tbody = document.getElementById('emails-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = logs.map(log => `
        <tr class="hover:bg-gray-50">
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                ${KaleAPI.formatDate(log.sent_at)}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">${log.username}</div>
                <div class="text-sm text-gray-500">${log.user_email}</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                ${log.template_id}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                ${log.recipient_email}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(log.status)}">
                    ${log.status}
                </span>
            </td>
        </tr>
    `).join('');
}

// Get status color for email logs
function getStatusColor(status) {
    switch (status.toLowerCase()) {
        case 'sent':
        case 'delivered':
            return 'bg-green-100 text-green-800';
        case 'failed':
        case 'bounced':
            return 'bg-red-100 text-red-800';
        case 'pending':
            return 'bg-yellow-100 text-yellow-800';
        default:
            return 'bg-gray-100 text-gray-800';
    }
}

// Refresh email logs
async function refreshEmailLogs() {
    await loadEmailLogsData();
    KaleAPI.showNotification('Email logs refreshed', 'success');
}

// Handle status filter change
async function handleStatusFilterChange(e) {
    const status = e.target.value;
    try {
        const logs = await KaleAPI.apiRequest(`/admin/email-logs${status ? `?status=${status}` : ''}`);
        emailLogsData = logs.logs || [];
        displayEmailLogsTable(emailLogsData);
    } catch (error) {
        KaleAPI.showNotification('Failed to filter email logs', 'error');
    }
}

// Load system health data
async function loadSystemHealthData() {
    try {
        const health = await KaleAPI.apiRequest('/admin/system-health');
        systemHealthData = health;
        updateSystemHealthDisplay(health);
    } catch (error) {
        KaleAPI.showNotification('Failed to load system health data', 'error');
    }
}

// Update system health display
function updateSystemHealthDisplay(health) {
    // Database status
    updateHealthIndicator('db-status', health.database?.status);
    updateHealthValue('db-pool-size', health.database?.pool_size || '-');
    updateHealthValue('db-active-connections', health.database?.active_connections || '-');
    
    // Redis status
    updateHealthIndicator('redis-status', health.redis?.status);
    updateHealthValue('redis-clients', health.redis?.connected_clients || '-');
    updateHealthValue('redis-memory', health.redis?.memory_used || '-');
    
    // Email service status
    updateHealthIndicator('email-status', health.email_service?.status);
    updateHealthValue('email-queue-size', health.email_service?.queue_size || '-');
    updateHealthValue('email-processing-rate', health.email_service?.processing_rate || '-');
}

// Update health indicator
function updateHealthIndicator(elementId, status) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    // Remove existing status classes
    element.classList.remove('status-healthy', 'status-warning', 'status-error');
    
    // Add appropriate status class
    switch (status?.toLowerCase()) {
        case 'healthy':
        case 'ok':
            element.classList.add('status-healthy');
            break;
        case 'warning':
            element.classList.add('status-warning');
            break;
        case 'error':
        case 'failed':
            element.classList.add('status-error');
            break;
        default:
            element.classList.add('status-warning');
    }
}

// Update health value
function updateHealthValue(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    }
}

// Load analytics data
async function loadAnalyticsData() {
    try {
        const analytics = await KaleAPI.apiRequest('/admin/analytics?days=30');
        analyticsData = analytics;
        updateAnalyticsDisplay(analytics);
    } catch (error) {
        KaleAPI.showNotification('Failed to load analytics data', 'error');
    }
}

// Update analytics display
function updateAnalyticsDisplay(analytics) {
    // Update performance metrics
    updateAnalyticsValue('avg-response-time', analytics.performance?.avg_response_time || '-');
    updateAnalyticsValue('success-rate', analytics.performance?.success_rate || '-');
    updateAnalyticsValue('error-rate', analytics.performance?.error_rate || '-');
    updateAnalyticsValue('throughput', analytics.performance?.throughput || '-');
    
    // Update charts
    updateAPIUsageChart(analytics.api_usage || []);
    updateTemplateUsageChart(analytics.template_usage || []);
}

// Update analytics value
function updateAnalyticsValue(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    }
}

// Update API usage chart
function updateAPIUsageChart(data) {
    const ctx = document.getElementById('apiUsageChart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (charts.apiUsage) {
        charts.apiUsage.destroy();
    }
    
    charts.apiUsage = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(item => item.endpoint),
            datasets: [{
                data: data.map(item => item.count),
                backgroundColor: [
                    '#4f46e5',
                    '#06b6d4',
                    '#10b981',
                    '#f59e0b',
                    '#ef4444'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Update template usage chart
function updateTemplateUsageChart(data) {
    const ctx = document.getElementById('templateUsageChart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (charts.templateUsage) {
        charts.templateUsage.destroy();
    }
    
    charts.templateUsage = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(item => item.template_name),
            datasets: [{
                label: 'Usage Count',
                data: data.map(item => item.count),
                backgroundColor: '#06b6d4',
                borderRadius: 4,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                },
                y: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Refresh all dashboard data
async function refreshDashboardData() {
    try {
        await loadTabData(currentTab);
        updateLastUpdated();
    } catch (error) {
        // Silent refresh failure
    }
}

// Update last updated timestamp
function updateLastUpdated() {
    const element = document.getElementById('last-updated');
    if (element) {
        element.textContent = new Date().toLocaleTimeString();
    }
}

// Export functions for external use
window.AdminDashboard = {
    switchTab,
    refreshEmailLogs,
    loadTabData,
    refreshDashboardData
};