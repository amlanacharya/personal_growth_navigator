#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Goal model for the Personal Growth Navigator.
"""

from src.core.models.db import get_db

class Goal:
    """Goal model class."""

    @staticmethod
    def get_by_id(goal_id):
        """Get a goal by ID."""
        db = get_db()
        goal = db.execute(
            'SELECT * FROM goals WHERE id = ?', (goal_id,)
        ).fetchone()
        return goal

    @staticmethod
    def get_all_by_user(user_id):
        """Get all goals for a user."""
        db = get_db()
        goals = db.execute(
            'SELECT * FROM goals WHERE user_id = ? ORDER BY priority, id DESC',
            (user_id,)
        ).fetchall()
        return goals

    @staticmethod
    def create(user_id, title, description=None, target_date=None, status='active', priority=2):
        """Create a new goal."""
        db = get_db()
        db.execute(
            '''INSERT INTO goals
               (user_id, category, description, deadline, status, priority)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (user_id, title, description, target_date, status, priority)
        )
        db.commit()

        # Get the last inserted row ID
        cursor = db.execute('SELECT last_insert_rowid()')
        goal_id = cursor.fetchone()[0]

        return Goal.get_by_id(goal_id)

    @staticmethod
    def update(goal_id, title, description=None, target_date=None, status=None, priority=None):
        """Update a goal."""
        db = get_db()

        # Get current values
        goal = Goal.get_by_id(goal_id)

        # Use current values if not provided
        title = title or goal['category']
        description = description if description is not None else goal['description']
        target_date = target_date if target_date is not None else goal['deadline']
        status = status or goal['status']
        priority = priority if priority is not None else goal['priority']

        db.execute(
            '''UPDATE goals
               SET category = ?, description = ?, deadline = ?, status = ?, priority = ?
               WHERE id = ?''',
            (title, description, target_date, status, priority, goal_id)
        )
        db.commit()

        return Goal.get_by_id(goal_id)

    @staticmethod
    def delete(goal_id):
        """Delete a goal."""
        db = get_db()
        db.execute('DELETE FROM goals WHERE id = ?', (goal_id,))
        db.commit()

    @staticmethod
    def get_stats_by_user(user_id):
        """Get goal statistics for a user."""
        db = get_db()

        # Get counts by status
        stats = {}

        # Total goals
        total = db.execute(
            'SELECT COUNT(*) FROM goals WHERE user_id = ?',
            (user_id,)
        ).fetchone()[0]
        stats['total'] = total

        # Completed goals
        completed = db.execute(
            'SELECT COUNT(*) FROM goals WHERE user_id = ? AND status = "completed"',
            (user_id,)
        ).fetchone()[0]
        stats['completed'] = completed

        # In progress goals
        in_progress = db.execute(
            'SELECT COUNT(*) FROM goals WHERE user_id = ? AND status = "in_progress"',
            (user_id,)
        ).fetchone()[0]
        stats['in_progress'] = in_progress

        # Not started goals
        not_started = db.execute(
            'SELECT COUNT(*) FROM goals WHERE user_id = ? AND status = "not_started"',
            (user_id,)
        ).fetchone()[0]
        stats['not_started'] = not_started

        # Completion rate
        stats['completion_rate'] = (completed / total * 100) if total > 0 else 0

        return stats
