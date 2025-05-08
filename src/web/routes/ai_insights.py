#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AI Insights routes for the Personal Growth Navigator.
"""

from datetime import datetime, date, timedelta
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)

from src.core.models.db import get_db
from src.web.routes.auth import login_required
from src.ai.helpers.ai_insights_helper import AIInsightsHelper

bp = Blueprint('ai_insights', __name__, url_prefix='/ai_insights')

def get_ai_insights_helper():
    """Get the AI insights helper."""
    return AIInsightsHelper()

@bp.route('/dashboard')
@login_required
def dashboard():
    """Show AI insights dashboard."""
    helper = get_ai_insights_helper()

    # Get user data for insights
    user_data = helper.get_user_data(g.user['id'])

    # Get insights
    habit_insights = helper.generate_habit_insights(user_data)
    energy_insights = helper.generate_energy_insights(user_data)
    mood_insights = helper.generate_mood_insights(user_data)

    return render_template('ai_insights_dashboard.html',
                          habit_insights=habit_insights,
                          energy_insights=energy_insights,
                          mood_insights=mood_insights)

@bp.route('/habit_suggestions')
@login_required
def habit_suggestions():
    """Show AI habit suggestions."""
    helper = get_ai_insights_helper()

    # Get user data for insights
    user_data = helper.get_user_data(g.user['id'])

    # Get habit suggestions
    suggestions = helper.generate_habit_suggestions(user_data)

    return render_template('ai_habit_suggestions.html', suggestions=suggestions)

@bp.route('/habit_motivation')
@login_required
def habit_motivation():
    """Show AI habit motivation."""
    helper = get_ai_insights_helper()

    # Get user data for insights
    user_data = helper.get_user_data(g.user['id'])

    # Get habit motivation
    motivation = helper.generate_habit_motivation(user_data)

    return render_template('ai_habit_motivation.html', motivation=motivation)

@bp.route('/energy_optimization')
@login_required
def energy_optimization():
    """Show AI energy optimization."""
    helper = get_ai_insights_helper()

    # Get user data for insights
    user_data = helper.get_user_data(g.user['id'])

    # Get energy optimization
    optimization = helper.generate_energy_optimization(user_data)

    return render_template('ai_energy_optimization.html', optimization=optimization)

@bp.route('/mood_suggestions')
@login_required
def mood_suggestions():
    """Show AI mood suggestions."""
    helper = get_ai_insights_helper()

    # Get user data for insights
    user_data = helper.get_user_data(g.user['id'])

    # Get mood suggestions
    suggestions = helper.generate_mood_suggestions(user_data)

    return render_template('ai_mood_suggestions.html', suggestions=suggestions)

@bp.route('/log_mood', methods=('POST',))
@login_required
def log_mood():
    """Log user mood."""
    mood_score = int(request.form.get('mood_score', 3))
    energy_level = int(request.form.get('energy_level', 5))
    mood_note = request.form.get('mood_note', '')

    # Validate mood score
    if mood_score < 1:
        mood_score = 1
    elif mood_score > 5:
        mood_score = 5

    # Validate energy level
    if energy_level < 1:
        energy_level = 1
    elif energy_level > 10:
        energy_level = 10

    db = get_db()

    # Check if already logged today
    today = datetime.now().strftime('%Y-%m-%d')
    existing = db.execute('''
        SELECT id FROM mood_logs
        WHERE user_id = ? AND date(logged_at) = ?
    ''', (g.user['id'], today)).fetchone()

    if existing:
        # Update existing entry
        db.execute('''
            UPDATE mood_logs
            SET mood_score = ?, mood_note = ?, energy_level = ?, logged_at = ?
            WHERE id = ?
        ''', (mood_score, mood_note, energy_level, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), existing[0]))
        message = "Mood updated for today!"
    else:
        # Create new entry
        db.execute('''
            INSERT INTO mood_logs (user_id, mood_score, mood_note, energy_level, logged_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (g.user['id'], mood_score, mood_note, energy_level, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        message = "Mood logged successfully!"

    db.commit()

    flash(message)
    return redirect(request.referrer or url_for('index'))

@bp.route('/mood_history')
@login_required
def mood_history():
    """Show mood history."""
    db = get_db()

    # Get mood history for the last 30 days
    mood_history = db.execute('''
        SELECT mood_score, mood_note, energy_level, logged_at
        FROM mood_logs
        WHERE user_id = ?
        ORDER BY logged_at DESC
        LIMIT 30
    ''', (g.user['id'],)).fetchall()

    # Format the data for the template
    formatted_history = []
    for entry in mood_history:
        formatted_history.append({
            'mood_score': entry[0],
            'mood_note': entry[1],
            'energy_level': entry[2],
            'logged_at': datetime.strptime(entry[3], '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y')
        })

    return render_template('mood_history.html', mood_history=formatted_history)

@bp.route('/get_insights')
@login_required
def get_insights():
    """Get AI insights as JSON."""
    helper = get_ai_insights_helper()

    # Get user data for insights
    user_data = helper.get_user_data(g.user['id'])

    # Get insights
    habit_insights = helper.generate_habit_insights(user_data)
    energy_insights = helper.generate_energy_insights(user_data)
    mood_insights = helper.generate_mood_insights(user_data)

    # Combine insights
    all_insights = []

    # Add habit insights
    for insight in habit_insights:
        all_insights.append({
            'title': insight.get('title', 'Habit Insight'),
            'content': insight.get('content', ''),
            'icon': insight.get('icon', 'fa-check-circle'),
            'color': insight.get('color', 'primary'),
            'actions': insight.get('actions', [])
        })

    # Add energy insights
    for insight in energy_insights:
        all_insights.append({
            'title': insight.get('title', 'Energy Insight'),
            'content': insight.get('content', ''),
            'icon': insight.get('icon', 'fa-bolt'),
            'color': insight.get('color', 'warning'),
            'actions': insight.get('actions', [])
        })

    # Add mood insights
    for insight in mood_insights:
        all_insights.append({
            'title': insight.get('title', 'Mood Insight'),
            'content': insight.get('content', ''),
            'icon': insight.get('icon', 'fa-smile'),
            'color': insight.get('color', 'info'),
            'actions': insight.get('actions', [])
        })

    return jsonify({'insights': all_insights})
