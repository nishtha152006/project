/**
 * Admin.js - Handles admin dashboard functionality
 * Includes: Loading data, rendering charts, approving requests, impact calculations
 */

let chartInstances = {};

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    loadAdminData();
});

async function loadAdminData() {
    // Verify authentication
    const authenticated = await verifyAuthentication();
    if (!authenticated) return;
    
    // Load all admin data
    await loadDashboardData();
    await loadChartData();
    await loadImpactMetrics();
}

// ============================================================================
// LOAD DASHBOARD DATA
// ============================================================================

async function loadDashboardData() {
    try {
        const response = await fetchJson('/api/admin/dashboard');
        
        if (!response.success) {
            showError('Failed to load dashboard data');
            return;
        }
        
        // Display latest surplus data
        if (response.latest_surplus) {
            const surplus = response.latest_surplus;
            document.getElementById('expected-attendance').textContent = surplus.expected_attendance || '-';
            document.getElementById('predicted-demand').textContent = 
                parseFloat(surplus.predicted_demand).toFixed(2) + ' kg';
            document.getElementById('recommended-quantity').textContent = 
                parseFloat(surplus.recommended_quantity).toFixed(2) + ' kg';
            document.getElementById('prepared-quantity').textContent = 
                parseFloat(surplus.prepared_quantity).toFixed(2) + ' kg';
            document.getElementById('consumed-quantity').textContent = 
                parseFloat(surplus.consumed_quantity).toFixed(2) + ' kg';
            document.getElementById('surplus-quantity').textContent = 
                parseFloat(surplus.surplus_quantity).toFixed(2) + ' kg';
            document.getElementById('storage-temperature').textContent = 
                parseFloat(surplus.storage_temperature).toFixed(1) + ' °C';
            document.getElementById('storage-time').textContent = surplus.storage_time || '-';
            
            const safetyStatusEl = document.getElementById('safety-status');
            safetyStatusEl.textContent = surplus.safety_status.toUpperCase();
            safetyStatusEl.className = 'status-value status-' + surplus.safety_status;
            
            document.getElementById('food-status').textContent = surplus.status;
        }
        
        // Display pending requests
        displayPendingRequests(response.pending_requests);

        const impact = response.impact || {};
        document.getElementById('food-saved').textContent = (impact.food_saved || 0).toFixed(2);
        document.getElementById('cost-saved').textContent = (impact.cost_saved || 0).toFixed(2);
        document.getElementById('carbon-saved').textContent = (impact.carbon_saved || 0).toFixed(2);

        const requestSummary = response.request_summary || {};
        document.getElementById('pending-request-count').textContent = requestSummary.pending || 0;
        document.getElementById('approved-request-count').textContent = requestSummary.approved || 0;
        document.getElementById('rejected-request-count').textContent = requestSummary.rejected || 0;
    } catch (error) {
        showError('Error loading dashboard: ' + error.message);
    }
}

// ============================================================================
// PENDING REQUESTS
// ============================================================================

function displayPendingRequests(requests) {
    const tbody = document.querySelector('#pending-requests-table tbody');
    
    if (!requests || requests.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="no-data">No pending requests</td></tr>';
        return;
    }
    
    tbody.innerHTML = requests.map(req => `
        <tr>
            <td>${req.id}</td>
            <td>${req.name}</td>
            <td>${parseFloat(req.quantity).toFixed(2)}</td>
            <td>${parseFloat(req.surplus_quantity).toFixed(2)}</td>
            <td><span class="status-badge status-${req.status}">${req.status.toUpperCase()}</span></td>
            <td>${new Date(req.created_at).toLocaleDateString()}</td>
            <td>
                <button class="btn btn-small btn-primary" onclick="approveRequest(${req.id})">
                    Approve
                </button>
            </td>
        </tr>
    `).join('');
}

async function approveRequest(requestId) {
    if (!confirm('Are you sure you want to approve this request?')) return;
    
    try {
        const response = await fetchJson('/api/admin/request/approve', {
            method: 'POST',
            body: JSON.stringify({ request_id: requestId })
        });
        
        if (response.success) {
            showSuccess('Request approved successfully!');
            // Reload data
            await loadDashboardData();
        } else {
            showError(response.error || 'Failed to approve request');
        }
    } catch (error) {
        showError('Error approving request: ' + error.message);
    }
}

// ============================================================================
// LOAD CHART DATA
// ============================================================================

async function loadChartData() {
    try {
        const response = await fetchJson('/api/admin/chart-data');
        
        if (!response.success) {
            showError('Failed to load chart data');
            return;
        }
        
        renderCharts(response);
    } catch (error) {
        showError('Error loading chart data: ' + error.message);
    }
}

function renderCharts(data) {
    // Check if we have data
    if (!data.dates || data.dates.length === 0) {
        showChartPlaceholder('demand-chart');
        showChartPlaceholder('surplus-chart');
        showChartPlaceholder('redistribution-chart');
        renderRequestsChart(data);
        return;
    }
    
    // Chart 1: Predicted vs Actual vs Consumed
    renderDemandChart(data);
    
    // Chart 2: Surplus Over Time
    renderSurplusChart(data);
    
    // Chart 3: Request Status
    renderRequestsChart(data);
    
    // Chart 4: Redistribution Impact
    renderRedistributionChart(data);
}

function renderDemandChart(data) {
    destroyChartIfExists('demandChart');
    
    const ctx = document.getElementById('demand-chart');
    if (!ctx) return;
    
    chartInstances.demandChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [
                {
                    label: 'Predicted Demand',
                    data: data.predicted_demand,
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.4,
                    fill: false
                },
                {
                    label: 'Prepared Quantity',
                    data: data.prepared_quantity,
                    borderColor: '#27ae60',
                    backgroundColor: 'rgba(39, 174, 96, 0.1)',
                    tension: 0.4,
                    fill: false
                },
                {
                    label: 'Consumed Quantity',
                    data: data.consumed_quantity,
                    borderColor: '#e74c3c',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    tension: 0.4,
                    fill: false
                },
                {
                    label: 'Surplus Quantity',
                    data: data.surplus_quantity,
                    borderColor: '#f39c12',
                    backgroundColor: 'rgba(243, 156, 18, 0.1)',
                    tension: 0.4,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { position: 'top' }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

function renderSurplusChart(data) {
    destroyChartIfExists('surplusChart');
    
    const ctx = document.getElementById('surplus-chart');
    if (!ctx) return;
    
    chartInstances.surplusChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.dates,
            datasets: [{
                label: 'Surplus Quantity (kg)',
                data: data.surplus_quantity,
                backgroundColor: '#f39c12',
                borderColor: '#e67e22',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { position: 'top' }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

function renderRequestsChart(data) {
    destroyChartIfExists('requestsChart');
    
    const ctx = document.getElementById('requests-chart');
    if (!ctx) return;
    
    const labels = Object.keys(data.request_status);
    const values = Object.values(data.request_status);
    
    chartInstances.requestsChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels.map(l => l.charAt(0).toUpperCase() + l.slice(1)),
            datasets: [{
                data: values,
                backgroundColor: [
                    '#3498db',
                    '#27ae60',
                    '#e74c3c'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

function renderRedistributionChart(data) {
    destroyChartIfExists('redistributionChart');
    
    const ctx = document.getElementById('redistribution-chart');
    if (!ctx) return;
    
    chartInstances.redistributionChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Redistributed (Approved)', 'Total Surplus'],
            datasets: [{
                label: 'Quantity (kg)',
                data: [
                    data.total_redistributed,
                    data.surplus_quantity.reduce((a, b) => a + b, 0)
                ],
                backgroundColor: [
                    '#27ae60',
                    '#95a5a6'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { position: 'top' }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

function destroyChartIfExists(chartName) {
    if (chartInstances[chartName]) {
        chartInstances[chartName].destroy();
        delete chartInstances[chartName];
    }
}

function showChartPlaceholder(elementId) {
    const ctx = document.getElementById(elementId);
    if (ctx) {
        ctx.parentElement.innerHTML = '<p class="no-data-message">No data available yet</p>';
    }
}

// ============================================================================
// LOAD IMPACT METRICS
// ============================================================================

async function loadImpactMetrics() {
    try {
        const response = await fetchJson('/api/impact/calculations');
        
        if (response.success) {
            document.getElementById('food-saved').textContent = 
                parseFloat(response.food_saved).toFixed(2);
            document.getElementById('cost-saved').textContent = 
                parseFloat(response.cost_saved).toFixed(2);
            document.getElementById('carbon-saved').textContent = 
                parseFloat(response.carbon_saved).toFixed(2);
        }
    } catch (error) {
        console.error('Error loading impact metrics:', error);
    }
}
