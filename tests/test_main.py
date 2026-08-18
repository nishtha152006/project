"""
Test suite for Rupee - Food Demand Forecasting System
Run with: pytest tests/test_main.py
"""

import pytest
import os
import sys
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from database import init_db, DATABASE_PATH

@pytest.fixture
def client():
    """Create a test client."""
    # Use a test database
    app.config['TESTING'] = True
    
    # Initialize database
    init_db()
    
    with app.test_client() as client:
        yield client

@pytest.fixture
def setup_auth(client):
    """Setup authenticated session."""
    response = client.post('/api/login', 
        json={'username': 'admin', 'password': 'admin123'},
        content_type='application/json'
    )
    assert response.status_code == 200
    return client

# ============================================================================
# DATABASE TESTS
# ============================================================================

def test_database_initialization():
    """Test that database is initialized correctly."""
    init_db()
    assert os.path.exists(DATABASE_PATH)
    print(f"✓ Database exists at {DATABASE_PATH}")

# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================

def test_login_page(client):
    """Test login page loads."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Rupee' in response.data
    print("✓ Login page loads")

def test_admin_login(client):
    """Test admin login."""
    response = client.post('/api/login',
        json={'username': 'admin', 'password': 'admin123'},
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert data['role'] == 'admin'
    print("✓ Admin login works")

def test_kitchen_login(client):
    """Test kitchen staff login."""
    response = client.post('/api/login',
        json={'username': 'kitchen', 'password': 'kitchen123'},
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert data['role'] == 'kitchen'
    print("✓ Kitchen staff login works")

def test_recipient_login(client):
    """Test recipient login."""
    response = client.post('/api/login',
        json={'username': 'recipient1', 'password': 'recipient123'},
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert data['role'] == 'recipient'
    print("✓ Recipient login works")

def test_invalid_login(client):
    """Test invalid login."""
    response = client.post('/api/login',
        json={'username': 'invalid', 'password': 'wrong'},
        content_type='application/json'
    )
    assert response.status_code == 401
    data = json.loads(response.data)
    assert data['success'] == False
    print("✓ Invalid login rejected")

# ============================================================================
# KITCHEN API TESTS
# ============================================================================

def test_kitchen_surplus_save(setup_auth):
    """Test kitchen can save surplus data."""
    client = setup_auth
    
    # Login as kitchen staff
    client.post('/api/login',
        json={'username': 'kitchen', 'password': 'kitchen123'},
        content_type='application/json'
    )
    
    response = client.post('/api/kitchen/surplus',
        json={
            'forecast_date': '2024-01-15',
            'expected_attendance': 200,
            'weather_conditions': 'sunny',
            'event_type': 'regular',
            'predicted_demand': 240.0,
            'recommended_quantity': 276.0,
            'prepared_quantity': 500,
            'consumed_quantity': 400,
            'storage_time': '02:30',
            'storage_temperature': 4
        },
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert data['surplus_quantity'] == 100
    assert data['safety_status'] == 'safe'
    print("✓ Kitchen can save surplus data")

def test_kitchen_surplus_calculation():
    """Test surplus calculation."""
    from app import app as flask_app
    with flask_app.app_context():
        # Test: 500 prepared - 400 consumed = 100 surplus
        client = flask_app.test_client()
        client.post('/api/login',
            json={'username': 'kitchen', 'password': 'kitchen123'},
            content_type='application/json'
        )
        
        response = client.post('/api/kitchen/surplus',
            json={
                'forecast_date': '2024-01-16',
                'expected_attendance': 150,
                'weather_conditions': 'cloudy',
                'event_type': 'regular',
                'predicted_demand': 180.0,
                'recommended_quantity': 207.0,
                'prepared_quantity': 300,
                'consumed_quantity': 250,
                'storage_time': '01:00',
                'storage_temperature': 4
            },
            content_type='application/json'
        )
        
        data = json.loads(response.data)
        assert data['surplus_quantity'] == 50
        print("✓ Surplus calculation correct")

def test_food_safety_check():
    """Test food safety logic."""
    from app import check_food_safety
    
    # Safe: Refrigerated for 2 hours
    assert check_food_safety('02:00', 4) == 'safe'
    
    # Safe: Frozen for 10 days
    assert check_food_safety('240:00', -18) == 'safe'
    
    # Unsafe: Room temp for 3 hours
    assert check_food_safety('03:00', 22) == 'unsafe'
    
    print("✓ Food safety check works")

def test_kitchen_latest_record(setup_auth):
    """Test getting latest kitchen record."""
    client = setup_auth
    
    # Login as kitchen and save data
    client.post('/api/login',
        json={'username': 'kitchen', 'password': 'kitchen123'},
        content_type='application/json'
    )
    
    client.post('/api/kitchen/surplus',
        json={
            'forecast_date': '2024-01-17',
            'expected_attendance': 180,
            'weather_conditions': 'rainy',
            'event_type': 'exam',
            'predicted_demand': 432.0,
            'recommended_quantity': 496.8,
            'prepared_quantity': 600,
            'consumed_quantity': 450,
            'storage_time': '01:30',
            'storage_temperature': 4
        },
        content_type='application/json'
    )
    
    # Get latest
    response = client.get('/api/kitchen/latest')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert data['forecast'] is not None
    assert data['surplus'] is not None
    print("✓ Can retrieve latest kitchen record")

# ============================================================================
# ADMIN API TESTS
# ============================================================================

def test_admin_dashboard(setup_auth):
    """Test admin can view dashboard."""
    client = setup_auth
    
    # Login as admin
    client.post('/api/login',
        json={'username': 'admin', 'password': 'admin123'},
        content_type='application/json'
    )
    
    response = client.get('/api/admin/dashboard')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert 'pending_requests' in data
    print("✓ Admin can view dashboard")

def test_admin_chart_data(setup_auth):
    """Test admin can get chart data."""
    client = setup_auth
    
    # Login as admin
    client.post('/api/login',
        json={'username': 'admin', 'password': 'admin123'},
        content_type='application/json'
    )
    
    response = client.get('/api/admin/chart-data')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert 'dates' in data
    assert 'predicted_demand' in data
    print("✓ Admin can retrieve chart data")

def test_admin_request_approval(setup_auth):
    """Test admin can approve requests."""
    client = setup_auth
    
    # Setup: Create a surplus and request
    from database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create forecast
    cursor.execute('''
        INSERT INTO forecasts (forecast_date, expected_attendance, weather_conditions, 
                              event_type, predicted_demand, recommended_quantity)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ('2024-01-20', 200, 'sunny', 'regular', 240.0, 276.0))
    forecast_id = cursor.lastrowid
    
    # Create surplus
    cursor.execute('''
        INSERT INTO food_surplus (forecast_id, prepared_quantity, consumed_quantity, 
                                 surplus_quantity, storage_time, storage_temperature,
                                 safety_status, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (forecast_id, 500, 400, 100, '01:00', 4, 'safe', 'available'))
    surplus_id = cursor.lastrowid
    
    # Create request
    cursor.execute('''
        INSERT INTO recipient_requests (recipient_id, surplus_id, quantity, status)
        VALUES (?, ?, ?, ?)
    ''', (1, surplus_id, 50, 'pending'))
    request_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    # Login as admin and approve
    client.post('/api/login',
        json={'username': 'admin', 'password': 'admin123'},
        content_type='application/json'
    )
    
    response = client.post('/api/admin/request/approve',
        json={'request_id': request_id},
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert data['new_surplus_quantity'] == 50
    print("✓ Admin can approve requests")

def test_no_negative_surplus():
    """Test that surplus never becomes negative."""
    from database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create forecast and surplus
    cursor.execute('''
        INSERT INTO forecasts (forecast_date, expected_attendance, weather_conditions, 
                              event_type, predicted_demand, recommended_quantity)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ('2024-01-21', 100, 'sunny', 'regular', 120.0, 138.0))
    forecast_id = cursor.lastrowid
    
    cursor.execute('''
        INSERT INTO food_surplus (forecast_id, prepared_quantity, consumed_quantity, 
                                 surplus_quantity, storage_time, storage_temperature,
                                 safety_status, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (forecast_id, 150, 140, 10, '01:00', 4, 'safe', 'available'))
    surplus_id = cursor.lastrowid
    
    # Try to request more than available
    cursor.execute('''
        INSERT INTO recipient_requests (recipient_id, surplus_id, quantity, status)
        VALUES (?, ?, ?, ?)
    ''', (1, surplus_id, 20, 'pending'))
    request_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    # Attempt to approve (should fail)
    from app import app as flask_app
    client = flask_app.test_client()
    client.post('/api/login',
        json={'username': 'admin', 'password': 'admin123'},
        content_type='application/json'
    )
    
    response = client.post('/api/admin/request/approve',
        json={'request_id': request_id},
        content_type='application/json'
    )
    
    data = json.loads(response.data)
    assert data['success'] == False
    print("✓ Surplus protection works (no negative surplus)")

# ============================================================================
# RECIPIENT API TESTS
# ============================================================================

def test_recipient_available_food(setup_auth):
    """Test recipient can see available food."""
    client = setup_auth
    
    # Login as recipient
    client.post('/api/login',
        json={'username': 'recipient1', 'password': 'recipient123'},
        content_type='application/json'
    )
    
    response = client.get('/api/recipient/available-food')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert 'available_food' in data
    print("✓ Recipient can view available food")

def test_recipient_creates_request(setup_auth):
    """Test recipient can create a request."""
    client = setup_auth
    
    # Setup: Create safe surplus
    from database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO forecasts (forecast_date, expected_attendance, weather_conditions, 
                              event_type, predicted_demand, recommended_quantity)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ('2024-01-22', 200, 'sunny', 'regular', 240.0, 276.0))
    forecast_id = cursor.lastrowid
    
    cursor.execute('''
        INSERT INTO food_surplus (forecast_id, prepared_quantity, consumed_quantity, 
                                 surplus_quantity, storage_time, storage_temperature,
                                 safety_status, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (forecast_id, 500, 400, 100, '01:00', 4, 'safe', 'available'))
    surplus_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    # Login as recipient and request
    client.post('/api/login',
        json={'username': 'recipient1', 'password': 'recipient123'},
        content_type='application/json'
    )
    
    response = client.post('/api/recipient/request',
        json={
            'recipient_id': 1,
            'surplus_id': surplus_id,
            'quantity': 25
        },
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert data['status'] == 'pending'
    print("✓ Recipient can create request")

def test_unsafe_food_not_visible():
    """Test that unsafe food is not visible to recipients."""
    from database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create unsafe surplus (hot food for too long)
    cursor.execute('''
        INSERT INTO forecasts (forecast_date, expected_attendance, weather_conditions, 
                              event_type, predicted_demand, recommended_quantity)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ('2024-01-23', 100, 'sunny', 'regular', 120.0, 138.0))
    forecast_id = cursor.lastrowid
    
    cursor.execute('''
        INSERT INTO food_surplus (forecast_id, prepared_quantity, consumed_quantity, 
                                 surplus_quantity, storage_time, storage_temperature,
                                 safety_status, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (forecast_id, 200, 150, 50, '03:00', 22, 'unsafe', 'available'))
    
    conn.commit()
    conn.close()
    
    # Check that unsafe food is not returned
    from app import app as flask_app
    client = flask_app.test_client()
    client.post('/api/login',
        json={'username': 'recipient1', 'password': 'recipient123'},
        content_type='application/json'
    )
    
    response = client.get('/api/recipient/available-food')
    data = json.loads(response.data)
    
    # Should not contain the unsafe item
    for item in data['available_food']:
        assert item['safety_status'] == 'safe'
    
    print("✓ Unsafe food is hidden from recipients")

# ============================================================================
# END-TO-END TEST
# ============================================================================

def test_end_to_end_workflow(setup_auth):
    """
    Complete workflow test:
    1. Kitchen enters 500 prepared, 400 consumed = 100 surplus
    2. Admin sees 100 surplus
    3. Recipient sees available food
    4. Recipient requests food
    5. Admin approves
    6. Surplus reduced correctly
    """
    client = setup_auth
    
    # Step 1: Kitchen enters data
    client.post('/api/login',
        json={'username': 'kitchen', 'password': 'kitchen123'},
        content_type='application/json'
    )
    
    response = client.post('/api/kitchen/surplus',
        json={
            'forecast_date': '2024-01-25',
            'expected_attendance': 200,
            'weather_conditions': 'sunny',
            'event_type': 'regular',
            'predicted_demand': 240.0,
            'recommended_quantity': 276.0,
            'prepared_quantity': 500,
            'consumed_quantity': 400,
            'storage_time': '01:00',
            'storage_temperature': 4
        },
        content_type='application/json'
    )
    
    data = json.loads(response.data)
    assert data['surplus_quantity'] == 100
    surplus_id = data['forecast_id']  # Will get actual surplus_id from DB
    
    # Step 2: Admin sees the data
    client.post('/api/login',
        json={'username': 'admin', 'password': 'admin123'},
        content_type='application/json'
    )
    
    response = client.get('/api/admin/dashboard')
    data = json.loads(response.data)
    assert data['latest_surplus']['surplus_quantity'] == 100
    
    # Step 3: Recipient sees available food and makes request
    client.post('/api/login',
        json={'username': 'recipient1', 'password': 'recipient123'},
        content_type='application/json'
    )
    
    response = client.get('/api/recipient/available-food')
    data = json.loads(response.data)
    assert len(data['available_food']) > 0
    
    available_surplus = data['available_food'][-1]
    surplus_id = available_surplus['id']
    
    response = client.post('/api/recipient/request',
        json={
            'recipient_id': 1,
            'surplus_id': surplus_id,
            'quantity': 100
        },
        content_type='application/json'
    )
    
    request_data = json.loads(response.data)
    request_id = request_data['request_id']
    assert request_data['status'] == 'pending'
    
    # Step 4: Admin approves
    client.post('/api/login',
        json={'username': 'admin', 'password': 'admin123'},
        content_type='application/json'
    )
    
    response = client.post('/api/admin/request/approve',
        json={'request_id': request_id},
        content_type='application/json'
    )
    
    approve_data = json.loads(response.data)
    assert approve_data['success'] == True
    assert approve_data['new_surplus_quantity'] == 0
    
    print("✓ End-to-end workflow complete")

# ============================================================================
# IMPACT METRICS TEST
# ============================================================================

def test_impact_calculations(setup_auth):
    """Test impact metrics calculation."""
    client = setup_auth
    
    client.post('/api/login',
        json={'username': 'admin', 'password': 'admin123'},
        content_type='application/json'
    )
    
    response = client.get('/api/impact/calculations')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert 'food_saved' in data
    assert 'cost_saved' in data
    assert 'carbon_saved' in data
    print("✓ Impact calculations work")

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
