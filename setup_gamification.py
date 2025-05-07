import os
import sqlite3
from schema_updates import update_database_schema
from populate_gamification_data import populate_gamification_data

def setup_gamification():
    """
    Set up the gamification features by updating the database schema
    and populating initial gamification data.
    """
    print("Setting up gamification features...")
    
    # Check if database exists
    if not os.path.exists('growth_navigator.db'):
        print("Database does not exist. Please run the application first to create it.")
        return
    
    # Update database schema
    print("\n1. Updating database schema...")
    update_database_schema()
    
    # Populate gamification data
    print("\n2. Populating gamification data...")
    populate_gamification_data()
    
    print("\nGamification setup complete! You can now use the gamification features.")
    print("Visit the Achievements and Challenges pages to see the new features.")

if __name__ == "__main__":
    setup_gamification()
