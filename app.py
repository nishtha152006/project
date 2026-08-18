"""Main Flask application for Rupee - Food Demand Forecasting System."""

import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect
from werkzeug.security import check_password_hash, generate_password_hash
from database import init_db, get_connection, query_db, execute_db

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'rupee-dev-secret-key-change-in-production')

# Initialize database on app startup
with app.app_context():
    init_db()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_db():
    """Get database connection."""
    return get_connection()


COST_PER_KG = 50
CARBON_PER_KG = 0.5


def calculate_impact_metrics():
    """Calculate impact from quantities in approved recipient requests."""
    redistributed = query_db('''
        SELECT COALESCE(SUM(quantity), 0) AS total
        FROM recipient_requests
        WHERE status = 'approved'
    ''', one=True)
    food_saved = float(redistributed['total']) if redistributed else 0
    return {
        'food_saved': round(food_saved, 2),
        'cost_saved': round(food_saved * COST_PER_KG, 2),
        'carbon_saved': round(food_saved * CARBON_PER_KG, 2)
    }

def calculate_demand_forecast(expected_attendance, weather_conditions, event_type, historical_factor=1.0):
    """
    Calculate predicted meal demand.
    
    Formula: predicted_demand = expected_attendance × attendance_factor × weather_factor × event_factor × historical_factor
    
    Factors:
    - Attendance factor: 1.2 (each person consumes ~1.2 portions on average)
    - Weather factor: 0.8-1.2 (affects appetite)
    - Event factor: 0.9-1.5 (special events increase demand)
    - Historical factor: customizable based on past data
    """
    
    # Attendance factor
    attendance_factor = 1.2
    
    # Weather factor
    weather_factors = {
        'sunny': 0.9,
        'cloudy': 1.0,
        'rainy': 1.1,
        'cold': 1.2,
        'hot': 0.8
    }
    weather_factor = weather_factors.get(weather_conditions.lower(), 1.0)
    
    # Event factor
    event_factors = {
        'regular': 1.0,
        'festival': 1.5,
        'exam': 1.2,
        'holiday': 0.8,
        'special': 1.4
    }
    event_factor = event_factors.get(event_type.lower(), 1.0)
    
    # Calculate predicted demand
    predicted_demand = expected_attendance * attendance_factor * weather_factor * event_factor * historical_factor
    
    return round(predicted_demand, 2)

def calculate_recommended_quantity(predicted_demand, safety_margin=0.15):
    """
    Calculate recommended preparation quantity with safety margin.
    Safety margin: 15% buffer for waste and unexpected demand.
    """
    recommended = predicted_demand * (1 + safety_margin)
    return round(recommended, 2)

def check_food_safety(storage_time_str, storage_temperature):
    """
    Check if food is safe based on storage conditions.
    
    Safety rules:
    - Room temperature (20-25°C): Maximum 2 hours
    - Refrigerated (4-8°C): Maximum 24 hours
    - Frozen (-18°C or below): Maximum 30 days
    - Otherwise: Unsafe
    """
    try:
        # Parse storage time (format: "HH:MM" in hours:minutes)
        if isinstance(storage_time_str, str) and ':' in storage_time_str:
            hours, minutes = map(int, storage_time_str.split(':'))
            total_hours = hours + (minutes / 60)
        else:
            total_hours = float(storage_time_str) if storage_time_str else 0
        
        storage_temperature = float(storage_temperature)
        
        # Check based on temperature
        if -18 <= storage_temperature <= 0:  # Frozen
            if total_hours <= (30 * 24):  # 30 days in hours
                return 'safe'
        elif 4 <= storage_temperature <= 8:  # Refrigerated
            if total_hours <= 24:
                return 'safe'
        elif 20 <= storage_temperature <= 25:  # Room temperature
            if total_hours <= 2:
                return 'safe'
        
        return 'unsafe'
    except:
        return 'unsafe'

# ============================================================================
# AUTH ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve login page."""
    if 'user_id' in session:
        # Redirect to appropriate dashboard
        user = query_db('SELECT role FROM users WHERE id = ?', (session['user_id'],), one=True)
        if user:
            return redirect(f'/dashboard/{user["role"]}')
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    """Handle login."""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    
    user = query_db('SELECT id, username, password, role, is_active FROM users WHERE username = ?', 
                   (username,), one=True)
    
    if user and user['is_active']:
        # For demo purposes, we're comparing plain text
        # In production, use proper password hashing
        if user['password'] == password:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return jsonify({'success': True, 'role': user['role']})
    
    return jsonify({'success': False, 'error': 'Invalid username or password'}), 401

@app.route('/api/logout', methods=['POST'])
def api_logout():
    """Handle logout."""
    session.clear()
    return jsonify({'success': True})

@app.route('/api/verify-session', methods=['GET'])
def api_verify_session():
    """Verify current session and return role."""
    if 'user_id' in session and 'role' in session:
        return jsonify({'authenticated': True, 'role': session['role']})
    return jsonify({'authenticated': False}), 401

# ============================================================================
# DASHBOARD ROUTES
# ============================================================================

@app.route('/dashboard/admin')
def dashboard_admin():
    """Serve admin dashboard."""
    if 'user_id' not in session or session.get('role') != 'admin':
        return render_template('login.html'), 401
    return render_template('admin.html')

@app.route('/dashboard/kitchen')
def dashboard_kitchen():
    """Serve kitchen dashboard."""
    if 'user_id' not in session or session.get('role') != 'kitchen':
        return render_template('login.html'), 401
    return render_template('kitchen.html')

@app.route('/dashboard/recipient')
def dashboard_recipient():
    """Serve recipient dashboard."""
    if 'user_id' not in session or session.get('role') != 'recipient':
        return render_template('login.html'), 401
    return render_template('recipient.html')

# ============================================================================
# KITCHEN API ROUTES
# ============================================================================

@app.route('/api/kitchen/latest', methods=['GET'])
def api_kitchen_latest():
    """Get latest forecast and surplus data."""
    if 'user_id' not in session or session.get('role') != 'kitchen':
        return jsonify({'error': 'Unauthorized'}), 401
    
    latest = query_db('''
        SELECT f.id AS forecast_id, f.forecast_date, f.expected_attendance,
               f.weather_conditions, f.event_type, f.predicted_demand,
               f.recommended_quantity, f.created_at AS forecast_created_at,
               s.id AS surplus_id, s.prepared_quantity, s.consumed_quantity,
               s.surplus_quantity, s.storage_time, s.storage_temperature,
               s.safety_status, s.status, s.created_at AS surplus_created_at
        FROM food_surplus s
        JOIN forecasts f ON s.forecast_id = f.id
        ORDER BY s.created_at DESC, s.id DESC
        LIMIT 1
    ''', one=True)

    forecast = None
    surplus = None
    if latest:
        forecast = {
            'id': latest['forecast_id'],
            'forecast_date': latest['forecast_date'],
            'expected_attendance': latest['expected_attendance'],
            'weather_conditions': latest['weather_conditions'],
            'event_type': latest['event_type'],
            'predicted_demand': latest['predicted_demand'],
            'recommended_quantity': latest['recommended_quantity'],
            'created_at': latest['forecast_created_at']
        }
        surplus = {
            'id': latest['surplus_id'],
            'forecast_id': latest['forecast_id'],
            'prepared_quantity': latest['prepared_quantity'],
            'consumed_quantity': latest['consumed_quantity'],
            'surplus_quantity': latest['surplus_quantity'],
            'storage_time': latest['storage_time'],
            'storage_temperature': latest['storage_temperature'],
            'safety_status': latest['safety_status'],
            'status': latest['status'],
            'created_at': latest['surplus_created_at']
        }
    
    return jsonify({
        'success': True,
        'forecast': dict(forecast) if forecast else None,
        'surplus': dict(surplus) if surplus else None
    })

@app.route('/api/kitchen/surplus', methods=['POST'])
def api_kitchen_surplus():
    """Save kitchen data (forecast and surplus)."""
    if 'user_id' not in session or session.get('role') != 'kitchen':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        
        # Validate input
        forecast_date = data.get('forecast_date', '').strip()
        expected_attendance = data.get('expected_attendance')
        weather_conditions = data.get('weather_conditions', '').strip()
        event_type = data.get('event_type', '').strip()
        prepared_quantity = data.get('prepared_quantity')
        consumed_quantity = data.get('consumed_quantity')
        storage_time = data.get('storage_time', '').strip()
        storage_temperature = data.get('storage_temperature')
        
        if any(value is None for value in [expected_attendance, prepared_quantity,
                                           consumed_quantity, storage_temperature]) or not all([
                                               forecast_date, weather_conditions,
                                               event_type, storage_time
                                           ]):
            return jsonify({'success': False, 'error': 'All fields are required'}), 400
        
        # Convert to appropriate types
        expected_attendance = int(expected_attendance)
        prepared_quantity = float(prepared_quantity)
        consumed_quantity = float(consumed_quantity)
        storage_temperature = float(storage_temperature)

        if expected_attendance < 1 or prepared_quantity < 0 or consumed_quantity < 0:
            return jsonify({'success': False, 'error': 'Quantities must be valid non-negative values'}), 400
        
        # Calculate predicted demand
        predicted_demand = calculate_demand_forecast(
            expected_attendance, 
            weather_conditions, 
            event_type
        )
        
        # Calculate recommended quantity
        recommended_quantity = calculate_recommended_quantity(predicted_demand)
        
        # Calculate surplus
        surplus_quantity = max(0, prepared_quantity - consumed_quantity)
        
        # Check food safety
        safety_status = check_food_safety(storage_time, storage_temperature)
        
        # Determine status
        status = 'available' if surplus_quantity > 0 and safety_status == 'safe' else 'disposed'
        
        # Save forecast
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO forecasts 
            (forecast_date, expected_attendance, weather_conditions, event_type, predicted_demand, recommended_quantity)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (forecast_date, expected_attendance, weather_conditions, event_type, predicted_demand, recommended_quantity))
        
        forecast_id = cursor.lastrowid
        
        # Save surplus
        cursor.execute('''
            INSERT INTO food_surplus 
            (forecast_id, prepared_quantity, consumed_quantity, surplus_quantity, storage_time, storage_temperature, safety_status, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (forecast_id, prepared_quantity, consumed_quantity, surplus_quantity, storage_time, storage_temperature, safety_status, status))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'forecast_id': forecast_id,
            'surplus_id': cursor.lastrowid,
            'predicted_demand': predicted_demand,
            'recommended_quantity': recommended_quantity,
            'surplus_quantity': surplus_quantity,
            'safety_status': safety_status,
            'status': status
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ============================================================================
# ADMIN API ROUTES
# ============================================================================

@app.route('/api/admin/dashboard', methods=['GET'])
def api_admin_dashboard():
    """Get admin dashboard data."""
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Get latest surplus
    latest_surplus = query_db('''
        SELECT f.forecast_date, f.expected_attendance, f.predicted_demand, 
               f.recommended_quantity, s.prepared_quantity, s.consumed_quantity, 
               s.surplus_quantity, s.storage_time, s.storage_temperature, 
               s.safety_status, s.status
        FROM food_surplus s
        JOIN forecasts f ON s.forecast_id = f.id
        ORDER BY s.created_at DESC
        LIMIT 1
    ''', one=True)
    
    # Get pending requests
    pending_requests = query_db('''
        SELECT rr.id, r.name, rr.quantity, rr.status, rr.created_at, s.surplus_quantity
        FROM recipient_requests rr
        JOIN recipients r ON rr.recipient_id = r.id
        JOIN food_surplus s ON rr.surplus_id = s.id
        WHERE rr.status = 'pending'
        ORDER BY rr.created_at DESC
    ''')

    request_counts = query_db('''
        SELECT status, COUNT(*) AS count
        FROM recipient_requests
        GROUP BY status
    ''')
    request_summary = {'pending': 0, 'approved': 0, 'rejected': 0}
    for row in request_counts:
        request_summary[row['status']] = row['count']
    
    return jsonify({
        'success': True,
        'latest_surplus': dict(latest_surplus) if latest_surplus else None,
        'pending_requests': [dict(row) for row in pending_requests],
        'request_summary': request_summary,
        'impact': calculate_impact_metrics()
    })

@app.route('/api/admin/chart-data', methods=['GET'])
def api_admin_chart_data():
    """Get data for admin charts."""
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Get forecast and surplus data
    records = query_db('''
        SELECT f.forecast_date, f.predicted_demand, s.prepared_quantity, 
               s.consumed_quantity, s.surplus_quantity
        FROM food_surplus s
        JOIN forecasts f ON s.forecast_id = f.id
        ORDER BY f.forecast_date ASC
        LIMIT 30
    ''')
    
    # Get request status counts
    request_counts = query_db('''
        SELECT status, COUNT(*) as count
        FROM recipient_requests
        GROUP BY status
    ''')
    
    # Get total redistributed
    total_redistributed = query_db('''
        SELECT COALESCE(SUM(quantity), 0) as total
        FROM recipient_requests
        WHERE status = 'approved'
    ''', one=True)
    
    dates = []
    predicted_demands = []
    prepared_quantities = []
    consumed_quantities = []
    surplus_quantities = []
    
    for record in records:
        dates.append(record['forecast_date'])
        predicted_demands.append(float(record['predicted_demand']))
        prepared_quantities.append(float(record['prepared_quantity']))
        consumed_quantities.append(float(record['consumed_quantity']))
        surplus_quantities.append(float(record['surplus_quantity']))
    
    request_status = {'pending': 0, 'approved': 0, 'rejected': 0}
    for row in request_counts:
        request_status[row['status']] = row['count']
    
    return jsonify({
        'success': True,
        'dates': dates,
        'predicted_demand': predicted_demands,
        'prepared_quantity': prepared_quantities,
        'consumed_quantity': consumed_quantities,
        'surplus_quantity': surplus_quantities,
        'request_status': request_status,
        'total_redistributed': float(total_redistributed['total']) if total_redistributed else 0
    })

@app.route('/api/admin/request/approve', methods=['POST'])
def api_admin_request_approve():
    """Approve a recipient request."""
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        request_id = data.get('request_id')
        
        if not request_id:
            return jsonify({'success': False, 'error': 'Request ID required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Get the request
        recipient_request = query_db(
            'SELECT id, surplus_id, quantity, status FROM recipient_requests WHERE id = ?',
            (request_id,), one=True
        )
        
        if not recipient_request:
            return jsonify({'success': False, 'error': 'Request not found'}), 404
        
        if recipient_request['status'] != 'pending':
            return jsonify({'success': False, 'error': 'Request is not pending'}), 400
        
        # Get the surplus
        surplus = query_db(
            'SELECT id, surplus_quantity, status FROM food_surplus WHERE id = ?',
            (recipient_request['surplus_id'],), one=True
        )
        
        if not surplus:
            return jsonify({'success': False, 'error': 'Surplus not found'}), 404
        
        if surplus['status'] != 'available':
            return jsonify({'success': False, 'error': 'Surplus is not available'}), 400
        
        requested_quantity = float(recipient_request['quantity'])
        available_quantity = float(surplus['surplus_quantity'])
        
        if requested_quantity > available_quantity:
            return jsonify({'success': False, 'error': 'Requested quantity exceeds available surplus'}), 400
        
        # Update request status
        cursor.execute(
            'UPDATE recipient_requests SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            ('approved', request_id)
        )
        
        # Update surplus quantity
        new_surplus_quantity = available_quantity - requested_quantity
        new_status = 'redistributed' if new_surplus_quantity == 0 else 'available'
        
        cursor.execute(
            'UPDATE food_surplus SET surplus_quantity = ?, status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (new_surplus_quantity, new_status, recipient_request['surplus_id'])
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Request approved',
            'new_surplus_quantity': new_surplus_quantity
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ============================================================================
# RECIPIENT API ROUTES
# ============================================================================

@app.route('/api/recipient/available-food', methods=['GET'])
def api_recipient_available_food():
    """Get available food for recipients."""
    if 'user_id' not in session or session.get('role') != 'recipient':
        return jsonify({'error': 'Unauthorized'}), 401
    
    recipient_id = request.args.get('recipient_id', 1, type=int)

    recipient = query_db('''
        SELECT id, name, eligibility_status, is_active
        FROM recipients
        WHERE id = ?
    ''', (recipient_id,), one=True)
    if not recipient:
        return jsonify({'success': False, 'error': 'Recipient not found'}), 404
    if recipient['eligibility_status'] != 'eligible' or not recipient['is_active']:
        return jsonify({'success': False, 'error': 'Recipient is not eligible'}), 400

    available_food = query_db('''
        SELECT s.id, f.forecast_date, s.prepared_quantity, s.consumed_quantity, 
               s.surplus_quantity, s.safety_status, s.status
        FROM food_surplus s
        JOIN forecasts f ON s.forecast_id = f.id
        WHERE s.status = 'available' 
        AND s.safety_status = 'safe' 
        AND s.surplus_quantity > 0
        ORDER BY s.created_at DESC
    ''')
    
    return jsonify({
        'success': True,
        'recipient': dict(recipient),
        'available_food': [dict(row) for row in available_food]
    })

@app.route('/api/recipient/request', methods=['POST'])
def api_recipient_request():
    """Create a food request from recipient."""
    if 'user_id' not in session or session.get('role') != 'recipient':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        recipient_id = data.get('recipient_id')
        surplus_id = data.get('surplus_id')
        quantity = data.get('quantity')
        
        if not all([recipient_id, surplus_id, quantity]):
            return jsonify({'success': False, 'error': 'All fields required'}), 400
        
        quantity = float(quantity)
        
        # Validate recipient
        recipient = query_db(
            'SELECT id, eligibility_status, is_active FROM recipients WHERE id = ?',
            (recipient_id,), one=True
        )
        
        if not recipient:
            return jsonify({'success': False, 'error': 'Recipient not found'}), 404
        
        if recipient['eligibility_status'] != 'eligible' or not recipient['is_active']:
            return jsonify({'success': False, 'error': 'Recipient is not eligible'}), 400
        
        # Validate surplus
        surplus = query_db(
            'SELECT id, surplus_quantity, safety_status, status FROM food_surplus WHERE id = ?',
            (surplus_id,), one=True
        )
        
        if not surplus:
            return jsonify({'success': False, 'error': 'Surplus not found'}), 404
        
        if surplus['status'] != 'available' or surplus['safety_status'] != 'safe':
            return jsonify({'success': False, 'error': 'Surplus not available or unsafe'}), 400
        
        if quantity <= 0:
            return jsonify({'success': False, 'error': 'Quantity must be greater than zero'}), 400
        
        if quantity > float(surplus['surplus_quantity']):
            return jsonify({'success': False, 'error': 'Requested quantity exceeds available surplus'}), 400
        
        # Create request
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO recipient_requests (recipient_id, surplus_id, quantity, status)
            VALUES (?, ?, ?, 'pending')
        ''', (recipient_id, surplus_id, quantity))
        
        conn.commit()
        request_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'success': True,
            'request_id': request_id,
            'status': 'pending'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/recipient/my-requests', methods=['GET'])
def api_recipient_my_requests():
    """Get recipient's own requests."""
    if 'user_id' not in session or session.get('role') != 'recipient':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        recipient_id = request.args.get('recipient_id')
        
        requests = query_db('''
            SELECT rr.id, rr.quantity, rr.status, rr.created_at, rr.updated_at,
                   f.forecast_date, s.surplus_quantity
            FROM recipient_requests rr
            JOIN food_surplus s ON rr.surplus_id = s.id
            JOIN forecasts f ON s.forecast_id = f.id
            WHERE rr.recipient_id = ?
            ORDER BY rr.created_at DESC
        ''', (recipient_id,))
        
        return jsonify({
            'success': True,
            'requests': [dict(row) for row in requests]
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ============================================================================
# IMPACT CALCULATION ROUTES
# ============================================================================

@app.route('/api/impact/calculations', methods=['GET'])
def api_impact_calculations():
    """Calculate impact metrics."""
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        metrics = calculate_impact_metrics()
        
        return jsonify({
            'success': True,
            **metrics,
            'assumptions': {
                'cost_per_kg': COST_PER_KG,
                'carbon_per_kg': CARBON_PER_KG
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors."""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
