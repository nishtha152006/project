/**
 * Login.js - Handles login page functionality
 */

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const errorMessage = document.getElementById('error-message');
    
    if (!loginForm) return;
    
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value.trim();
        
        // Clear error
        errorMessage.style.display = 'none';
        
        if (!username || !password) {
            showLoginError('Please enter both username and password');
            return;
        }
        
        try {
            const response = await fetchJson('/api/login', {
                method: 'POST',
                body: JSON.stringify({ username, password })
            });
            
            if (response.success) {
                // Redirect to appropriate dashboard
                window.location.href = `/dashboard/${response.role}`;
            } else {
                showLoginError(response.error || 'Login failed');
            }
        } catch (error) {
            showLoginError('Invalid username or password');
        }
    });
    
    function showLoginError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
    }
});

/**
 * Fetch function for login page
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
        console.error('Login Error:', error);
        throw error;
    }
}
