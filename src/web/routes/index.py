#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Index route for the Personal Growth Navigator.
"""

from datetime import datetime, date
from flask import Blueprint, render_template, g

from src.core.models.db import get_db
from src.core.services.helpers import get_gamification_helper, get_ai_notification_helper

bp = Blueprint('index', __name__)

def get_current_user():
    """Get the current user."""
    if g.user:
        return g.user
    return None

def get_partner():
    """Get the partner of the current user."""
    user = get_current_user()
    if user and 'partner_id' in user.keys() and user['partner_id']:
        db = get_db()
        partner = db.execute('SELECT * FROM users WHERE id = ?', (user['partner_id'],)).fetchone()
        return partner
    return None

@bp.route('/')
def index():
    """Show the home page."""
    if g.user:
        user_id = g.user['id']
        db = get_db()

        # Get goals
        goals = db.execute('SELECT * FROM goals WHERE user_id = ? AND status = "active" ORDER BY priority',
                        (user_id,)).fetchall()

        # Get today's routine
        today_name = datetime.now().strftime('%A')
        routines = db.execute('SELECT * FROM routines WHERE user_id = ? AND weekdays LIKE ? ORDER BY time_block',
                           (user_id, f'%{today_name}%')).fetchall()

        # Get habits
        habits = db.execute('''
            SELECT h.*, g.description as goal_description,
            (SELECT COUNT(*) FROM habit_logs hl WHERE hl.habit_id = h.id AND hl.completed_date = ?) as completed_today
            FROM habits h
            LEFT JOIN goals g ON h.goal_id = g.id
            WHERE h.user_id = ?
        ''', (date.today().strftime('%Y-%m-%d'), user_id)).fetchall()

        # Get completion data for calendar view
        habit_logs = db.execute('''
            SELECT hl.habit_id, hl.completed_date, COUNT(*) as count
            FROM habit_logs hl
            JOIN habits h ON hl.habit_id = h.id
            WHERE h.user_id = ?
            GROUP BY hl.habit_id, hl.completed_date
        ''', (user_id,)).fetchall()

        # Convert to format needed for calendar
        calendar_data = {}
        for log in habit_logs:
            habit_id = log[0]
            completed_date = log[1]

            if habit_id not in calendar_data:
                calendar_data[habit_id] = []

            calendar_data[habit_id].append(completed_date)

        # Get user level info
        helper = get_gamification_helper()
        level_info = helper.get_user_level_info(user_id)

        # Get mood history for the last 7 days
        mood_history = db.execute('''
            SELECT mood_score, mood_note, energy_level, logged_at
            FROM mood_logs
            WHERE user_id = ?
            ORDER BY logged_at DESC
            LIMIT 7
        ''', (user_id,)).fetchall()

        # Format the mood history data
        formatted_mood_history = []
        for entry in mood_history:
            formatted_mood_history.append({
                'mood_score': entry[0],
                'mood_note': entry[1],
                'energy_level': entry[2],
                'logged_at': datetime.strptime(entry[3], '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y')
            })

        # Check if mood logged today
        today = date.today().strftime('%Y-%m-%d')
        mood_today = db.execute('''
            SELECT mood_score FROM mood_logs
            WHERE user_id = ? AND date(logged_at) = ?
        ''', (user_id, today)).fetchone()

        # Get unread notifications
        notification_helper = get_ai_notification_helper()
        notifications = notification_helper.get_user_notifications(user_id, 5, False)

        return render_template('index.html',
                              goals=goals,
                              routines=routines,
                              habits=habits,
                              today=date.today().strftime('%Y-%m-%d'),
                              now=datetime.now(),
                              current_user=get_current_user(),
                              partner=get_partner(),
                              level_info=level_info,
                              calendar_data=calendar_data,
                              mood_history=formatted_mood_history,
                              mood_today=mood_today[0] if mood_today else None,
                              notifications=notifications,
                              use_custom_energy_legend=True)

    return render_template('welcome.html')
