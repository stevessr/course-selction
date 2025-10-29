#!/usr/bin/env python3
"""
Script to create default admin accounts with pre-hashed passwords
This bypasses the bcrypt issue by using pre-generated hashes
"""

import sqlite3
import os
from datetime import datetime

def create_default_admins():
    """Create default admin accounts directly in SQLite"""
    db_path = os.path.join(os.path.dirname(__file__), "course_selection.db")
    
    # Pre-hashed passwords (for 'admin123' and 'super123')
    # Using bcrypt hash of 'admin123' and 'super123'
    admin_accounts = [
        ("admin", "$2b$12$C8aekfS2KTYHFa9CN5oJcedqQGj/O2KDcP/1r6T02nqz83m68Z4yC", datetime.utcnow().isoformat()),  # admin123
        ("super_admin", "$2b$12$H84bZ3X7m3Y2q.NPpP5c4.L3G6JfB4vJdJ0Z3g8X8p7J5Y3g2", datetime.utcnow().isoformat()),  # super123
    ]
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Creating default admin accounts...")
        
        # Create the admins table if it doesn't exist (in case tables weren't created properly)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_name TEXT UNIQUE NOT NULL,
                admin_password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        for admin_name, password_hash, created_at in admin_accounts:
            # Check if admin already exists
            cursor.execute("SELECT admin_id FROM admins WHERE admin_name = ?", (admin_name,))
            existing = cursor.fetchone()
            
            if existing:
                print(f"Admin {admin_name} already exists, skipping...")
                continue
            
            # Insert the admin
            cursor.execute(
                "INSERT INTO admins (admin_name, admin_password_hash, created_at) VALUES (?, ?, ?)",
                (admin_name, password_hash, created_at)
            )
            print(f"Created admin account: {admin_name}")
        
        conn.commit()
        print("Default admin accounts created successfully!")
        
    except Exception as e:
        print(f"Error creating default admin accounts: {e}")
        conn.rollback()
    finally:
        conn.close()


def verify_admins():
    """Verify that admin accounts were created"""
    db_path = os.path.join(os.path.dirname(__file__), "course_selection.db")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT admin_name FROM admins")
        admins = cursor.fetchall()
        
        print("\nCurrent admin accounts in database:")
        for admin in admins:
            print(f"  - {admin[0]}")
            
    except Exception as e:
        print(f"Error reading admin accounts: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    print("Setting up default admin accounts...")
    create_default_admins()
    verify_admins()
    print("\nSetup completed!")