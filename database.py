"""Database initialization and management for Rupee system."""

import sqlite3
import os
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database', 'rupee.db')

def get_db_path():
    """Return the database path."""
    return DATABASE_PATH

def get_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with schema."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'kitchen', 'recipient')),
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Recipients table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS recipients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        eligibility_status TEXT NOT NULL CHECK(eligibility_status IN ('eligible', 'ineligible')),
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Forecasts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS forecasts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        forecast_date DATE NOT NULL,
        expected_attendance INTEGER NOT NULL,
        weather_conditions TEXT NOT NULL,
        event_type TEXT NOT NULL,
        predicted_demand REAL NOT NULL,
        recommended_quantity REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Food surplus table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS food_surplus (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        forecast_id INTEGER NOT NULL,
        prepared_quantity REAL NOT NULL,
        consumed_quantity REAL NOT NULL,
        surplus_quantity REAL NOT NULL DEFAULT 0,
        storage_time TEXT NOT NULL,
        storage_temperature REAL NOT NULL,
        safety_status TEXT NOT NULL CHECK(safety_status IN ('safe', 'unsafe')),
        status TEXT NOT NULL CHECK(status IN ('available', 'redistributed', 'disposed')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (forecast_id) REFERENCES forecasts (id)
    )
    ''')
    
    # Recipient requests table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS recipient_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient_id INTEGER NOT NULL,
        surplus_id INTEGER NOT NULL,
        quantity REAL NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('pending', 'approved', 'rejected')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (recipient_id) REFERENCES recipients (id),
        FOREIGN KEY (surplus_id) REFERENCES food_surplus (id)
    )
    ''')
    
    conn.commit()
    
    # Insert demo data only if users table is empty
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        # Demo users
        demo_users = [
            ('admin', 'admin123', 'admin'),
            ('kitchen', 'kitchen123', 'kitchen'),
            ('recipient1', 'recipient123', 'recipient'),
            ('recipient2', 'recipient123', 'recipient'),
        ]
        
        cursor.executemany(
            'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
            demo_users
        )
        
        # Demo recipients
        demo_recipients = [
            ('Community Center A', 'eligible'),
            ('Local Food Bank B', 'eligible'),
            ('Shelter C', 'ineligible'),
        ]
        
        cursor.executemany(
            'INSERT INTO recipients (name, eligibility_status) VALUES (?, ?)',
            demo_recipients
        )
        
        conn.commit()
    
    conn.close()

def query_db(query, args=(), one=False):
    """Execute a query and return results."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, args)
    result = cursor.fetchall()
    conn.close()
    return (result[0] if result else None) if one else result

def execute_db(query, args=()):
    """Execute an insert/update/delete query."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, args)
    conn.commit()
    result_id = cursor.lastrowid
    conn.close()
    return result_id

if __name__ == '__main__':
    init_db()
    print(f"Database initialized at: {DATABASE_PATH}")
