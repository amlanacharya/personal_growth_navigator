import sqlite3
import json
from datetime import datetime, timedelta
import re

class AINotificationHelper:
    def __init__(self):
        """Initialize the AI Notification Helper."""
        self.db_path = 'growth_navigator.db'
    
    def get_db_connection(self):
        """Get a database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_user_notifications(self, user_id, limit=20, include_read=False):
        """
        Get notifications for a user.
        
        Args:
            user_id (int): The user's ID
            limit (int): Maximum number of notifications to return
            include_read (bool): Whether to include read notifications
            
        Returns:
            list: A list of notification objects
        """
        conn = self.get_db_connection()
        
        try:
            query = '''
                SELECT * FROM ai_notifications 
                WHERE user_id = ? 
                AND (snoozed_until IS NULL OR snoozed_until <= datetime('now'))
            '''
            
            if not include_read:
                query += ' AND read = 0'
                
            query += ' ORDER BY created_at DESC LIMIT ?'
            
            notifications = conn.execute(query, (user_id, limit)).fetchall()
            
            # Convert to list of dicts and parse JSON fields
            result = []
            for notification in notifications:
                notification_dict = dict(notification)
                
                # Parse actions JSON
                if notification_dict['actions']:
                    try:
                        notification_dict['actions'] = json.loads(notification_dict['actions'])
                    except json.JSONDecodeError:
                        notification_dict['actions'] = []
                else:
                    notification_dict['actions'] = []
                
                # Parse metadata JSON
                if notification_dict['metadata']:
                    try:
                        notification_dict['metadata'] = json.loads(notification_dict['metadata'])
                    except json.JSONDecodeError:
                        notification_dict['metadata'] = {}
                else:
                    notification_dict['metadata'] = {}
                
                result.append(notification_dict)
            
            return result
            
        finally:
            conn.close()
    
    def create_notification(self, user_id, title, message, notification_type, actions=None, important=False, source=None, source_id=None, metadata=None):
        """
        Create a new notification for a user.
        
        Args:
            user_id (int): The user's ID
            title (str): Notification title
            message (str): Notification message
            notification_type (str): Type of notification (insight, suggestion, alert, reminder)
            actions (list): List of action objects with text, action, and optional url
            important (bool): Whether this is an important notification
            source (str): Source of the notification (e.g., 'habit', 'goal')
            source_id (str): ID of the source object
            metadata (dict): Additional metadata for the notification
            
        Returns:
            int: The ID of the created notification
        """
        conn = self.get_db_connection()
        
        try:
            # Check user notification settings
            settings = self.get_user_notification_settings(user_id)
            
            # Check if this type of notification is enabled
            setting_key = f"{notification_type}s_enabled"
            if setting_key in settings and not settings[setting_key]:
                return None
            
            # Check quiet hours
            if settings.get('quiet_hours_start') and settings.get('quiet_hours_end'):
                now = datetime.now().time()
                start = datetime.strptime(settings['quiet_hours_start'], '%H:%M').time()
                end = datetime.strptime(settings['quiet_hours_end'], '%H:%M').time()
                
                # Check if current time is within quiet hours
                if self._is_time_between(now, start, end) and not important:
                    return None
            
            # Prepare actions JSON
            actions_json = json.dumps(actions) if actions else None
            
            # Prepare metadata JSON
            metadata_json = json.dumps(metadata) if metadata else None
            
            # Insert notification
            cursor = conn.execute('''
                INSERT INTO ai_notifications 
                (user_id, title, message, type, actions, important, source, source_id, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, 
                title, 
                message, 
                notification_type, 
                actions_json, 
                1 if important else 0, 
                source, 
                source_id, 
                metadata_json, 
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            
            notification_id = cursor.lastrowid
            conn.commit()
            
            return notification_id
            
        finally:
            conn.close()
    
    def mark_notification_read(self, notification_id, user_id=None):
        """
        Mark a notification as read.
        
        Args:
            notification_id (int): The notification ID
            user_id (int): Optional user ID for security check
            
        Returns:
            bool: True if successful, False otherwise
        """
        conn = self.get_db_connection()
        
        try:
            query = 'UPDATE ai_notifications SET read = 1, updated_at = ? WHERE id = ?'
            params = (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), notification_id)
            
            # Add user_id check if provided
            if user_id:
                query += ' AND user_id = ?'
                params = params + (user_id,)
            
            conn.execute(query, params)
            conn.commit()
            
            return True
            
        except Exception as e:
            print(f"Error marking notification as read: {e}")
            return False
            
        finally:
            conn.close()
    
    def mark_all_notifications_read(self, user_id):
        """
        Mark all notifications as read for a user.
        
        Args:
            user_id (int): The user's ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        conn = self.get_db_connection()
        
        try:
            conn.execute('''
                UPDATE ai_notifications 
                SET read = 1, updated_at = ? 
                WHERE user_id = ? AND read = 0
            ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error marking all notifications as read: {e}")
            return False
            
        finally:
            conn.close()
    
    def snooze_notification(self, notification_id, user_id=None, hours=3):
        """
        Snooze a notification for a specified number of hours.
        
        Args:
            notification_id (int): The notification ID
            user_id (int): Optional user ID for security check
            hours (int): Number of hours to snooze
            
        Returns:
            bool: True if successful, False otherwise
        """
        conn = self.get_db_connection()
        
        try:
            snooze_until = (datetime.now() + timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
            
            query = '''
                UPDATE ai_notifications 
                SET snoozed_until = ?, updated_at = ? 
                WHERE id = ?
            '''
            params = (snooze_until, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), notification_id)
            
            # Add user_id check if provided
            if user_id:
                query += ' AND user_id = ?'
                params = params + (user_id,)
            
            conn.execute(query, params)
            conn.commit()
            
            return True
            
        except Exception as e:
            print(f"Error snoozing notification: {e}")
            return False
            
        finally:
            conn.close()
    
    def delete_notification(self, notification_id, user_id=None):
        """
        Delete a notification.
        
        Args:
            notification_id (int): The notification ID
            user_id (int): Optional user ID for security check
            
        Returns:
            bool: True if successful, False otherwise
        """
        conn = self.get_db_connection()
        
        try:
            query = 'DELETE FROM ai_notifications WHERE id = ?'
            params = (notification_id,)
            
            # Add user_id check if provided
            if user_id:
                query += ' AND user_id = ?'
                params = params + (user_id,)
            
            conn.execute(query, params)
            conn.commit()
            
            return True
            
        except Exception as e:
            print(f"Error deleting notification: {e}")
            return False
            
        finally:
            conn.close()
    
    def get_user_notification_settings(self, user_id):
        """
        Get notification settings for a user.
        
        Args:
            user_id (int): The user's ID
            
        Returns:
            dict: User notification settings
        """
        conn = self.get_db_connection()
        
        try:
            # Check if settings exist for this user
            settings = conn.execute('SELECT * FROM ai_notification_settings WHERE user_id = ?', (user_id,)).fetchone()
            
            if not settings:
                # Create default settings
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                conn.execute('''
                    INSERT INTO ai_notification_settings 
                    (user_id, insights_enabled, suggestions_enabled, alerts_enabled, reminders_enabled, 
                     email_notifications, push_notifications, created_at)
                    VALUES (?, 1, 1, 1, 1, 0, 0, ?)
                ''', (user_id, now))
                
                conn.commit()
                
                # Get the newly created settings
                settings = conn.execute('SELECT * FROM ai_notification_settings WHERE user_id = ?', (user_id,)).fetchone()
            
            return dict(settings)
            
        finally:
            conn.close()
    
    def update_user_notification_settings(self, user_id, settings):
        """
        Update notification settings for a user.
        
        Args:
            user_id (int): The user's ID
            settings (dict): Updated settings
            
        Returns:
            bool: True if successful, False otherwise
        """
        conn = self.get_db_connection()
        
        try:
            # Ensure settings exist
            self.get_user_notification_settings(user_id)
            
            # Update settings
            set_clauses = []
            params = []
            
            for key, value in settings.items():
                if key in ['insights_enabled', 'suggestions_enabled', 'alerts_enabled', 'reminders_enabled', 
                          'email_notifications', 'push_notifications', 'quiet_hours_start', 'quiet_hours_end']:
                    set_clauses.append(f"{key} = ?")
                    params.append(value)
            
            if not set_clauses:
                return False
            
            set_clauses.append("updated_at = ?")
            params.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            params.append(user_id)
            
            query = f'''
                UPDATE ai_notification_settings 
                SET {', '.join(set_clauses)} 
                WHERE user_id = ?
            '''
            
            conn.execute(query, params)
            conn.commit()
            
            return True
            
        except Exception as e:
            print(f"Error updating notification settings: {e}")
            return False
            
        finally:
            conn.close()
    
    def check_notification_triggers(self, user_id):
        """
        Check all notification triggers for a user and create notifications if conditions are met.
        
        Args:
            user_id (int): The user's ID
            
        Returns:
            list: List of created notification IDs
        """
        conn = self.get_db_connection()
        
        try:
            # Get all enabled triggers
            triggers = conn.execute('SELECT * FROM ai_notification_triggers WHERE enabled = 1').fetchall()
            
            created_notifications = []
            
            for trigger in triggers:
                # Parse conditions
                conditions = json.loads(trigger['conditions'])
                
                # Check if conditions are met
                if self._check_trigger_conditions(conn, user_id, trigger['name'], conditions):
                    # Create notification based on trigger template
                    notification_id = self._create_notification_from_trigger(conn, user_id, trigger)
                    
                    if notification_id:
                        created_notifications.append(notification_id)
            
            return created_notifications
            
        finally:
            conn.close()
    
    def _check_trigger_conditions(self, conn, user_id, trigger_name, conditions):
        """
        Check if conditions for a trigger are met.
        
        Args:
            conn: Database connection
            user_id (int): The user's ID
            trigger_name (str): Name of the trigger
            conditions (dict): Trigger conditions
            
        Returns:
            bool: True if conditions are met, False otherwise
        """
        if trigger_name == 'habit_streak_at_risk':
            return self._check_habit_streak_at_risk(conn, user_id, conditions)
        elif trigger_name == 'goal_deadline_approaching':
            return self._check_goal_deadline_approaching(conn, user_id, conditions)
        elif trigger_name == 'mood_pattern_detected':
            return self._check_mood_pattern_detected(conn, user_id, conditions)
        elif trigger_name == 'energy_optimization_available':
            return self._check_energy_optimization_available(conn, user_id, conditions)
        elif trigger_name == 'habit_suggestion':
            return self._check_habit_suggestion(conn, user_id, conditions)
        
        return False
    
    def _create_notification_from_trigger(self, conn, user_id, trigger):
        """
        Create a notification based on a trigger template.
        
        Args:
            conn: Database connection
            user_id (int): The user's ID
            trigger (dict): Trigger data
            
        Returns:
            int: Notification ID if created, None otherwise
        """
        # Get data for template variables
        template_data = self._get_template_data(conn, user_id, trigger['name'])
        
        if not template_data:
            return None
        
        # Replace template variables in title and message
        title = self._replace_template_variables(trigger['template_title'], template_data)
        message = self._replace_template_variables(trigger['template_message'], template_data)
        
        # Parse and process actions
        actions = json.loads(trigger['template_actions']) if trigger['template_actions'] else []
        
        for action in actions:
            if 'url' in action:
                action['url'] = self._replace_template_variables(action['url'], template_data)
        
        # Create notification
        important = trigger['type'] == 'alert'
        source = trigger['name']
        source_id = str(template_data.get('id', ''))
        
        # Check if a similar notification already exists
        existing = conn.execute('''
            SELECT id FROM ai_notifications 
            WHERE user_id = ? AND source = ? AND source_id = ? AND read = 0
            AND (snoozed_until IS NULL OR snoozed_until <= datetime('now'))
        ''', (user_id, source, source_id)).fetchone()
        
        if existing:
            return None
        
        # Create the notification
        notification_id = self.create_notification(
            user_id, 
            title, 
            message, 
            trigger['type'], 
            actions, 
            important, 
            source, 
            source_id, 
            template_data
        )
        
        return notification_id
    
    def _get_template_data(self, conn, user_id, trigger_name):
        """
        Get data for template variables based on trigger name.
        
        Args:
            conn: Database connection
            user_id (int): The user's ID
            trigger_name (str): Name of the trigger
            
        Returns:
            dict: Data for template variables
        """
        if trigger_name == 'habit_streak_at_risk':
            return self._get_habit_streak_at_risk_data(conn, user_id)
        elif trigger_name == 'goal_deadline_approaching':
            return self._get_goal_deadline_approaching_data(conn, user_id)
        elif trigger_name == 'mood_pattern_detected':
            return self._get_mood_pattern_data(conn, user_id)
        elif trigger_name == 'energy_optimization_available':
            return self._get_energy_optimization_data(conn, user_id)
        elif trigger_name == 'habit_suggestion':
            return self._get_habit_suggestion_data(conn, user_id)
        
        return {}
    
    def _replace_template_variables(self, template, data):
        """
        Replace template variables with actual data.
        
        Args:
            template (str): Template string with {variable} placeholders
            data (dict): Data for template variables
            
        Returns:
            str: Template with variables replaced
        """
        # Use regex to find all {variable} patterns
        pattern = r'\{([^}]+)\}'
        
        def replace_var(match):
            var_name = match.group(1)
            return str(data.get(var_name, match.group(0)))
        
        return re.sub(pattern, replace_var, template)
    
    def _is_time_between(self, time, start, end):
        """
        Check if a time is between start and end times.
        
        Args:
            time: Time to check
            start: Start time
            end: End time
            
        Returns:
            bool: True if time is between start and end
        """
        if start <= end:
            return start <= time <= end
        else:  # Over midnight
            return start <= time or time <= end
    
    # Trigger condition checkers
    
    def _check_habit_streak_at_risk(self, conn, user_id, conditions):
        """Check if any habit streaks are at risk."""
        days_since_last = conditions.get('days_since_last_completion', 1)
        min_streak = conditions.get('min_streak', 3)
        
        # Find habits with streaks at risk
        cutoff_date = (datetime.now() - timedelta(days=days_since_last)).strftime('%Y-%m-%d')
        
        at_risk_habits = conn.execute('''
            SELECT h.id, h.name, h.streak
            FROM habits h
            LEFT JOIN habit_logs hl ON h.id = hl.habit_id AND hl.completed_date >= ?
            WHERE h.user_id = ? AND h.streak >= ? AND hl.id IS NULL
            GROUP BY h.id
        ''', (cutoff_date, user_id, min_streak)).fetchall()
        
        return len(at_risk_habits) > 0
    
    def _check_goal_deadline_approaching(self, conn, user_id, conditions):
        """Check if any goal deadlines are approaching."""
        days_until_deadline = conditions.get('days_until_deadline', 7)
        
        # Calculate the date range
        future_date = (datetime.now() + timedelta(days=days_until_deadline)).strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Find goals with approaching deadlines
        approaching_goals = conn.execute('''
            SELECT id, description, deadline
            FROM goals
            WHERE user_id = ? AND status = 'active' AND deadline BETWEEN ? AND ?
        ''', (user_id, today, future_date)).fetchall()
        
        return len(approaching_goals) > 0
    
    def _check_mood_pattern_detected(self, conn, user_id, conditions):
        """Check if a negative mood pattern is detected."""
        consecutive_days = conditions.get('consecutive_low_mood_days', 3)
        mood_threshold = conditions.get('mood_threshold', 2)
        
        # Get recent mood logs
        mood_logs = conn.execute('''
            SELECT mood_score, logged_at
            FROM mood_logs
            WHERE user_id = ?
            ORDER BY logged_at DESC
            LIMIT ?
        ''', (user_id, consecutive_days)).fetchall()
        
        # Check if we have enough logs
        if len(mood_logs) < consecutive_days:
            return False
        
        # Check if all recent moods are below threshold
        low_mood_count = sum(1 for log in mood_logs if log['mood_score'] <= mood_threshold)
        
        return low_mood_count >= consecutive_days
    
    def _check_energy_optimization_available(self, conn, user_id, conditions):
        """Check if energy optimization is available."""
        min_mood_logs = conditions.get('min_mood_logs', 5)
        
        # Count mood logs with energy data
        mood_log_count = conn.execute('''
            SELECT COUNT(*) as count
            FROM mood_logs
            WHERE user_id = ? AND energy_level IS NOT NULL
        ''', (user_id,)).fetchone()['count']
        
        # Check if user has routines
        routine_count = conn.execute('''
            SELECT COUNT(*) as count
            FROM routines
            WHERE user_id = ?
        ''', (user_id,)).fetchone()['count']
        
        # Check if optimization notification was sent recently
        recent_notification = conn.execute('''
            SELECT id
            FROM ai_notifications
            WHERE user_id = ? AND source = 'energy_optimization_available'
            AND created_at > datetime('now', '-7 days')
        ''', (user_id,)).fetchone()
        
        return mood_log_count >= min_mood_logs and routine_count > 0 and not recent_notification
    
    def _check_habit_suggestion(self, conn, user_id, conditions):
        """Check if habit suggestions should be offered."""
        days_since_last = conditions.get('days_since_last_habit_added', 14)
        min_goals_without_habits = conditions.get('min_goals_without_habits', 1)
        
        # Check when the last habit was added
        last_habit = conn.execute('''
            SELECT created_at
            FROM habits
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (user_id,)).fetchone()
        
        if last_habit:
            last_habit_date = datetime.strptime(last_habit['created_at'], '%Y-%m-%d')
            days_since = (datetime.now().date() - last_habit_date.date()).days
            if days_since < days_since_last:
                return False
        
        # Find goals without habits
        goals_without_habits = conn.execute('''
            SELECT g.id
            FROM goals g
            LEFT JOIN habits h ON g.id = h.goal_id
            WHERE g.user_id = ? AND g.status = 'active' AND h.id IS NULL
            GROUP BY g.id
        ''', (user_id,)).fetchall()
        
        return len(goals_without_habits) >= min_goals_without_habits
    
    # Data getters for templates
    
    def _get_habit_streak_at_risk_data(self, conn, user_id):
        """Get data for habit streak at risk notification."""
        cutoff_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        habit = conn.execute('''
            SELECT h.id, h.name, h.streak
            FROM habits h
            LEFT JOIN habit_logs hl ON h.id = hl.habit_id AND hl.completed_date >= ?
            WHERE h.user_id = ? AND h.streak >= 3 AND hl.id IS NULL
            GROUP BY h.id
            ORDER BY h.streak DESC
            LIMIT 1
        ''', (cutoff_date, user_id)).fetchone()
        
        if not habit:
            return None
        
        return {
            'id': habit['id'],
            'habit_id': habit['id'],
            'habit_name': habit['name'],
            'streak': habit['streak']
        }
    
    def _get_goal_deadline_approaching_data(self, conn, user_id):
        """Get data for goal deadline approaching notification."""
        future_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')
        
        goal = conn.execute('''
            SELECT id, description, deadline
            FROM goals
            WHERE user_id = ? AND status = 'active' AND deadline BETWEEN ? AND ?
            ORDER BY deadline ASC
            LIMIT 1
        ''', (user_id, today, future_date)).fetchone()
        
        if not goal:
            return None
        
        deadline_date = datetime.strptime(goal['deadline'], '%Y-%m-%d').date()
        days_until = (deadline_date - datetime.now().date()).days
        
        return {
            'id': goal['id'],
            'goal_id': goal['id'],
            'goal_description': goal['description'],
            'deadline': goal['deadline'],
            'days_until_deadline': days_until
        }
    
    def _get_mood_pattern_data(self, conn, user_id):
        """Get data for mood pattern notification."""
        # This doesn't need specific data from the database
        return {
            'id': 'mood_pattern'
        }
    
    def _get_energy_optimization_data(self, conn, user_id):
        """Get data for energy optimization notification."""
        # This doesn't need specific data from the database
        return {
            'id': 'energy_optimization'
        }
    
    def _get_habit_suggestion_data(self, conn, user_id):
        """Get data for habit suggestion notification."""
        goal = conn.execute('''
            SELECT g.id, g.description
            FROM goals g
            LEFT JOIN habits h ON g.id = h.goal_id
            WHERE g.user_id = ? AND g.status = 'active' AND h.id IS NULL
            GROUP BY g.id
            LIMIT 1
        ''', (user_id,)).fetchone()
        
        if not goal:
            return None
        
        return {
            'id': goal['id'],
            'goal_id': goal['id'],
            'goal_description': goal['description']
        }
