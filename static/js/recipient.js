/**
 * Recipient.js - Handles recipient dashboard functionality
 * Includes: Loading available food, viewing requests, creating requests
 */

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    loadRecipientData();
});

async function loadRecipientData() {
    // Verify authentication
    const authenticated = await verifyAuthentication();
    if (!authenticated) return;
    
    const recipientId = 1;
    
    // Load profile
    await loadRecipientProfile(recipientId);
    
    // Load available food
    await loadAvailableFood(recipientId);
    
    // Load recipient's requests
    await loadMyRequests(recipientId);
    
    // Setup modal
    setupRequestModal(recipientId);
}

// ============================================================================
// RECIPIENT PROFILE
// ============================================================================

function loadRecipientProfile(recipientId) {
    return fetchJson(`/api/recipient/available-food?recipient_id=${recipientId}`)
        .then(response => {
            const recipient = response.recipient;
            document.getElementById('recipient-name').textContent = recipient.name;
            const eligibility = document.getElementById('eligibility-status');
            eligibility.textContent = recipient.eligibility_status;
            eligibility.className = `status-badge status-${recipient.eligibility_status}`;
        })
        .catch(error => showError('Error loading profile: ' + error.message));
}

// ============================================================================
// AVAILABLE FOOD
// ============================================================================

async function loadAvailableFood(recipientId) {
    try {
        const response = await fetchJson(`/api/recipient/available-food?recipient_id=${recipientId}`);
        
        if (!response.success) {
            showError('Failed to load available food');
            return;
        }
        
        displayAvailableFood(response.available_food, recipientId);
    } catch (error) {
        showError('Error loading available food: ' + error.message);
    }
}

function displayAvailableFood(foodList, recipientId) {
    const container = document.getElementById('available-food-list');
    
    if (!foodList || foodList.length === 0) {
        container.innerHTML = '<p class="no-data">No available surplus food at this time</p>';
        return;
    }
    
    container.innerHTML = foodList.map((food, index) => `
        <div class="food-card">
            <h3>Surplus Food ${index + 1}</h3>
            <div class="food-details">
                <p><strong>Date:</strong> ${food.forecast_date}</p>
                <p><strong>Available Quantity:</strong> ${parseFloat(food.surplus_quantity).toFixed(2)} kg</p>
                <p><strong>Safety Status:</strong> 
                    <span class="status-badge status-${food.safety_status}">
                        ${food.safety_status.toUpperCase()}
                    </span>
                </p>
                <p><strong>Status:</strong> ${food.status}</p>
            </div>
            <button class="btn btn-primary" onclick="openRequestModal(${food.id}, ${food.surplus_quantity}, ${recipientId})">
                Request This Food
            </button>
        </div>
    `).join('');
}

// ============================================================================
// REQUEST MODAL
// ============================================================================

function openRequestModal(surplusId, availableQty, recipientId) {
    const modal = document.getElementById('request-modal');
    document.getElementById('modal-surplus-id').value = surplusId;
    document.getElementById('modal-recipient-id').value = recipientId;
    document.getElementById('modal-available-quantity').value = parseFloat(availableQty).toFixed(2);
    document.getElementById('request-quantity').value = '';
    document.getElementById('request-quantity').max = availableQty;
    modal.style.display = 'flex';
}

function setupRequestModal(recipientId) {
    const modal = document.getElementById('request-modal');
    const closeBtn = document.getElementById('close-modal');
    const requestForm = document.getElementById('request-form');
    
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }
    
    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // Form submission
    if (requestForm) {
        requestForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const surplusId = parseInt(document.getElementById('modal-surplus-id').value);
            const recId = parseInt(document.getElementById('modal-recipient-id').value);
            const quantity = parseFloat(document.getElementById('request-quantity').value);
            const maxQty = parseFloat(document.getElementById('modal-available-quantity').value);
            
            if (quantity > maxQty) {
                showError('Requested quantity exceeds available amount');
                return;
            }
            
            try {
                const response = await fetchJson('/api/recipient/request', {
                    method: 'POST',
                    body: JSON.stringify({
                        recipient_id: recId,
                        surplus_id: surplusId,
                        quantity: quantity
                    })
                });
                
                if (response.success) {
                    showSuccess('Request submitted successfully! Status: PENDING');
                    modal.style.display = 'none';
                    // Reload data
                    await loadAvailableFood(recipientId);
                    await loadMyRequests(recipientId);
                } else {
                    showError(response.error || 'Failed to submit request');
                }
            } catch (error) {
                showError('Error submitting request: ' + error.message);
            }
        });
    }
}

// ============================================================================
// MY REQUESTS
// ============================================================================

async function loadMyRequests(recipientId) {
    try {
        const response = await fetchJson(`/api/recipient/my-requests?recipient_id=${recipientId}`);
        
        if (!response.success) {
            showError('Failed to load your requests');
            return;
        }
        
        displayMyRequests(response.requests);
    } catch (error) {
        showError('Error loading requests: ' + error.message);
    }
}

function displayMyRequests(requests) {
    const tbody = document.querySelector('#my-requests-table tbody');
    
    if (!requests || requests.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="no-data">No requests yet</td></tr>';
        return;
    }
    
    tbody.innerHTML = requests.map(req => {
        const createdDate = new Date(req.created_at).toLocaleDateString();
        const updatedDate = new Date(req.updated_at).toLocaleDateString();
        
        return `
            <tr>
                <td>${req.id}</td>
                <td>${req.forecast_date}</td>
                <td>${parseFloat(req.quantity).toFixed(2)}</td>
                <td><span class="status-badge status-${req.status}">${req.status.toUpperCase()}</span></td>
                <td>${updatedDate}</td>
            </tr>
        `;
    }).join('');
}
