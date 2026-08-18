/**
 * Common.js - Shared functions for all dashboards
 * Contains: fetchJson, showError, showSuccess, getDetectedRole, etc.
 */

// ============================================================================
// API COMMUNICATION
// ============================================================================

/**
 * Universal fetch wrapper for JSON APIs
 * Handles errors and response parsing
 */
async function fetchJson(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ============================================================================
// ROLE DETECTION & AUTH
// ============================================================================

let detectedRole = null;

/**
 * Get the current user's role from session
 */
async function getDetectedRole() {
    if (detectedRole) return detectedRole;
    
    try {
        const result = await fetchJson('/api/verify-session');
        detectedRole = result.role;
        return detectedRole;
    } catch (error) {
        console.error('Session verification failed:', error);
        return null;
    }
}

/**
 * Verify user is logged in and redirect if not
 */
async function verifyAuthentication() {
    try {
        const result = await fetchJson('/api/verify-session');
        if (!result.authenticated) {
            window.location.href = '/';
            return false;
        }
        return true;
    } catch (error) {
        window.location.href = '/';
        return false;
    }
}

// ============================================================================
// ERROR & SUCCESS HANDLING
// ============================================================================

/**
 * Display error message in the dashboard
 */
function showError(message) {
    const errorElement = document.getElementById('error-message');
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            errorElement.style.display = 'none';
        }, 5000);
    }
    console.error('Error:', message);
}

/**
 * Display success message in the dashboard
 */
function showSuccess(message) {
    const successElement = document.getElementById('success-message');
    if (successElement) {
        successElement.textContent = message;
        successElement.style.display = 'block';
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            successElement.style.display = 'none';
        }, 3000);
    }
}

// ============================================================================
// LOGOUT
// ============================================================================

/**
 * Handle logout for all dashboards
 */
async function handleLogout() {
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async () => {
            try {
                await fetchJson('/api/logout', { method: 'POST' });
                window.location.href = '/';
            } catch (error) {
                console.error('Logout error:', error);
                window.location.href = '/';
            }
        });
    }
}

// ============================================================================
// INITIALIZATION
// ============================================================================

/**
 * Global initialization that runs on all pages
 */
document.addEventListener('DOMContentLoaded', () => {
    verifyAuthentication();
    handleLogout();
});
