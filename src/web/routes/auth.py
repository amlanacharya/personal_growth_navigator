#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Authentication routes for the Personal Growth Navigator.
"""

import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from src.core.models.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    """Register a new user."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form.get('email', '')
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif db.execute(
            'SELECT id FROM users WHERE username = ?', (username,)
        ).fetchone() is not None:
            error = f"User {username} is already registered."

        if error is None:
            # Check if email column exists in users table
            columns = db.execute("PRAGMA table_info(users)").fetchall()
            column_names = [col[1] for col in columns]

            if 'email' in column_names:
                db.execute(
                    'INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                    (username, generate_password_hash(password), email)
                )
            elif 'name' in column_names:
                # For compatibility with the legacy schema
                db.execute(
                    'INSERT INTO users (username, password, name) VALUES (?, ?, ?)',
                    (username, generate_password_hash(password), username)
                )
            else:
                # Fallback to minimal schema
                db.execute(
                    'INSERT INTO users (username, password) VALUES (?, ?)',
                    (username, generate_password_hash(password))
                )
            db.commit()

            # Add initial XP points to the user (if columns exist)
            user_id = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()[0]

            # Check if xp_points column exists in users table
            columns = db.execute("PRAGMA table_info(users)").fetchall()
            column_names = [col[1] for col in columns]

            if 'xp_points' in column_names and 'level' in column_names:
                # Update user's XP points and level
                db.execute(
                    'UPDATE users SET xp_points = ?, level = ? WHERE id = ?',
                    (0, 1, user_id)
                )

            # Check if xp_transactions table exists
            tables = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='xp_transactions'").fetchall()
            if tables:
                # Record the initial XP transaction
                db.execute(
                    'INSERT INTO xp_transactions (user_id, amount, source, description, created_at) VALUES (?, ?, ?, ?, datetime("now"))',
                    (user_id, 0, 'registration', 'Initial registration', )
                )

            db.commit()

            return redirect(url_for('auth.login'))

        flash(error)

    return render_template('signup.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    """Log in a user."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']

            # Commented out until last_login column is added to the database
            # db.execute(
            #     'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
            #     (user['id'],)
            # )
            db.commit()

            return redirect(url_for('index.index'))

        flash(error)

    return render_template('login.html')

@bp.route('/logout')
def logout():
    """Log out a user."""
    session.clear()
    return redirect(url_for('index.index'))

@bp.before_app_request
def load_logged_in_user():
    """Load user if logged in."""
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM users WHERE id = ?', (user_id,)
        ).fetchone()

def login_required(view):
    """View decorator that redirects anonymous users to the login page."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
