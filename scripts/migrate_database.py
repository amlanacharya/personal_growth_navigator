#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to migrate the database to the new location.

This script should be run after the codebase has been reorganized.
"""

import os
import shutil
import sqlite3
from datetime import datetime

def migrate_database():
    """Migrate the database to the new location."""
    # Source and destination paths
    source_path = 'growth_navigator.db'
    instance_dir = 'instance'
    dest_path = os.path.join(instance_dir, 'growth_navigator.db')
    
    # Check if source database exists
    if not os.path.exists(source_path):
        print(f"Source database not found at {source_path}")
        return False
    
    # Create instance directory if it doesn't exist
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
        print(f"Created instance directory at {instance_dir}")
    
    # Create a backup of the source database
    backup_path = f"growth_navigator_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(source_path, backup_path)
    print(f"Created backup of database at {backup_path}")
    
    # Copy the database to the new location
    shutil.copy2(source_path, dest_path)
    print(f"Copied database to {dest_path}")
    
    # Verify the new database
    try:
        conn = sqlite3.connect(dest_path)
        cursor = conn.cursor()
        
        # Check if we can query the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"Verified database at {dest_path}. Found {len(tables)} tables.")
        conn.close()
        
        return True
    except sqlite3.Error as e:
        print(f"Error verifying database: {e}")
        return False

def main():
    """Main function to migrate the database."""
    print("Starting database migration...")
    
    success = migrate_database()
    
    if success:
        print("\nDatabase migration completed successfully!")
        print("\nNext steps:")
        print("1. Update the database path in your configuration if needed")
        print("2. Test the application to ensure it can connect to the database")
        print("3. Once everything is working, you can remove the original database file")
    else:
        print("\nDatabase migration failed. Please check the error messages above.")

if __name__ == "__main__":
    main()
