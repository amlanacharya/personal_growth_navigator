# schema_updates_scheduled_notifications.py
import sqlite3
import os
from datetime import datetime
from config.config import DATABASE

def update_database_schema_for_scheduled_notifications():
    """Update the database schema to add scheduled notifications tables."""
    if not os.path.exists(DATABASE):
        print(f"Database file not found at {DATABASE}. Schema update for scheduled notifications skipped.")
        return

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Check if the ai_scheduled_notifications table already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_scheduled_notifications'")
    if cursor.fetchone() is None:
        print("Creating ai_scheduled_notifications table...")

        # Create the ai_scheduled_notifications table
        cursor.execute('''
        CREATE TABLE ai_scheduled_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            notification_data TEXT NOT NULL,
            scheduled_time TEXT NOT NULL,
            repeat_type TEXT,
            repeat_value INTEGER,
            repeat_count INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')

        print("ai_scheduled_notifications table created successfully.")
    else:
        print("ai_scheduled_notifications table already exists.")

    # Check if the push_notification_subscriptions table already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='push_notification_subscriptions'")
    if cursor.fetchone() is None:
        print("Creating push_notification_subscriptions table...")

        # Create the push_notification_subscriptions table
        cursor.execute('''
        CREATE TABLE push_notification_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            endpoint TEXT NOT NULL,
            p256dh TEXT NOT NULL,
            auth TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')

        print("push_notification_subscriptions table created successfully.")
    else:
        print("push_notification_subscriptions table already exists.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_database_schema_for_scheduled_notifications()
