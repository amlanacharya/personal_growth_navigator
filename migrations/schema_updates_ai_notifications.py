import sqlite3
import os
from datetime import datetime

def update_database_schema_for_ai_notifications():
    """
    Update the database schema to add tables for AI notifications.
    """
    # Check if database exists
    if not os.path.exists('growth_navigator.db'):
        print("Database does not exist. Please run the main application first.")
        return
    
    # Connect to the database
    conn = sqlite3.connect('growth_navigator.db')
    cursor = conn.cursor()
    
    try:
        # Check if ai_notifications table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_notifications'")
        if cursor.fetchone() is None:
            # Create ai_notifications table
            cursor.execute('''
            CREATE TABLE ai_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                type TEXT NOT NULL,
                actions TEXT,
                read INTEGER DEFAULT 0,
                important INTEGER DEFAULT 0,
                snoozed_until TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                source TEXT,
                source_id TEXT,
                metadata TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            ''')
            print("Created ai_notifications table")
        
        # Check if ai_notification_settings table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_notification_settings'")
        if cursor.fetchone() is None:
            # Create ai_notification_settings table
            cursor.execute('''
            CREATE TABLE ai_notification_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                insights_enabled INTEGER DEFAULT 1,
                suggestions_enabled INTEGER DEFAULT 1,
                alerts_enabled INTEGER DEFAULT 1,
                reminders_enabled INTEGER DEFAULT 1,
                email_notifications INTEGER DEFAULT 0,
                push_notifications INTEGER DEFAULT 0,
                quiet_hours_start TEXT,
                quiet_hours_end TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            ''')
            print("Created ai_notification_settings table")
        
        # Check if ai_notification_triggers table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_notification_triggers'")
        if cursor.fetchone() is None:
            # Create ai_notification_triggers table
            cursor.execute('''
            CREATE TABLE ai_notification_triggers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                type TEXT NOT NULL,
                conditions TEXT,
                template_title TEXT NOT NULL,
                template_message TEXT NOT NULL,
                template_actions TEXT,
                enabled INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
            ''')
            print("Created ai_notification_triggers table")
            
            # Insert default notification triggers
            default_triggers = [
                (
                    'habit_streak_at_risk',
                    'Notify when a habit streak is at risk of being broken',
                    'alert',
                    '{"days_since_last_completion": 1, "min_streak": 3}',
                    'Habit Streak at Risk',
                    'Your {habit_name} streak of {streak} days is at risk! Complete it today to keep your momentum.',
                    '[{"text": "Complete Now", "action": "complete_habit", "url": "/habits/log/{habit_id}"}, {"text": "Remind Later", "action": "snooze"}]',
                    1,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    None
                ),
                (
                    'goal_deadline_approaching',
                    'Notify when a goal deadline is approaching',
                    'reminder',
                    '{"days_until_deadline": 7}',
                    'Goal Deadline Approaching',
                    'Your goal "{goal_description}" is due in {days_until_deadline} days.',
                    '[{"text": "View Goal", "action": "view", "url": "/goals/{goal_id}"}, {"text": "Extend Deadline", "action": "extend_deadline"}]',
                    1,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    None
                ),
                (
                    'mood_pattern_detected',
                    'Notify when a negative mood pattern is detected',
                    'insight',
                    '{"consecutive_low_mood_days": 3, "mood_threshold": 2}',
                    'Mood Pattern Detected',
                    'I\'ve noticed your mood has been lower than usual for several days. Would you like some wellbeing suggestions?',
                    '[{"text": "Get Suggestions", "action": "view", "url": "/ai_mood_suggestions"}, {"text": "Dismiss", "action": "dismiss"}]',
                    1,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    None
                ),
                (
                    'energy_optimization_available',
                    'Notify when energy optimization is available',
                    'suggestion',
                    '{"min_mood_logs": 5}',
                    'Energy Optimization Available',
                    'Based on your energy patterns, I can help optimize your daily schedule for maximum productivity.',
                    '[{"text": "Optimize Schedule", "action": "view", "url": "/ai_energy_optimization"}, {"text": "Later", "action": "snooze"}]',
                    1,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    None
                ),
                (
                    'habit_suggestion',
                    'Suggest new habits based on goals',
                    'suggestion',
                    '{"days_since_last_habit_added": 14, "min_goals_without_habits": 1}',
                    'Habit Suggestions Available',
                    'I\'ve generated some habit suggestions for your goal "{goal_description}".',
                    '[{"text": "View Suggestions", "action": "view", "url": "/ai_suggest_habits/{goal_id}"}, {"text": "Later", "action": "snooze"}]',
                    1,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    None
                )
            ]
            
            cursor.executemany('''
            INSERT INTO ai_notification_triggers 
            (name, description, type, conditions, template_title, template_message, template_actions, enabled, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', default_triggers)
            
            print("Inserted default notification triggers")
        
        # Commit the changes
        conn.commit()
        print("Database schema updated successfully for AI notifications")
        
    except Exception as e:
        conn.rollback()
        print(f"Error updating database schema: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_database_schema_for_ai_notifications()
