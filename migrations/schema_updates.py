import sqlite3
import os

def update_database_schema():
    """
    Update the database schema to support gamification features.
    This script adds new tables and columns to the existing database.
    """
    # Connect to the database
    conn = sqlite3.connect('growth_navigator.db')
    cursor = conn.cursor()

    # Check if database exists
    if not os.path.exists('growth_navigator.db'):
        print("Database does not exist. Please run the application first to create it.")
        return

    try:
        # 1. Add XP points column to users table if it doesn't exist
        try:
            cursor.execute('''
            ALTER TABLE users ADD COLUMN xp_points INTEGER DEFAULT 0
            ''')
            print("Added xp_points column to users table")
        except sqlite3.Error as e:
            if "duplicate column name" in str(e):
                print("xp_points column already exists in users table")
            else:
                raise e

        # Add level column if it doesn't exist
        try:
            cursor.execute('''
            ALTER TABLE users ADD COLUMN level INTEGER DEFAULT 1
            ''')
            print("Added level column to users table")
        except sqlite3.Error as e:
            if "duplicate column name" in str(e):
                print("level column already exists in users table")
            else:
                raise e

        # 2. Create achievements table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            icon TEXT NOT NULL,
            category TEXT NOT NULL,
            tier TEXT NOT NULL,
            xp_reward INTEGER NOT NULL,
            requirement_type TEXT NOT NULL,
            requirement_value INTEGER NOT NULL
        )
        ''')

        # 3. Create user_achievements table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            achievement_id INTEGER NOT NULL,
            unlocked_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (achievement_id) REFERENCES achievements (id)
        )
        ''')

        # 4. Create levels table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS levels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level_number INTEGER NOT NULL,
            title TEXT NOT NULL,
            min_xp INTEGER NOT NULL,
            max_xp INTEGER NOT NULL
        )
        ''')

        # 5. Create xp_transactions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS xp_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            source TEXT NOT NULL,
            source_id INTEGER,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')

        # 6. Create challenges table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            xp_reward INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1
        )
        ''')

        # 7. Create user_challenges table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            challenge_id INTEGER NOT NULL,
            status TEXT DEFAULT 'in_progress',
            progress INTEGER DEFAULT 0,
            completed_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (challenge_id) REFERENCES challenges (id)
        )
        ''')

        # 8. Create growth_metaphors table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS growth_metaphors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            metaphor_type TEXT NOT NULL,
            current_stage INTEGER DEFAULT 1,
            max_stage INTEGER NOT NULL,
            growth_points INTEGER DEFAULT 0,
            last_updated TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')

        # Commit the changes
        conn.commit()
        print("Database schema updated successfully!")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_database_schema()
