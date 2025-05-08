#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AI Notifications routes for the Personal Growth Navigator.
"""

from datetime import datetime
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)

from src.core.models.db import get_db
from src.web.routes.auth import login_required
from src.ai.helpers.ai_notification_helper import AINotificationHelper
from src.core.services.notification_service import NotificationScheduler

bp = Blueprint('ai_notifications', __name__, url_prefix='/ai_notifications')

def get_ai_notification_helper():
    """Get the AI notification helper."""
    return AINotificationHelper()

@bp.route('/')
@login_required
def index():
    """Show AI notifications dashboard."""
    db = get_db()
    
    # Get all notifications
    notifications = db.execute('''
        SELECT * FROM ai_notifications
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (g.user['id'],)).fetchall()
    
    # Get scheduled notifications
    scheduled = db.execute('''
        SELECT * FROM scheduled_notifications
        WHERE user_id = ? AND sent = 0
        ORDER BY scheduled_time
    ''', (g.user['id'],)).fetchall()
    
    # Get notification settings
    settings = db.execute('''
        SELECT * FROM notification_settings
        WHERE user_id = ?
    ''', (g.user['id'],)).fetchone()
    
    # If no settings exist, create default settings
    if not settings:
        db.execute('''
            INSERT INTO notification_settings
            (user_id, enabled, frequency, habit_reminders, mood_prompts, insights, push_enabled)
            VALUES (?, 1, 'daily', 1, 1, 1, 0)
        ''', (g.user['id'],))
        db.commit()
        
        settings = db.execute('''
            SELECT * FROM notification_settings
            WHERE user_id = ?
        ''', (g.user['id'],)).fetchone()
    
    return render_template('ai_notifications.html',
                          notifications=notifications,
                          scheduled=scheduled,
                          settings=settings)

@bp.route('/settings', methods=('GET', 'POST'))
@login_required
def settings():
    """Manage notification settings."""
    if request.method == 'POST':
        enabled = request.form.get('enabled', '0') == '1'
        frequency = request.form.get('frequency', 'daily')
        habit_reminders = request.form.get('habit_reminders', '0') == '1'
        mood_prompts = request.form.get('mood_prompts', '0') == '1'
        insights = request.form.get('insights', '0') == '1'
        push_enabled = request.form.get('push_enabled', '0') == '1'
        
        db = get_db()
        
        # Check if settings exist
        settings = db.execute('''
            SELECT * FROM notification_settings
            WHERE user_id = ?
        ''', (g.user['id'],)).fetchone()
        
        if settings:
            # Update existing settings
            db.execute('''
                UPDATE notification_settings
                SET enabled = ?, frequency = ?, habit_reminders = ?, mood_prompts = ?, insights = ?, push_enabled = ?
                WHERE user_id = ?
            ''', (enabled, frequency, habit_reminders, mood_prompts, insights, push_enabled, g.user['id']))
        else:
            # Create new settings
            db.execute('''
                INSERT INTO notification_settings
                (user_id, enabled, frequency, habit_reminders, mood_prompts, insights, push_enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (g.user['id'], enabled, frequency, habit_reminders, mood_prompts, insights, push_enabled))
        
        db.commit()
        
        flash('Notification settings updated successfully!')
        return redirect(url_for('ai_notifications.index'))
    
    db = get_db()
    settings = db.execute('''
        SELECT * FROM notification_settings
        WHERE user_id = ?
    ''', (g.user['id'],)).fetchone()
    
    # If no settings exist, create default settings
    if not settings:
        db.execute('''
            INSERT INTO notification_settings
            (user_id, enabled, frequency, habit_reminders, mood_prompts, insights, push_enabled)
            VALUES (?, 1, 'daily', 1, 1, 1, 0)
        ''', (g.user['id'],))
        db.commit()
        
        settings = db.execute('''
            SELECT * FROM notification_settings
            WHERE user_id = ?
        ''', (g.user['id'],)).fetchone()
    
    return render_template('ai_notification_settings.html', settings=settings)

@bp.route('/mark_read/<int:id>', methods=('POST',))
@login_required
def mark_read(id):
    """Mark a notification as read."""
    db = get_db()
    
    # Verify the notification belongs to the current user
    notification = db.execute('''
        SELECT * FROM ai_notifications
        WHERE id = ? AND user_id = ?
    ''', (id, g.user['id'])).fetchone()
    
    if notification is None:
        flash('Notification not found or you do not have permission to modify it.')
        return redirect(url_for('ai_notifications.index'))
    
    # Mark as read
    db.execute('''
        UPDATE ai_notifications
        SET read = 1
        WHERE id = ?
    ''', (id,))
    db.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    
    flash('Notification marked as read.')
    return redirect(url_for('ai_notifications.index'))

@bp.route('/mark_all_read', methods=('POST',))
@login_required
def mark_all_read():
    """Mark all notifications as read."""
    db = get_db()
    
    # Mark all as read
    db.execute('''
        UPDATE ai_notifications
        SET read = 1
        WHERE user_id = ?
    ''', (g.user['id'],))
    db.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    
    flash('All notifications marked as read.')
    return redirect(url_for('ai_notifications.index'))

@bp.route('/delete/<int:id>', methods=('POST',))
@login_required
def delete(id):
    """Delete a notification."""
    db = get_db()
    
    # Verify the notification belongs to the current user
    notification = db.execute('''
        SELECT * FROM ai_notifications
        WHERE id = ? AND user_id = ?
    ''', (id, g.user['id'])).fetchone()
    
    if notification is None:
        flash('Notification not found or you do not have permission to delete it.')
        return redirect(url_for('ai_notifications.index'))
    
    # Delete the notification
    db.execute('DELETE FROM ai_notifications WHERE id = ?', (id,))
    db.commit()
    
    flash('Notification deleted successfully.')
    return redirect(url_for('ai_notifications.index'))

@bp.route('/schedule', methods=('POST',))
@login_required
def schedule():
    """Schedule a new notification."""
    title = request.form.get('title', '')
    content = request.form.get('content', '')
    scheduled_time = request.form.get('scheduled_time', '')
    
    if not title or not content or not scheduled_time:
        flash('All fields are required.')
        return redirect(url_for('ai_notifications.index'))
    
    try:
        # Parse the scheduled time
        scheduled_datetime = datetime.strptime(scheduled_time, '%Y-%m-%dT%H:%M')
        
        # Ensure the scheduled time is in the future
        if scheduled_datetime <= datetime.now():
            flash('Scheduled time must be in the future.')
            return redirect(url_for('ai_notifications.index'))
        
        db = get_db()
        
        # Create the scheduled notification
        db.execute('''
            INSERT INTO scheduled_notifications
            (user_id, title, content, scheduled_time, sent)
            VALUES (?, ?, ?, ?, 0)
        ''', (g.user['id'], title, content, scheduled_datetime.strftime('%Y-%m-%d %H:%M:%S')))
        db.commit()
        
        # Restart the notification scheduler to pick up the new notification
        scheduler = NotificationScheduler()
        scheduler.restart()
        
        flash('Notification scheduled successfully.')
        return redirect(url_for('ai_notifications.index'))
    
    except ValueError:
        flash('Invalid date format. Please use the date picker.')
        return redirect(url_for('ai_notifications.index'))

@bp.route('/cancel_scheduled/<int:id>', methods=('POST',))
@login_required
def cancel_scheduled(id):
    """Cancel a scheduled notification."""
    db = get_db()
    
    # Verify the notification belongs to the current user
    notification = db.execute('''
        SELECT * FROM scheduled_notifications
        WHERE id = ? AND user_id = ? AND sent = 0
    ''', (id, g.user['id'])).fetchone()
    
    if notification is None:
        flash('Scheduled notification not found, already sent, or you do not have permission to cancel it.')
        return redirect(url_for('ai_notifications.index'))
    
    # Delete the scheduled notification
    db.execute('DELETE FROM scheduled_notifications WHERE id = ?', (id,))
    db.commit()
    
    flash('Scheduled notification cancelled successfully.')
    return redirect(url_for('ai_notifications.index'))

@bp.route('/generate', methods=('POST',))
@login_required
def generate():
    """Generate a new AI notification."""
    notification_type = request.form.get('type', 'general')
    
    helper = get_ai_notification_helper()
    notification = helper.generate_notification(g.user['id'], notification_type)
    
    if notification:
        flash('New notification generated successfully.')
    else:
        flash('Failed to generate notification. Please try again later.')
    
    return redirect(url_for('ai_notifications.index'))

@bp.route('/register_device', methods=('POST',))
@login_required
def register_device():
    """Register a device for push notifications."""
    subscription = request.json
    
    if not subscription:
        return jsonify({'success': False, 'error': 'Invalid subscription data'})
    
    helper = get_ai_notification_helper()
    success = helper.register_device(g.user['id'], subscription)
    
    return jsonify({'success': success})
