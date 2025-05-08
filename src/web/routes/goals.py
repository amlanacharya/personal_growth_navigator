#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Goal routes for the Personal Growth Navigator.
"""

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from src.core.models.goal import Goal
from src.web.routes.auth import login_required

bp = Blueprint('goals', __name__, url_prefix='/goals')

@bp.route('/')
@login_required
def index():
    """Show all goals."""
    goals = Goal.get_all_by_user(g.user['id'])
    stats = Goal.get_stats_by_user(g.user['id'])
    return render_template('goals.html', goals=goals, stats=stats)

@bp.route('/add', methods=('GET', 'POST'))
@login_required
def add():
    """Add a new goal."""
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        target_date = request.form.get('target_date', None)
        status = request.form.get('status', 'not_started')
        
        error = None
        
        if not title:
            error = 'Title is required.'
        
        if error is not None:
            flash(error)
        else:
            Goal.create(
                user_id=g.user['id'],
                title=title,
                description=description,
                target_date=target_date,
                status=status
            )
            return redirect(url_for('goals.index'))
    
    return render_template('add_goal.html')

@bp.route('/<int:goal_id>/edit', methods=('GET', 'POST'))
@login_required
def edit(goal_id):
    """Edit a goal."""
    goal = Goal.get_by_id(goal_id)
    
    if goal is None or goal['user_id'] != g.user['id']:
        flash('Goal not found or you do not have permission to edit it.')
        return redirect(url_for('goals.index'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        target_date = request.form.get('target_date', None)
        status = request.form.get('status', goal['status'])
        
        error = None
        
        if not title:
            error = 'Title is required.'
        
        if error is not None:
            flash(error)
        else:
            Goal.update(
                goal_id=goal_id,
                title=title,
                description=description,
                target_date=target_date,
                status=status
            )
            return redirect(url_for('goals.index'))
    
    return render_template('edit_goal.html', goal=goal)

@bp.route('/<int:goal_id>/delete', methods=('POST',))
@login_required
def delete(goal_id):
    """Delete a goal."""
    goal = Goal.get_by_id(goal_id)
    
    if goal is None or goal['user_id'] != g.user['id']:
        flash('Goal not found or you do not have permission to delete it.')
    else:
        Goal.delete(goal_id)
        flash('Goal deleted successfully.')
    
    return redirect(url_for('goals.index'))

@bp.route('/<int:goal_id>/complete', methods=('POST',))
@login_required
def complete(goal_id):
    """Mark a goal as complete."""
    goal = Goal.get_by_id(goal_id)
    
    if goal is None or goal['user_id'] != g.user['id']:
        flash('Goal not found or you do not have permission to update it.')
    else:
        Goal.update(goal_id=goal_id, status='completed')
        
        # Add points for completing a goal
        from src.core.models.user import User
        level_up = User.add_points(g.user['id'], 50)
        
        if level_up:
            flash('Congratulations! You leveled up!')
        else:
            flash('Goal marked as complete. You earned 50 points!')
    
    return redirect(url_for('goals.index'))
