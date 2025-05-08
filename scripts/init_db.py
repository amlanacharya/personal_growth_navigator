#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to initialize the database with the correct schema.
"""

import os
import sqlite3
import sys

def init_db():
    """Initialize the database with the correct schema."""
    # Get the base directory
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    # Create the instance directory if it doesn't exist
    instance_dir = os.path.join(base_dir, 'instance')
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
        print(f"Created instance directory at {instance_dir}")
    
    # Database path
    db_path = os.path.join(instance_dir, 'growth_navigator.db')
    
    # Check if the database already exists
    if os.path.exists(db_path):
        backup_path = os.path.join(instance_dir, 'growth_navigator_backup.db')
        print(f"Database already exists at {db_path}")
        print(f"Creating backup at {backup_path}")
        import shutil
        shutil.copy2(db_path, backup_path)
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Read the schema file
    schema_path = os.path.join(base_dir, 'migrations', 'schema.sql')
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    # Execute the schema SQL
    cursor.executescript(schema_sql)
    
    # Commit the changes
    conn.commit()
    
    # Close the connection
    conn.close()
    
    print(f"Database initialized successfully at {db_path}")
    
    # Check if we need to migrate data from the old database
    old_db_path = os.path.join(base_dir, 'growth_navigator.db')
    if os.path.exists(old_db_path):
        print(f"Found old database at {old_db_path}")
        print("You may want to migrate data from the old database to the new one.")
        print("Run the following command to migrate data:")
        print(f"python scripts/migrate_database.py")

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Done!")
