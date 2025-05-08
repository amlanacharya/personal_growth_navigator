#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Habit routes for the Personal Growth Navigator.
"""

import json
from datetime import date, datetime
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)

from src.core.models.db import get_db
from src.web.routes.auth import login_required
from src.core.services.gamification_service import GamificationHelper

bp = Blueprint('habits', __name__, url_prefix='/habits')

def get_gamification_helper():
    """Get the gamification helper."""
    return GamificationHelper()

@bp.route('/')
@login_required
def index():
    """Show all habits."""
    user_id = g.user['id']
    db = get_db()

    # Get habits with goal descriptions
    habits = db.execute('''
        SELECT h.*, g.description as goal_description
        FROM habits h
        LEFT JOIN goals g ON h.goal_id = g.id
        WHERE h.user_id = ?
        ORDER BY h.name
    ''', (user_id,)).fetchall()

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

    return render_template('habits.html',
                          habits=habits,
                          calendar_data=calendar_data,
                          today=date.today().strftime('%Y-%m-%d'))

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    """Create a new habit."""
    if request.method == 'POST':
        name = request.form['name']
        goal_id = request.form['goal_id'] if request.form['goal_id'] != '' else None
        frequency = request.form['frequency']

        error = None

        if not name:
            error = 'Name is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO habits (user_id, name, goal_id, frequency, streak, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                (g.user['id'], name, goal_id, frequency, 0, datetime.now().strftime('%Y-%m-%d'))
            )
            db.commit()

            flash('Habit added successfully!')
            return redirect(url_for('habits.index'))

    # Get goals for the dropdown
    db = get_db()
    goals = db.execute(
        'SELECT id, description FROM goals WHERE user_id = ? AND status = "active"',
        (g.user['id'],)
    ).fetchall()

    return render_template('add_habit.html', goals=goals)

@bp.route('/add', methods=('GET', 'POST'))
@login_required
def add():
    """Add a new habit (alias for create)."""
    return create()

@bp.route('/edit/<int:id>', methods=('GET', 'POST'))
@login_required
def edit(id):
    """Edit a habit."""
    db = get_db()
    habit = db.execute(
        'SELECT * FROM habits WHERE id = ? AND user_id = ?',
        (id, g.user['id'])
    ).fetchone()

    if habit is None:
        flash('Habit not found or you do not have permission to edit it.')
        return redirect(url_for('habits.index'))

    if request.method == 'POST':
        name = request.form['name']
        goal_id = request.form['goal_id'] if request.form['goal_id'] != '' else None
        frequency = request.form['frequency']
        streak = int(request.form['streak'])

        error = None

        if not name:
            error = 'Name is required.'

        if error is not None:
            flash(error)
        else:
            db.execute(
                'UPDATE habits SET name = ?, goal_id = ?, frequency = ?, streak = ? WHERE id = ? AND user_id = ?',
                (name, goal_id, frequency, streak, id, g.user['id'])
            )
            db.commit()

            flash('Habit updated successfully!')
            return redirect(url_for('habits.index'))

    goals = db.execute(
        'SELECT id, description FROM goals WHERE user_id = ? AND status = "active"',
        (g.user['id'],)
    ).fetchall()

    return render_template('edit_habit.html', habit=habit, goals=goals)

@bp.route('/delete/<int:id>', methods=('POST',))
@login_required
def delete(id):
    """Delete a habit."""
    db = get_db()

    # Verify the habit belongs to the current user
    habit = db.execute(
        'SELECT * FROM habits WHERE id = ? AND user_id = ?',
        (id, g.user['id'])
    ).fetchone()

    if habit is None:
        flash('Habit not found or you do not have permission to delete it.')
        return redirect(url_for('habits.index'))

    # Delete habit logs first (foreign key constraint)
    db.execute('DELETE FROM habit_logs WHERE habit_id = ?', (id,))

    # Delete the habit
    db.execute('DELETE FROM habits WHERE id = ? AND user_id = ?', (id, g.user['id']))
    db.commit()

    flash('Habit deleted successfully!')
    return redirect(url_for('habits.index'))

@bp.route('/log/<int:id>', methods=('POST',))
@login_required
def log(id):
    """Log a habit completion."""
    completed = request.form.get('completed', 'false') == 'true'
    today = date.today().strftime('%Y-%m-%d')
    notes = request.form.get('notes', '')

    db = get_db()

    # Verify the habit belongs to the current user
    habit = db.execute(
        'SELECT * FROM habits WHERE id = ? AND user_id = ?',
        (id, g.user['id'])
    ).fetchone()

    if habit is None:
        flash('Habit not found or you do not have permission to log it.')
        return redirect(url_for('habits.index'))

    # Check if already logged today
    existing = db.execute(
        'SELECT id FROM habit_logs WHERE habit_id = ? AND completed_date = ?',
        (id, today)
    ).fetchone()

    # Get the current streak
    current_streak = habit['streak']
    new_streak = current_streak

    # Get gamification helper
    helper = get_gamification_helper()

    if completed:
        if not existing:
            # Add log
            db.execute(
                'INSERT INTO habit_logs (habit_id, completed_date, notes) VALUES (?, ?, ?)',
                (id, today, notes)
            )

            # Update streak
            new_streak = current_streak + 1
            db.execute('UPDATE habits SET streak = ? WHERE id = ?', (new_streak, id))

            # Award XP for completing a habit (10 XP per completion)
            helper.award_xp(db, g.user['id'], 10, 'habit_completion', id, f"Completed habit: {habit['name']}")

            # Check for streak milestones and award bonus XP
            if new_streak in [7, 30, 66, 100]:
                bonus_xp = new_streak  # XP equal to streak milestone
                helper.award_xp(db, g.user['id'], bonus_xp, 'streak_milestone', id,
                               f"Reached {new_streak}-day streak for habit: {habit['name']}")

            db.commit()
            if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                flash('Habit marked as completed!')
    else:
        if existing:
            # Remove log
            db.execute(
                'DELETE FROM habit_logs WHERE habit_id = ? AND completed_date = ?',
                (id, today)
            )

            # Update streak (not reset to 0, just decrement)
            if current_streak > 0:
                new_streak = current_streak - 1
                db.execute('UPDATE habits SET streak = ? WHERE id = ?', (new_streak, id))

            db.commit()
            if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                flash('Habit completion removed!')

    # Check for new achievements
    new_achievements = helper.check_achievements(g.user['id'])

    # Get user level info to check for level up
    level_info = helper.get_user_level_info(g.user['id'])

    # Check for milestone
    milestone = None
    if completed and not existing and new_streak in [7, 30, 66, 100]:
        milestone = {
            'type': 'streak',
            'message': f"You've reached a {new_streak}-day streak!",
            'description': "Consistency is key to building lasting habits. Keep up the great work!",
            'value': new_streak,
            'label': 'Day Streak',
            'habit_name': habit['name']
        }

    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
        return jsonify({
            'success': True,
            'completed': completed,
            'new_streak': new_streak,
            'new_achievements': [dict(a) for a in new_achievements],
            'level_info': level_info,
            'milestone': milestone
        })

    return redirect(url_for('habits.index'))

@bp.route('/quick_log')
@login_required
def quick_log():
    """Get habits for quick logging."""
    today = date.today().strftime('%Y-%m-%d')

    db = get_db()

    # Get all habits for the user
    habits_data = db.execute(
        'SELECT id, name, streak FROM habits WHERE user_id = ? ORDER BY name',
        (g.user['id'],)
    ).fetchall()

    # Get habits completed today
    completed_today = db.execute(
        '''SELECT habit_id FROM habit_logs
           WHERE habit_id IN (SELECT id FROM habits WHERE user_id = ?)
           AND completed_date = ?''',
        (g.user['id'], today)
    ).fetchall()

    # Format the data for JSON response
    habits = []
    for habit in habits_data:
        habits.append({
            'id': habit[0],
            'name': habit[1],
            'streak': habit[2]
        })

    completed_ids = [log[0] for log in completed_today]

    return jsonify({
        'habits': habits,
        'completed_today': completed_ids
    })
