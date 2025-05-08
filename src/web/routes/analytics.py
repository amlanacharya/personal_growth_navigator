#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Analytics routes for the Personal Growth Navigator.
"""

from datetime import datetime, date, timedelta
from flask import (
    Blueprint, render_template, g
)

from src.core.models.db import get_db
from src.web.routes.auth import login_required

bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@bp.route('/')
@login_required
def index():
    """Show analytics dashboard."""
    db = get_db()
    
    # Get habit completion rates
    habits = db.execute('''
        SELECT h.id, h.name, h.created_at,
        (SELECT COUNT(*) FROM habit_logs hl WHERE hl.habit_id = h.id) as total_completions,
        (julianday('now') - julianday(h.created_at)) as days_since_creation
        FROM habits h
        WHERE h.user_id = ?
    ''', (g.user['id'],)).fetchall()
    
    habit_stats = []
    for habit in habits:
        habit_id, name, created_at, total_completions, days_since_creation = habit
        
        if days_since_creation > 0:
            completion_rate = (total_completions / days_since_creation) * 100
        else:
            completion_rate = 0
        
        habit_stats.append({
            'id': habit_id,
            'name': name,
            'created_at': created_at,
            'total_completions': total_completions,
            'days_since_creation': int(days_since_creation),
            'completion_rate': round(completion_rate, 1),
            'current_streak': db.execute('SELECT streak FROM habits WHERE id = ?', (habit_id,)).fetchone()[0]
        })
    
    # Get today's energy distribution
    today_name = datetime.now().strftime('%A')
    energy_distribution = db.execute('''
        SELECT energy_level, SUM(duration) as total_minutes
        FROM routines
        WHERE user_id = ? AND weekdays LIKE ?
        GROUP BY energy_level
    ''', (g.user['id'], f'%{today_name}%')).fetchall()
    
    return render_template('analytics.html', 
                          habit_stats=habit_stats, 
                          energy_distribution=energy_distribution,
                          use_custom_energy_legend=True)

@bp.route('/weekly_summary')
@login_required
def weekly_summary():
    """Show weekly summary."""
    db = get_db()
    
    # Calculate date range for the past week
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    
    # Format dates for display
    start_date_str = start_date.strftime('%b %d, %Y')
    end_date_str = end_date.strftime('%b %d, %Y')
    
    # Get habit completion rate for the week
    total_habits = db.execute('''
        SELECT COUNT(*) FROM habits WHERE user_id = ?
    ''', (g.user['id'],)).fetchone()[0]
    
    completed_habits = db.execute('''
        SELECT COUNT(DISTINCT habit_id) FROM habit_logs
        WHERE habit_id IN (SELECT id FROM habits WHERE user_id = ?)
        AND completed_date BETWEEN ? AND ?
    ''', (g.user['id'], start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))).fetchone()[0]
    
    habit_completion_rate = round((completed_habits / total_habits * 100) if total_habits > 0 else 0)
    
    # Get XP earned this week
    xp_earned = db.execute('''
        SELECT SUM(amount) FROM xp_transactions
        WHERE user_id = ? AND created_at BETWEEN ? AND ?
    ''', (g.user['id'], start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))).fetchone()[0] or 0
    
    # Get focus minutes for the week
    focus_minutes = db.execute('''
        SELECT SUM(duration) FROM routines
        WHERE user_id = ? AND energy_level = 'High'
    ''', (g.user['id'],)).fetchone()[0] or 0
    
    # Get top habits by streak
    top_habits = db.execute('''
        SELECT name, streak FROM habits
        WHERE user_id = ?
        ORDER BY streak DESC
        LIMIT 5
    ''', (g.user['id'],)).fetchall()
    
    formatted_top_habits = []
    for habit in top_habits:
        formatted_top_habits.append({
            'name': habit[0],
            'streak': habit[1]
        })
    
    # Get mood data
    mood_data = db.execute('''
        SELECT mood_score, energy_level, logged_at
        FROM mood_logs
        WHERE user_id = ? AND logged_at BETWEEN ? AND ?
        ORDER BY logged_at
    ''', (g.user['id'], start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))).fetchall()
    
    # Calculate average mood
    avg_mood = 0
    highest_energy_day = "N/A"
    highest_energy = 0
    
    if mood_data:
        total_mood = sum(entry[0] for entry in mood_data)
        avg_mood = round(total_mood / len(mood_data), 1)
        
        # Find highest energy day
        for entry in mood_data:
            if entry[1] > highest_energy:
                highest_energy = entry[1]
                highest_energy_day = datetime.strptime(entry[2], '%Y-%m-%d %H:%M:%S').strftime('%A')
    
    return render_template('weekly_summary.html',
                          start_date=start_date_str,
                          end_date=end_date_str,
                          habit_completion_rate=habit_completion_rate,
                          xp_earned=xp_earned,
                          focus_minutes=focus_minutes,
                          top_habits=formatted_top_habits,
                          avg_mood=avg_mood,
                          highest_energy_day=highest_energy_day)
