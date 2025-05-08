#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AI Roadmap routes for the Personal Growth Navigator.
"""

import json
from datetime import datetime, timedelta
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)

from src.core.models.db import get_db
from src.web.routes.auth import login_required
from src.ai.helpers.ai_helper import AIHelper

bp = Blueprint('ai_roadmap', __name__, url_prefix='/ai_roadmap')

def get_ai_helper():
    """Get the AI helper."""
    return AIHelper()

@bp.route('/')
@login_required
def index():
    """Show AI roadmap interface."""
    db = get_db()
    
    # Get saved roadmaps
    roadmaps = db.execute(
        'SELECT * FROM ai_roadmaps WHERE user_id = ? ORDER BY created_at DESC',
        (g.user['id'],)
    ).fetchall()
    
    # Get conversation history
    helper = get_ai_helper()
    conversation_history = helper.get_conversation_history(g.user['id'])
    
    return render_template('ai_roadmap.html',
                          roadmaps=roadmaps,
                          conversation_history=conversation_history)

@bp.route('/chat', methods=('POST',))
@login_required
def chat():
    """Process chat with AI."""
    user_message = request.form['message']
    
    # Get AI response
    helper = get_ai_helper()
    ai_response = helper.generate_response(user_message)
    
    # Save conversation
    helper.save_conversation(g.user['id'], user_message, ai_response)
    
    return jsonify({
        'response': ai_response
    })

@bp.route('/save', methods=('POST',))
@login_required
def save():
    """Save a roadmap."""
    title = request.form['title']
    content = request.form['content']
    
    db = get_db()
    db.execute(
        'INSERT INTO ai_roadmaps (user_id, title, content, created_at) VALUES (?, ?, ?, ?)',
        (g.user['id'], title, content, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    db.commit()
    
    flash('Roadmap saved successfully!')
    return redirect(url_for('ai_roadmap.index'))

@bp.route('/view/<int:id>')
@login_required
def view(id):
    """View a saved roadmap."""
    db = get_db()
    roadmap = db.execute(
        'SELECT * FROM ai_roadmaps WHERE id = ? AND user_id = ?',
        (id, g.user['id'])
    ).fetchone()
    
    if roadmap is None:
        flash('Roadmap not found or you do not have permission to view it.')
        return redirect(url_for('ai_roadmap.index'))
    
    return render_template('view_roadmap.html', roadmap=roadmap)

@bp.route('/delete/<int:id>', methods=('POST',))
@login_required
def delete(id):
    """Delete a roadmap."""
    db = get_db()
    
    # Verify the roadmap belongs to the current user
    roadmap = db.execute(
        'SELECT * FROM ai_roadmaps WHERE id = ? AND user_id = ?',
        (id, g.user['id'])
    ).fetchone()
    
    if roadmap is None:
        flash('Roadmap not found or you do not have permission to delete it.')
        return redirect(url_for('ai_roadmap.index'))
    
    # Delete the roadmap
    db.execute('DELETE FROM ai_roadmaps WHERE id = ? AND user_id = ?', (id, g.user['id']))
    db.commit()
    
    flash('Roadmap deleted successfully!')
    return redirect(url_for('ai_roadmap.index'))

@bp.route('/save_goals', methods=('POST',))
@login_required
def save_goals():
    """Save extracted goals from a roadmap."""
    goals_json = request.form.get('goals', '[]')
    
    try:
        goals = json.loads(goals_json)
        
        if not goals:
            flash('No goals selected to save')
            return redirect(request.referrer or url_for('ai_roadmap.index'))
        
        db = get_db()
        
        # Save each goal
        for goal in goals:
            # Determine a default category based on the goal content
            category = 'Personal Development'  # Default category
            if any(kw in goal.lower() for kw in ['health', 'exercise', 'fitness', 'diet', 'nutrition', 'weight']):
                category = 'Physical Fitness'
            elif any(kw in goal.lower() for kw in ['career', 'job', 'work', 'professional', 'business']):
                category = 'Career'
            elif any(kw in goal.lower() for kw in ['learn', 'study', 'education', 'knowledge', 'skill']):
                category = 'Learning'
            elif any(kw in goal.lower() for kw in ['family', 'friend', 'relationship', 'social']):
                category = 'Relationships'
            elif any(kw in goal.lower() for kw in ['finance', 'money', 'saving', 'budget', 'invest']):
                category = 'Financial'
            
            # Set a default deadline of 3 months from now
            deadline = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')
            
            # Set a medium priority by default
            priority = 2
            
            db.execute(
                'INSERT INTO goals (user_id, category, description, deadline, priority, status) VALUES (?, ?, ?, ?, ?, ?)',
                (g.user['id'], category, goal, deadline, priority, 'active')
            )
        
        db.commit()
        
        flash(f'Successfully added {len(goals)} goals to your account!')
        return redirect(url_for('goals.index'))
        
    except json.JSONDecodeError:
        flash('Error processing goals data')
        return redirect(request.referrer or url_for('ai_roadmap.index'))

@bp.route('/save_habits', methods=('POST',))
@login_required
def save_habits():
    """Save extracted habits from a roadmap."""
    habits_json = request.form.get('habits', '[]')
    
    try:
        habits = json.loads(habits_json)
        
        if not habits:
            flash('No habits selected to save')
            return redirect(request.referrer or url_for('ai_roadmap.index'))
        
        db = get_db()
        
        # Get user's active goals for potential linking
        goals = db.execute(
            'SELECT id, description FROM goals WHERE user_id = ? AND status = "active"',
            (g.user['id'],)
        ).fetchall()
        
        # Save each habit
        for habit in habits:
            # Try to find a related goal
            related_goal_id = None
            for goal in goals:
                # Simple matching - check if any significant words from the habit appear in the goal
                habit_words = set(w.lower() for w in habit.split() if len(w) > 3)
                goal_words = set(w.lower() for w in goal[1].split() if len(w) > 3)
                
                if habit_words.intersection(goal_words):
                    related_goal_id = goal[0]
                    break
            
            # Default frequency
            frequency = 'daily'
            
            db.execute(
                'INSERT INTO habits (user_id, name, goal_id, frequency, streak, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                (g.user['id'], habit, related_goal_id, frequency, 0, datetime.now().strftime('%Y-%m-%d'))
            )
        
        db.commit()
        
        flash(f'Successfully added {len(habits)} habits to your account!')
        return redirect(url_for('habits.index'))
        
    except json.JSONDecodeError:
        flash('Error processing habits data')
        return redirect(request.referrer or url_for('ai_roadmap.index'))

@bp.route('/save_routines', methods=('POST',))
@login_required
def save_routines():
    """Save extracted routines from a roadmap."""
    routines_json = request.form.get('routines', '[]')
    
    try:
        routines = json.loads(routines_json)
        
        if not routines:
            flash('No routines selected to save')
            return redirect(request.referrer or url_for('ai_roadmap.index'))
        
        db = get_db()
        
        # Save each routine
        for routine in routines:
            # Try to extract time information from the routine description
            time_block = 'Morning'  # Default
            if any(kw in routine.lower() for kw in ['morning', 'am', 'breakfast', 'wake']):
                time_block = 'Morning'
            elif any(kw in routine.lower() for kw in ['noon', 'lunch', 'midday']):
                time_block = 'Midday'
            elif any(kw in routine.lower() for kw in ['afternoon', 'evening', 'pm']):
                time_block = 'Afternoon'
            elif any(kw in routine.lower() for kw in ['night', 'bedtime', 'sleep']):
                time_block = 'Evening'
            
            # Default duration of 30 minutes
            duration = 30
            
            # Default energy level
            energy_level = 'Medium'
            
            # Default to all weekdays
            weekdays = 'Monday,Tuesday,Wednesday,Thursday,Friday'
            
            db.execute(
                'INSERT INTO routines (user_id, time_block, activity, duration, energy_level, weekdays) VALUES (?, ?, ?, ?, ?, ?)',
                (g.user['id'], time_block, routine, duration, energy_level, weekdays)
            )
        
        db.commit()
        
        flash(f'Successfully added {len(routines)} routines to your account!')
        return redirect(url_for('routines.index'))
        
    except json.JSONDecodeError:
        flash('Error processing routines data')
        return redirect(request.referrer or url_for('ai_roadmap.index'))
