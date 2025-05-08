#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CLI commands for the Personal Growth Navigator.
"""

import click
from flask.cli import with_appcontext
from src.core.models.db import init_db, get_db

def init_app(app):
    """Register CLI commands with the Flask app."""
    app.cli.add_command(init_db_command)
    app.cli.add_command(setup_demo_command)

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

@click.command('setup-demo')
@with_appcontext
def setup_demo_command():
    """Set up demo data for the application."""
    from scripts.setup_demo import setup_demo
    setup_demo()
    click.echo('Demo data has been set up.')
