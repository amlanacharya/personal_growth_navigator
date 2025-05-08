#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple test to verify the goals routes are working.
"""

import os
import sys

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_goal_routes_exist():
    """Test that the goal routes are defined correctly."""
    from src.web.routes.goals import bp

    # Check that the blueprint is defined
    assert bp.name == 'goals'
    assert bp.url_prefix == '/goals'

    # Check that the route functions are defined
    from src.web.routes.goals import index, create, add, edit, delete, complete

    # Verify that all the required route functions exist
    assert callable(index)
    assert callable(create)
    assert callable(add)
    assert callable(edit)
    assert callable(delete)
    assert callable(complete)

def test_goal_model_methods():
    """Test that the Goal model has the required methods."""
    from src.core.models.goal import Goal

    # Check that the methods are defined
    assert hasattr(Goal, 'get_by_id')
    assert hasattr(Goal, 'get_all_by_user')
    assert hasattr(Goal, 'create')
    assert hasattr(Goal, 'update')
    assert hasattr(Goal, 'delete')
    assert hasattr(Goal, 'get_stats_by_user')
