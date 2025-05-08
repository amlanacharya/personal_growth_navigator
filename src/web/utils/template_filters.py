#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Template filters and global variables for the Personal Growth Navigator.
"""

from datetime import datetime

def init_app(app):
    """Initialize template filters and global variables."""
    # Make datetime available to all templates
    app.jinja_env.globals['datetime'] = datetime
    
    # Register custom filters
    app.jinja_env.filters['datetime_format'] = datetime_format_filter

def datetime_format_filter(value):
    """Format a datetime string to a more readable format."""
    if not value:
        return ""
    try:
        dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%b %d, %Y at %I:%M %p')
    except ValueError:
        return value
