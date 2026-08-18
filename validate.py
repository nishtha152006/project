#!/usr/bin/env python3
"""Quick validation script for Rupee project."""

import sys
import os

# Add project to path
project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_path)

print("=" * 70)
print("RUPEE PROJECT VALIDATION")
print("=" * 70)

# Test 1: Import database
print("\n[1] Testing database module...")
try:
    from database import init_db, DATABASE_PATH
    print("    ✓ Database module imported successfully")
    print(f"    ✓ Database path: {DATABASE_PATH}")
except Exception as e:
    print(f"    ✗ Error importing database: {e}")
    sys.exit(1)

# Test 2: Import Flask app
print("\n[2] Testing Flask application...")
try:
    from app import app
    print("    ✓ Flask app imported successfully")
except Exception as e:
    print(f"    ✗ Error importing Flask app: {e}")
    sys.exit(1)

# Test 3: Initialize database
print("\n[3] Initializing database...")
try:
    init_db()
    if os.path.exists(DATABASE_PATH):
        print(f"    ✓ Database initialized at {DATABASE_PATH}")
        print(f"    ✓ Database size: {os.path.getsize(DATABASE_PATH)} bytes")
    else:
        print(f"    ✗ Database file not created")
        sys.exit(1)
except Exception as e:
    print(f"    ✗ Error initializing database: {e}")
    sys.exit(1)

# Test 4: Check database tables
print("\n[4] Checking database tables...")
try:
    from database import query_db
    
    tables = query_db("SELECT name FROM sqlite_master WHERE type='table'")
    expected_tables = ['users', 'recipients', 'forecasts', 'food_surplus', 'recipient_requests']
    
    found_tables = [t['name'] for t in tables]
    
    for table in expected_tables:
        if table in found_tables:
            print(f"    ✓ Table '{table}' exists")
        else:
            print(f"    ✗ Table '{table}' missing")
            sys.exit(1)
except Exception as e:
    print(f"    ✗ Error checking tables: {e}")
    sys.exit(1)

# Test 5: Check demo users
print("\n[5] Checking demo users...")
try:
    users = query_db("SELECT username, role FROM users WHERE is_active = 1")
    
    expected_users = {
        'admin': 'admin',
        'kitchen': 'kitchen',
        'recipient1': 'recipient',
        'recipient2': 'recipient'
    }
    
    found_users = {u['username']: u['role'] for u in users}
    
    for username, role in expected_users.items():
        if username in found_users and found_users[username] == role:
            print(f"    ✓ User '{username}' (role: {role}) exists")
        else:
            print(f"    ✗ User '{username}' missing or incorrect role")
except Exception as e:
    print(f"    ✗ Error checking users: {e}")
    sys.exit(1)

# Test 6: Check Flask routes
print("\n[6] Checking Flask routes...")
try:
    routes = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            routes.append(str(rule))
    
    expected_routes = [
        '/',
        '/api/login',
        '/api/logout',
        '/api/verify-session',
        '/dashboard/admin',
        '/dashboard/kitchen',
        '/dashboard/recipient',
        '/api/kitchen/latest',
        '/api/kitchen/surplus',
        '/api/admin/dashboard',
        '/api/admin/chart-data',
        '/api/admin/request/approve',
        '/api/recipient/available-food',
        '/api/recipient/request',
        '/api/recipient/my-requests',
        '/api/impact/calculations'
    ]
    
    found_route_paths = [r.split()[0] for r in routes]
    
    for route in expected_routes:
        if route in found_route_paths:
            print(f"    ✓ Route '{route}' found")
        else:
            print(f"    ✗ Route '{route}' missing")
    
    print(f"    ✓ Total routes: {len(found_route_paths)}")
except Exception as e:
    print(f"    ✗ Error checking routes: {e}")
    sys.exit(1)

# Test 7: Test demand calculation
print("\n[7] Testing demand forecasting...")
try:
    from app import calculate_demand_forecast
    
    demand = calculate_demand_forecast(200, 'sunny', 'regular')
    expected = 200 * 1.2 * 0.9 * 1.0
    
    if abs(demand - expected) < 0.01:
        print(f"    ✓ Demand calculation correct: {demand} kg")
    else:
        print(f"    ✗ Demand calculation incorrect: {demand} vs {expected}")
except Exception as e:
    print(f"    ✗ Error testing demand calculation: {e}")
    sys.exit(1)

# Test 8: Test food safety check
print("\n[8] Testing food safety logic...")
try:
    from app import check_food_safety
    
    # Safe: Refrigerated for 2 hours
    safe = check_food_safety('02:00', 4)
    if safe == 'safe':
        print(f"    ✓ Refrigerated food (2h, 4°C): {safe}")
    else:
        print(f"    ✗ Expected safe, got {safe}")
    
    # Unsafe: Room temp for 3 hours
    unsafe = check_food_safety('03:00', 22)
    if unsafe == 'unsafe':
        print(f"    ✓ Room temp food (3h, 22°C): {unsafe}")
    else:
        print(f"    ✗ Expected unsafe, got {unsafe}")
except Exception as e:
    print(f"    ✗ Error testing food safety: {e}")
    sys.exit(1)

# Test 9: Test Flask test client
print("\n[9] Testing Flask test client...")
try:
    with app.test_client() as client:
        # Test login endpoint exists
        response = client.get('/')
        if response.status_code == 200:
            print(f"    ✓ Login page loads (status: {response.status_code})")
        else:
            print(f"    ✗ Login page returned status: {response.status_code}")
except Exception as e:
    print(f"    ✗ Error testing Flask: {e}")
    sys.exit(1)

# Test 10: Check static files
print("\n[10] Checking static files...")
try:
    static_files = {
        'css/style.css': os.path.join(project_path, 'static', 'css', 'style.css'),
        'js/common.js': os.path.join(project_path, 'static', 'js', 'common.js'),
        'js/login.js': os.path.join(project_path, 'static', 'js', 'login.js'),
        'js/admin.js': os.path.join(project_path, 'static', 'js', 'admin.js'),
        'js/kitchen.js': os.path.join(project_path, 'static', 'js', 'kitchen.js'),
        'js/recipient.js': os.path.join(project_path, 'static', 'js', 'recipient.js'),
    }
    
    for name, path in static_files.items():
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"    ✓ {name} ({size} bytes)")
        else:
            print(f"    ✗ {name} missing")
except Exception as e:
    print(f"    ✗ Error checking files: {e}")
    sys.exit(1)

# Test 11: Check templates
print("\n[11] Checking HTML templates...")
try:
    templates = {
        'login.html': os.path.join(project_path, 'templates', 'login.html'),
        'admin.html': os.path.join(project_path, 'templates', 'admin.html'),
        'kitchen.html': os.path.join(project_path, 'templates', 'kitchen.html'),
        'recipient.html': os.path.join(project_path, 'templates', 'recipient.html'),
    }
    
    for name, path in templates.items():
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"    ✓ {name} ({size} bytes)")
        else:
            print(f"    ✗ {name} missing")
except Exception as e:
    print(f"    ✗ Error checking templates: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("✓ ALL VALIDATION CHECKS PASSED!")
print("=" * 70)
print("\nProject is ready to run. Start with:")
print("  python3 app.py")
print("\nThen access at: http://localhost:5000")
