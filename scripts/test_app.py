#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to test the application after reorganization.

This script performs basic tests to ensure the application is working correctly.
"""

import os
import sys
import sqlite3
import importlib

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_imports():
    """Test importing key modules."""
    print("Testing imports...")

    modules_to_test = [
        'src',
        'src.web.app',
        'src.core.models.db',
        'src.core.models.user',
        'src.core.models.goal',
        'src.web.routes.auth',
        'src.web.routes.index',
        'src.web.routes.goals',
        'src.web.routes.habits',
        'src.web.routes.routines',
        'src.web.routes.analytics',
        'src.web.routes.ai_roadmap',
        'src.web.routes.ai_insights',
        'src.web.routes.ai_notifications',
        'src.web.routes.gamification',
        'src.ai.helpers.ai_helper',
        'src.ai.prompts.system_prompts',
        'src.core.services.gamification_service',
        'src.core.services.notification_service',
        'src.core.utils.commands'
    ]

    success_count = 0
    failed_modules = []

    for module_name in modules_to_test:
        try:
            importlib.import_module(module_name)
            success_count += 1
            print(f"  ✓ Successfully imported {module_name}")
        except ImportError as e:
            failed_modules.append((module_name, str(e)))
            print(f"  ✗ Failed to import {module_name}: {e}")

    print(f"\nImport test results: {success_count}/{len(modules_to_test)} modules imported successfully")

    if failed_modules:
        print("\nFailed modules:")
        for module, error in failed_modules:
            print(f"  - {module}: {error}")

    return len(failed_modules) == 0

def test_database():
    """Test database connection."""
    print("\nTesting database connection...")

    # Check if database exists
    instance_db_path = os.path.join('instance', 'growth_navigator.db')
    root_db_path = 'growth_navigator.db'

    if os.path.exists(instance_db_path):
        db_path = instance_db_path
        print(f"  ✓ Found database at {instance_db_path}")
    elif os.path.exists(root_db_path):
        db_path = root_db_path
        print(f"  ✓ Found database at {root_db_path}")
    else:
        print("  ✗ Database not found")
        return False

    # Try to connect to the database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if we can query the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        print(f"  ✓ Successfully connected to database. Found {len(tables)} tables:")
        for table in tables:
            print(f"    - {table[0]}")

        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"  ✗ Error connecting to database: {e}")
        return False

def test_app_creation():
    """Test creating the Flask app."""
    print("\nTesting Flask app creation...")

    try:
        from src.web.app import create_app
        app = create_app()

        print(f"  ✓ Successfully created Flask app")
        print(f"    - App name: {app.name}")
        print(f"    - Debug mode: {app.debug}")
        print(f"    - Testing mode: {app.testing}")
        print(f"    - Instance path: {app.instance_path}")
        print(f"    - Static folder: {app.static_folder}")
        print(f"    - Template folder: {app.template_folder}")

        # Check registered blueprints
        blueprints = [bp.name for bp in app.blueprints.values()]
        print(f"    - Registered blueprints ({len(blueprints)}): {', '.join(blueprints)}")

        return True
    except Exception as e:
        print(f"  ✗ Error creating Flask app: {e}")
        return False

def main():
    """Run all tests."""
    print("Running tests for the Personal Growth Navigator...\n")

    # Run tests
    imports_ok = test_imports()
    db_ok = test_database()
    app_ok = test_app_creation()

    # Print summary
    print("\nTest Summary:")
    print(f"  Imports: {'✓ PASS' if imports_ok else '✗ FAIL'}")
    print(f"  Database: {'✓ PASS' if db_ok else '✗ FAIL'}")
    print(f"  Flask App: {'✓ PASS' if app_ok else '✗ FAIL'}")

    # Overall result
    if imports_ok and db_ok and app_ok:
        print("\n✅ All tests passed! The application appears to be working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
