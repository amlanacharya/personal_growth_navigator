#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Flask application factory for the Personal Growth Navigator.
"""

import os
from flask import Flask
from dotenv import load_dotenv
import schema_updates_mood
import schema_updates_ai_notifications
import schema_updates_scheduled_notifications
# from notification_scheduler import start_notification_scheduler

def create_app(test_config=None):
    """Create and configure the Flask application."""

    # Load environment variables
    load_dotenv()

    # Create and configure the app
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')

    # Configure the app
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        DATABASE=os.path.join(app.instance_path, 'growth_navigator.db'),
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile(os.path.join('..', '..', 'config', 'config.py'), silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize template filters and globals
    from src.web.utils import template_filters
    template_filters.init_app(app)

    # Initialize helper services
    from src.core.services import helpers
    helpers.init_app(app)

    # Register blueprints
    from src.web.routes import all_blueprints
    for blueprint in all_blueprints:
        app.register_blueprint(blueprint)

    # Set up database
    from src.core.models import db
    db.init_app(app)

    # Register CLI commands
    from src.core.utils import commands
    commands.init_app(app)

    # Update database schema for mood tracking, AI notifications, and scheduled notifications
    schema_updates_mood.update_database_schema_for_mood()
    schema_updates_ai_notifications.update_database_schema_for_ai_notifications()
    schema_updates_scheduled_notifications.update_database_schema_for_scheduled_notifications()

    # Start the notification scheduler (temporarily disabled)
    # start_notification_scheduler()

    return app
