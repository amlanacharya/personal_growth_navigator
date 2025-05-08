# notification_scheduler.py
import threading
import time
import sqlite3
import json
from datetime import datetime, timedelta
from src.ai.helpers.ai_notification_helper import AINotificationHelper

class NotificationScheduler:
    """
    A background scheduler for checking notification triggers and generating notifications.
    """

    def __init__(self, check_interval=300):
        """
        Initialize the notification scheduler.

        Args:
            check_interval (int): Interval in seconds between checks (default: 300 seconds / 5 minutes)
        """
        self.check_interval = check_interval
        self.running = False
        self.thread = None
        self.notification_helper = AINotificationHelper()
        self.db_path = 'instance/growth_navigator.db'

    def start(self):
        """Start the notification scheduler."""
        if self.running:
            print("Notification scheduler is already running.")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True  # Allow the thread to exit when the main program exits
        self.thread.start()
        print("Notification scheduler started.")

    def stop(self):
        """Stop the notification scheduler."""
        if not self.running:
            print("Notification scheduler is not running.")
            return

        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        print("Notification scheduler stopped.")

    def _run(self):
        """Run the notification scheduler loop."""
        while self.running:
            try:
                self._check_notifications()
            except Exception as e:
                print(f"Error in notification scheduler: {e}")

            # Sleep for the check interval
            time.sleep(self.check_interval)

    def _check_notifications(self):
        """Check for notifications for all users."""
        conn = self._get_db_connection()

        try:
            # Get all users
            users = conn.execute('SELECT id FROM users').fetchall()

            for user in users:
                user_id = user[0]

                # Check notification triggers for this user
                created_notifications = self.notification_helper.check_notification_triggers(user_id)

                if created_notifications:
                    print(f"Created {len(created_notifications)} notifications for user {user_id}")

                    # Check for scheduled notifications
                    self._check_scheduled_notifications(user_id)
        finally:
            conn.close()

    def _check_scheduled_notifications(self, user_id):
        """Check for scheduled notifications for a user."""
        conn = self._get_db_connection()

        try:
            # Get scheduled notifications that are due
            scheduled = conn.execute('''
                SELECT * FROM ai_scheduled_notifications
                WHERE user_id = ? AND scheduled_time <= datetime('now')
                AND (repeat_count > 0 OR repeat_count = -1)
            ''', (user_id,)).fetchall()

            for notification in scheduled:
                # Create the notification
                self._create_scheduled_notification(conn, notification)

                # Update the scheduled notification
                self._update_scheduled_notification(conn, notification)
        finally:
            conn.close()

    def _create_scheduled_notification(self, conn, scheduled):
        """Create a notification from a scheduled notification."""
        # Parse the notification data
        notification_data = json.loads(scheduled['notification_data'])

        # Create the notification
        notification_id = self.notification_helper.create_notification(
            scheduled['user_id'],
            notification_data.get('title', 'Scheduled Notification'),
            notification_data.get('message', 'This is a scheduled notification.'),
            notification_data.get('type', 'reminder'),
            notification_data.get('actions'),
            notification_data.get('important', False),
            'scheduler',
            str(scheduled['id']),
            notification_data.get('metadata')
        )

        return notification_id

    def _update_scheduled_notification(self, conn, scheduled):
        """Update a scheduled notification after it has been triggered."""
        # If this is a repeating notification, update the next scheduled time
        if scheduled['repeat_type']:
            # Calculate the next scheduled time
            next_time = self._calculate_next_scheduled_time(
                scheduled['scheduled_time'],
                scheduled['repeat_type'],
                scheduled['repeat_value']
            )

            # Update the repeat count if it's not infinite (-1)
            repeat_count = scheduled['repeat_count']
            if repeat_count > 0:
                repeat_count -= 1

            # Update the scheduled notification
            conn.execute('''
                UPDATE ai_scheduled_notifications
                SET scheduled_time = ?, repeat_count = ?, updated_at = ?
                WHERE id = ?
            ''', (
                next_time,
                repeat_count,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                scheduled['id']
            ))

            conn.commit()
        else:
            # This is a one-time notification, mark it as completed
            conn.execute('''
                UPDATE ai_scheduled_notifications
                SET repeat_count = 0, updated_at = ?
                WHERE id = ?
            ''', (
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                scheduled['id']
            ))

            conn.commit()

    def _calculate_next_scheduled_time(self, current_time, repeat_type, repeat_value):
        """Calculate the next scheduled time based on the repeat type and value."""
        current_datetime = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S')

        if repeat_type == 'daily':
            next_time = current_datetime + timedelta(days=repeat_value)
        elif repeat_type == 'weekly':
            next_time = current_datetime + timedelta(weeks=repeat_value)
        elif repeat_type == 'monthly':
            # This is a simplification - doesn't handle month boundaries perfectly
            next_time = current_datetime + timedelta(days=30 * repeat_value)
        elif repeat_type == 'hourly':
            next_time = current_datetime + timedelta(hours=repeat_value)
        elif repeat_type == 'minutes':
            next_time = current_datetime + timedelta(minutes=repeat_value)
        else:
            # Default to daily
            next_time = current_datetime + timedelta(days=1)

        return next_time.strftime('%Y-%m-%d %H:%M:%S')

    def _get_db_connection(self):
        """Get a database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

# Singleton instance
notification_scheduler = NotificationScheduler()

def start_notification_scheduler():
    """Start the notification scheduler."""
    notification_scheduler.start()

def stop_notification_scheduler():
    """Stop the notification scheduler."""
    notification_scheduler.stop()
