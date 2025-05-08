import sqlite3
import os
from config.config import DATABASE

def update_database_schema_for_mood():
    """
    Update the database schema to support mood tracking.
    This script adds a new table for mood tracking.
    """
    # Connect to the database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Check if database exists
    if not os.path.exists(DATABASE):
        print(f"Database does not exist at {DATABASE}. Please run the application first to create it.")
        return

    try:
        # Create mood_logs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS mood_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mood_score INTEGER NOT NULL,
            mood_note TEXT,
            energy_level INTEGER NOT NULL,
            logged_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')

        # Commit the changes
        conn.commit()
        print("Mood tracking table created successfully!")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_database_schema_for_mood()
