#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Check the database structure.
"""

import sqlite3
import os

def check_db():
    """Check the database structure."""
    print("Checking database structure...")
    
    # Check if database exists
    if not os.path.exists('instance/growth_navigator.db'):
        print("Database does not exist.")
        return
    
    # Connect to the database
    conn = sqlite3.connect('instance/growth_navigator.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [table[0] for table in cursor.fetchall()]
    print(f"Tables: {tables}")
    
    # Check if user_levels table exists
    if 'user_levels' in tables:
        print("user_levels table exists")
    else:
        print("user_levels table does not exist")
    
    # Check users table structure
    cursor.execute("PRAGMA table_info(users)")
    users_columns = [col[1] for col in cursor.fetchall()]
    print(f"Users columns: {users_columns}")
    
    # Check goals table structure
    cursor.execute("PRAGMA table_info(goals)")
    goals_columns = [col[1] for col in cursor.fetchall()]
    print(f"Goals columns: {goals_columns}")
    
    # Check if created_at column exists in goals
    if 'created_at' in goals_columns:
        print("created_at column exists in goals table")
    else:
        print("created_at column does not exist in goals table")
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    check_db()
