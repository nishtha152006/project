/**
 * Kitchen.js - Handles kitchen dashboard functionality
 * Includes: Calendar, Location, Form submission, Data display
 */

let selectedCalendarDate = null;
let calendarDate = new Date();

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    loadKitchenData();
});

async function loadKitchenData() {
    // Verify authentication
    const authenticated = await verifyAuthentication();
    if (!authenticated) return;
    
    // Build the form and UI
    buildKitchenForm();
    
    // Setup calendar - must be after HTML exists
    setupCalendar();
    
    // Setup location
    setupLocation();
    
    // Load latest data
    await loadLatestRecord();
}

// ============================================================================
// KITCHEN FORM HANDLING
// ============================================================================

function buildKitchenForm() {
    // Form is already in HTML, just set up event listeners
    const kitchenForm = document.getElementById('kitchen-form');
    if (!kitchenForm) return;
    
    kitchenForm.addEventListener('submit', handleKitchenFormSubmit);
    
    // Auto-calculate demand when forecast inputs change
    const attendanceInput = document.getElementById('expected-attendance');
    const weatherSelect = document.getElementById('weather-conditions');
    const eventSelect = document.getElementById('event-type');
    
    if (attendanceInput) attendanceInput.addEventListener('change', calculateAndDisplayDemand);
    if (weatherSelect) weatherSelect.addEventListener('change', calculateAndDisplayDemand);
    if (eventSelect) eventSelect.addEventListener('change', calculateAndDisplayDemand);
}

function calculateAndDisplayDemand() {
    const attendance = parseFloat(document.getElementById('expected-attendance').value) || 0;
    const weather = document.getElementById('weather-conditions').value;
    const event = document.getElementById('event-type').value;
    
    if (!attendance || !weather || !event) return;
    
    // Client-side calculation (matches backend logic)
    const attendanceFactor = 1.2;
    const weatherFactors = {
        'sunny': 0.9,
        'cloudy': 1.0,
        'rainy': 1.1,
        'cold': 1.2,
        'hot': 0.8
    };
    const eventFactors = {
        'regular': 1.0,
        'festival': 1.5,
        'exam': 1.2,
        'holiday': 0.8,
        'special': 1.4
    };
    
    const weatherFactor = weatherFactors[weather] || 1.0;
    const eventFactor = eventFactors[event] || 1.0;
    
    const predictedDemand = attendance * attendanceFactor * weatherFactor * eventFactor;
    const recommendedQuantity = predictedDemand * 1.15; // 15% safety margin
    
    document.getElementById('predicted-demand').value = predictedDemand.toFixed(2);
    document.getElementById('recommended-quantity').value = recommendedQuantity.toFixed(2);
}

async function handleKitchenFormSubmit(e) {
    e.preventDefault();
    
    const formData = {
        forecast_date: document.getElementById('forecast-date').value,
        expected_attendance: parseInt(document.getElementById('expected-attendance').value),
        weather_conditions: document.getElementById('weather-conditions').value,
        event_type: document.getElementById('event-type').value,
        predicted_demand: parseFloat(document.getElementById('predicted-demand').value),
        recommended_quantity: parseFloat(document.getElementById('recommended-quantity').value),
        prepared_quantity: parseFloat(document.getElementById('prepared-quantity').value),
        consumed_quantity: parseFloat(document.getElementById('consumed-quantity').value),
        storage_time: document.getElementById('storage-time').value,
        storage_temperature: parseFloat(document.getElementById('storage-temperature').value)
    };
    
    // Validate
    if (!formData.forecast_date || !formData.expected_attendance || !formData.weather_conditions ||
        !formData.event_type || !formData.prepared_quantity || !formData.consumed_quantity ||
        !formData.storage_time || !formData.storage_temperature) {
        showError('Please fill all required fields');
        return;
    }
    
    try {
        const response = await fetchJson('/api/kitchen/surplus', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
        
        if (response.success) {
            showSuccess('Kitchen data saved successfully!');
            await loadLatestRecord();
        } else {
            showError(response.error || 'Failed to save data');
        }
    } catch (error) {
        showError('Error saving kitchen data: ' + error.message);
    }
}

// ============================================================================
// LOAD LATEST RECORD
// ============================================================================

async function loadLatestRecord() {
    try {
        const response = await fetchJson('/api/kitchen/latest');
        
        if (!response.success) {
            document.getElementById('latest-record').innerHTML = '<p>No records yet</p>';
            return;
        }
        
        if (!response.forecast || !response.surplus) {
            document.getElementById('latest-record').innerHTML = '<p>No records yet</p>';
            return;
        }
        
        const forecast = response.forecast;
        const surplus = response.surplus;

        document.getElementById('forecast-date').value = forecast.forecast_date;
        document.getElementById('expected-attendance').value = forecast.expected_attendance;
        document.getElementById('weather-conditions').value = forecast.weather_conditions;
        document.getElementById('event-type').value = forecast.event_type;
        document.getElementById('predicted-demand').value = parseFloat(forecast.predicted_demand).toFixed(2);
        document.getElementById('recommended-quantity').value = parseFloat(forecast.recommended_quantity).toFixed(2);
        document.getElementById('prepared-quantity').value = surplus.prepared_quantity;
        document.getElementById('consumed-quantity').value = surplus.consumed_quantity;
        document.getElementById('storage-time').value = surplus.storage_time;
        document.getElementById('storage-temperature').value = surplus.storage_temperature;
        selectedCalendarDate = forecast.forecast_date;
        calendarDate = new Date(`${forecast.forecast_date}T00:00:00`);
        renderCalendar();
        
        const html = `
            <div class="record-card">
                <h3>Date: ${forecast.forecast_date}</h3>
                <div class="record-grid">
                    <div class="record-item">
                        <strong>Expected Attendance:</strong>
                        <p>${forecast.expected_attendance} people</p>
                    </div>
                    <div class="record-item">
                        <strong>Weather:</strong>
                        <p>${forecast.weather_conditions}</p>
                    </div>
                    <div class="record-item">
                        <strong>Event Type:</strong>
                        <p>${forecast.event_type}</p>
                    </div>
                </div>
                <div class="record-grid">
                    <div class="record-item">
                        <strong>Predicted Demand:</strong>
                        <p>${parseFloat(forecast.predicted_demand).toFixed(2)} kg</p>
                    </div>
                    <div class="record-item">
                        <strong>Recommended Qty:</strong>
                        <p>${parseFloat(forecast.recommended_quantity).toFixed(2)} kg</p>
                    </div>
                </div>
                <div class="record-grid">
                    <div class="record-item">
                        <strong>Prepared Quantity:</strong>
                        <p>${parseFloat(surplus.prepared_quantity).toFixed(2)} kg</p>
                    </div>
                    <div class="record-item">
                        <strong>Consumed Quantity:</strong>
                        <p>${parseFloat(surplus.consumed_quantity).toFixed(2)} kg</p>
                    </div>
                    <div class="record-item">
                        <strong>Surplus Quantity:</strong>
                        <p class="highlight">${parseFloat(surplus.surplus_quantity).toFixed(2)} kg</p>
                    </div>
                </div>
                <div class="record-grid">
                    <div class="record-item">
                        <strong>Storage Temperature:</strong>
                        <p>${parseFloat(surplus.storage_temperature).toFixed(1)} °C</p>
                    </div>
                    <div class="record-item">
                        <strong>Food Safety:</strong>
                        <p class="${surplus.safety_status === 'safe' ? 'status-safe' : 'status-unsafe'}">
                            ${surplus.safety_status.toUpperCase()}
                        </p>
                    </div>
                    <div class="record-item">
                        <strong>Status:</strong>
                        <p>${surplus.status}</p>
                    </div>
                </div>
            </div>
        `;
        
        document.getElementById('latest-record').innerHTML = html;
    } catch (error) {
        console.error('Error loading latest record:', error);
        document.getElementById('latest-record').innerHTML = '<p>Error loading records</p>';
    }
}

// ============================================================================
// CALENDAR
// ============================================================================

function setupCalendar() {
    const prevBtn = document.getElementById('prev-month-btn');
    const nextBtn = document.getElementById('next-month-btn');
    
    if (prevBtn) prevBtn.addEventListener('click', () => {
        calendarDate.setMonth(calendarDate.getMonth() - 1);
        renderCalendar();
    });
    
    if (nextBtn) nextBtn.addEventListener('click', () => {
        calendarDate.setMonth(calendarDate.getMonth() + 1);
        renderCalendar();
    });
    
    // Initial render
    renderCalendar();
}

function renderCalendar() {
    const year = calendarDate.getFullYear();
    const month = calendarDate.getMonth();
    
    // Update header
    const monthYear = calendarDate.toLocaleString('default', { month: 'long', year: 'numeric' });
    document.getElementById('calendar-month-year').textContent = monthYear;
    
    // Get first day of month and number of days
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const today = new Date();
    
    // Clear and render dates
    const datesContainer = document.getElementById('calendar-dates');
    datesContainer.innerHTML = '';
    
    // Empty cells for days before month starts
    for (let i = 0; i < firstDay; i++) {
        const emptyCell = document.createElement('div');
        emptyCell.className = 'calendar-date empty';
        datesContainer.appendChild(emptyCell);
    }
    
    // Days of month
    for (let day = 1; day <= daysInMonth; day++) {
        const dateCell = document.createElement('button');
        dateCell.className = 'calendar-date';
        dateCell.textContent = day;
        dateCell.type = 'button';
        
        const cellDate = new Date(year, month, day);
        const dateStr = cellDate.toISOString().split('T')[0];
        
        // Mark today
        if (cellDate.toDateString() === today.toDateString()) {
            dateCell.classList.add('today');
        }
        
        // Mark selected
        if (selectedCalendarDate === dateStr) {
            dateCell.classList.add('selected');
        }
        
        // Click handler
        dateCell.addEventListener('click', () => {
            selectedCalendarDate = dateStr;
            document.getElementById('forecast-date').value = dateStr;
            renderCalendar(); // Re-render to show selection
        });
        
        datesContainer.appendChild(dateCell);
    }
}

// ============================================================================
// LOCATION
// ============================================================================

function setupLocation() {
    const locationBtn = document.getElementById('location-btn');
    if (!locationBtn) return;
    
    locationBtn.addEventListener('click', () => {
        if (!navigator.geolocation) {
            showError('Geolocation is not supported by your browser');
            return;
        }
        
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const { latitude, longitude } = position.coords;
                
                document.getElementById('latitude').textContent = latitude.toFixed(6);
                document.getElementById('longitude').textContent = longitude.toFixed(6);
                document.getElementById('location-info').style.display = 'block';
                document.getElementById('location-error').style.display = 'none';
                
                // Embed OpenStreetMap
                const mapUrl = `https://www.openstreetmap.org/export/embed.html?bbox=${longitude-0.01},${latitude-0.01},${longitude+0.01},${latitude+0.01}&layer=mapnik&marker=${latitude},${longitude}`;
                document.getElementById('map-frame').src = mapUrl;
            },
            (error) => {
                const errorMsg = error.code === 1 ? 'Location permission denied' : 'Unable to get your location';
                document.getElementById('location-error').textContent = errorMsg;
                document.getElementById('location-error').style.display = 'block';
            }
        );
    });
}
