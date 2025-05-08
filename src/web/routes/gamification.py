#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Gamification routes for the Personal Growth Navigator.
"""

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)

from src.core.models.db import get_db
from src.web.routes.auth import login_required
from src.core.services.gamification_service import GamificationHelper

bp = Blueprint('gamification', __name__, url_prefix='/gamification')

def get_gamification_helper():
    """Get the gamification helper."""
    return GamificationHelper()

@bp.route('/achievements')
@login_required
def achievements():
    """Show user achievements."""
    helper = get_gamification_helper()

    # Check for new achievements
    new_achievements = helper.check_achievements(g.user['id'])

    # Get all achievements
    achievements = helper.get_user_achievements(g.user['id'])

    # Get user level info
    level_info = helper.get_user_level_info(g.user['id'])

    return render_template('achievements.html',
                          achievements=achievements,
                          level_info=level_info,
                          new_achievements=new_achievements)

@bp.route('/challenges')
@login_required
def challenges():
    """Show user challenges."""
    helper = get_gamification_helper()

    # Get active challenges
    active_challenges = helper.get_active_challenges(g.user['id'])

    # Get completed challenges
    db = get_db()
    completed_challenges = db.execute('''
        SELECT c.*, uc.completed_at
        FROM challenges c
        JOIN user_challenges uc ON c.id = uc.challenge_id
        WHERE uc.user_id = ? AND uc.completed = 1
        ORDER BY uc.completed_at DESC
    ''', (g.user['id'],)).fetchall()

    return render_template('challenges.html',
                          active_challenges=active_challenges,
                          completed_challenges=completed_challenges)

@bp.route('/challenges/update', methods=('POST',))
@login_required
def update_challenge():
    """Update challenge progress."""
    challenge_id = request.form.get('challenge_id')
    progress = int(request.form.get('progress', 0))

    if not challenge_id:
        flash('Challenge ID is required')
        return redirect(url_for('gamification.challenges'))

    # Validate progress
    if progress < 0:
        progress = 0
    elif progress > 100:
        progress = 100

    helper = get_gamification_helper()
    helper.update_challenge_progress(g.user['id'], challenge_id, progress)

    flash('Challenge progress updated!')
    return redirect(url_for('gamification.challenges'))

@bp.route('/check_achievements')
@login_required
def check_achievements():
    """Check for new achievements."""
    helper = get_gamification_helper()

    # Check for new achievements
    new_achievements = helper.check_achievements(g.user['id'])

    return jsonify({
        'new_achievements': [dict(a) for a in new_achievements]
    })

@bp.route('/leaderboard')
@login_required
def leaderboard():
    """Show leaderboard."""
    db = get_db()

    # Check if users table has level and xp_points columns
    columns = db.execute("PRAGMA table_info(users)").fetchall()
    column_names = [col[1] for col in columns]

    if 'level' in column_names and 'xp_points' in column_names:
        # Get top users by level and XP points
        leaderboard_data = db.execute('''
            SELECT username, level, xp_points as points
            FROM users
            ORDER BY level DESC, xp_points DESC
            LIMIT 10
        ''').fetchall()

        # Get current user's rank
        user_rank = db.execute('''
            SELECT COUNT(*) + 1
            FROM users
            WHERE level > (SELECT level FROM users WHERE id = ?)
            OR (level = (SELECT level FROM users WHERE id = ?)
                AND xp_points > (SELECT xp_points FROM users WHERE id = ?))
        ''', (g.user['id'], g.user['id'], g.user['id'])).fetchone()[0]

        # Get user's level info
        level_info = db.execute('''
            SELECT level, xp_points as points FROM users WHERE id = ?
        ''', (g.user['id'],)).fetchone()
    else:
        # Fallback for databases without gamification columns
        leaderboard_data = []
        user_rank = 0
        level_info = {'level': 1, 'points': 0}

    return render_template('leaderboard.html',
                          leaderboard=leaderboard_data,
                          user_rank=user_rank,
                          level_info=level_info)
