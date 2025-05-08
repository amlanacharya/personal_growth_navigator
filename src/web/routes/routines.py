#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Routine routes for the Personal Growth Navigator.
"""

from datetime import datetime
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from src.core.models.db import get_db
from src.web.routes.auth import login_required

bp = Blueprint('routines', __name__, url_prefix='/routines')

@bp.route('/')
@login_required
def index():
    """Show all routines."""
    db = get_db()
    routines = db.execute(
        'SELECT * FROM routines WHERE user_id = ? ORDER BY time_block',
        (g.user['id'],)
    ).fetchall()
    
    # Get current day of the week
    today_name = datetime.now().strftime('%A')
    
    # Pass all weekdays and highlight the current day
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    return render_template('routines.html',
                          routines=routines,
                          today_name=today_name,
                          weekdays=weekdays,
                          use_custom_energy_legend=True)

@bp.route('/add', methods=('GET', 'POST'))
@login_required
def add():
    """Add a new routine."""
    if request.method == 'POST':
        time_block = request.form['time_block']
        activity = request.form['activity']
        duration = request.form['duration']
        energy_level = request.form['energy_level']
        weekdays = ','.join(request.form.getlist('weekdays'))
        
        error = None
        
        if not time_block:
            error = 'Time block is required.'
        elif not activity:
            error = 'Activity is required.'
        
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                '''INSERT INTO routines 
                   (user_id, time_block, activity, duration, energy_level, weekdays) 
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (g.user['id'], time_block, activity, duration, energy_level, weekdays)
            )
            db.commit()
            
            flash('Routine activity added successfully!')
            return redirect(url_for('routines.index'))
    
    return render_template('add_routine.html')

@bp.route('/edit/<int:id>', methods=('GET', 'POST'))
@login_required
def edit(id):
    """Edit a routine."""
    db = get_db()
    routine = db.execute(
        'SELECT * FROM routines WHERE id = ? AND user_id = ?',
        (id, g.user['id'])
    ).fetchone()
    
    if routine is None:
        flash('Routine not found or you do not have permission to edit it.')
        return redirect(url_for('routines.index'))
    
    if request.method == 'POST':
        time_block = request.form['time_block']
        activity = request.form['activity']
        duration = request.form['duration']
        energy_level = request.form['energy_level']
        weekdays = ','.join(request.form.getlist('weekdays'))
        
        error = None
        
        if not time_block:
            error = 'Time block is required.'
        elif not activity:
            error = 'Activity is required.'
        
        if error is not None:
            flash(error)
        else:
            db.execute(
                '''UPDATE routines 
                   SET time_block = ?, activity = ?, duration = ?, energy_level = ?, weekdays = ? 
                   WHERE id = ? AND user_id = ?''',
                (time_block, activity, duration, energy_level, weekdays, id, g.user['id'])
            )
            db.commit()
            
            flash('Routine updated successfully!')
            return redirect(url_for('routines.index'))
    
    selected_weekdays = routine['weekdays'].split(',') if routine['weekdays'] else []
    
    return render_template('edit_routine.html', routine=routine, selected_weekdays=selected_weekdays)

@bp.route('/delete/<int:id>', methods=('POST',))
@login_required
def delete(id):
    """Delete a routine."""
    db = get_db()
    
    # Verify the routine belongs to the current user
    routine = db.execute(
        'SELECT * FROM routines WHERE id = ? AND user_id = ?',
        (id, g.user['id'])
    ).fetchone()
    
    if routine is None:
        flash('Routine not found or you do not have permission to delete it.')
        return redirect(url_for('routines.index'))
    
    # Delete the routine
    db.execute('DELETE FROM routines WHERE id = ? AND user_id = ?', (id, g.user['id']))
    db.commit()
    
    flash('Routine deleted successfully!')
    return redirect(url_for('routines.index'))
