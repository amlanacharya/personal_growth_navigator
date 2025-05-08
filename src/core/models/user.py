#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
User model for the Personal Growth Navigator.
"""

from src.core.models.db import get_db

class User:
    """User model class."""
    
    @staticmethod
    def get_by_id(user_id):
        """Get a user by ID."""
        db = get_db()
        user = db.execute(
            'SELECT * FROM users WHERE id = ?', (user_id,)
        ).fetchone()
        return user
    
    @staticmethod
    def get_by_username(username):
        """Get a user by username."""
        db = get_db()
        user = db.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()
        return user
    
    @staticmethod
    def create(username, password_hash, email=None):
        """Create a new user."""
        db = get_db()
        db.execute(
            'INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
            (username, password_hash, email)
        )
        db.commit()
        
        # Get the user ID
        user = User.get_by_username(username)
        
        # Create initial user level
        db.execute(
            'INSERT INTO user_levels (user_id, level, points) VALUES (?, 1, 0)',
            (user['id'],)
        )
        db.commit()
        
        return user
    
    @staticmethod
    def update_last_login(user_id):
        """Update the last login time for a user."""
        db = get_db()
        db.execute(
            'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
            (user_id,)
        )
        db.commit()
    
    @staticmethod
    def get_level(user_id):
        """Get the level information for a user."""
        db = get_db()
        level = db.execute(
            'SELECT * FROM user_levels WHERE user_id = ?',
            (user_id,)
        ).fetchone()
        return level
    
    @staticmethod
    def add_points(user_id, points):
        """Add points to a user's account and update level if necessary."""
        db = get_db()
        
        # Get current level and points
        level_info = User.get_level(user_id)
        current_level = level_info['level']
        current_points = level_info['points']
        
        # Add points
        new_points = current_points + points
        
        # Check if level up is needed (simple formula: 100 points per level)
        new_level = (new_points // 100) + 1
        
        # Update level and points
        db.execute(
            'UPDATE user_levels SET level = ?, points = ? WHERE user_id = ?',
            (new_level, new_points, user_id)
        )
        db.commit()
        
        # Return whether a level up occurred
        return new_level > current_level
