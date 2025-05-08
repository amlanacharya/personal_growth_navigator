#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to migrate the existing codebase to the new structure.

This script should be run from the root directory of the project.
"""

import os
import shutil
import re

def create_directory(path):
    """Create a directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")

def copy_file(src, dest):
    """Copy a file from source to destination."""
    if os.path.exists(src):
        # Create the destination directory if it doesn't exist
        dest_dir = os.path.dirname(dest)
        create_directory(dest_dir)
        
        # Copy the file
        shutil.copy2(src, dest)
        print(f"Copied: {src} -> {dest}")
    else:
        print(f"Warning: Source file not found: {src}")

def migrate_templates():
    """Migrate template files to the new structure."""
    # Create the templates directory
    create_directory("src/web/templates")
    create_directory("src/web/templates/components")
    
    # Copy template files
    for filename in os.listdir("templates"):
        src_path = os.path.join("templates", filename)
        
        # Skip directories (except components)
        if os.path.isdir(src_path) and filename != "components":
            continue
        
        # Handle components directory separately
        if filename == "components":
            for component_file in os.listdir(src_path):
                component_src = os.path.join(src_path, component_file)
                component_dest = os.path.join("src/web/templates/components", component_file)
                copy_file(component_src, component_dest)
        else:
            dest_path = os.path.join("src/web/templates", filename)
            copy_file(src_path, dest_path)

def migrate_static_files():
    """Migrate static files to the new structure."""
    # Create the static directories
    create_directory("src/web/static/js")
    create_directory("src/web/static/css")
    create_directory("src/web/static/images")
    
    # Copy static files
    if os.path.exists("static"):
        for root, dirs, files in os.walk("static"):
            for filename in files:
                src_path = os.path.join(root, filename)
                
                # Determine the destination path based on file extension
                if filename.endswith(".js"):
                    dest_path = os.path.join("src/web/static/js", filename)
                elif filename.endswith(".css"):
                    dest_path = os.path.join("src/web/static/css", filename)
                elif filename.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg")):
                    dest_path = os.path.join("src/web/static/images", filename)
                else:
                    # For other file types, maintain the same directory structure
                    rel_path = os.path.relpath(src_path, "static")
                    dest_path = os.path.join("src/web/static", rel_path)
                
                copy_file(src_path, dest_path)

def migrate_python_files():
    """Migrate Python files to the new structure."""
    # AI helper files
    ai_files = ["ai_helper.py", "ai_insights_helper.py", "ai_notification_helper.py"]
    for filename in ai_files:
        if os.path.exists(filename):
            dest_path = os.path.join("src/ai/helpers", filename)
            copy_file(filename, dest_path)
    
    # Database schema files
    schema_files = ["schema_updates.py", "schema_updates_ai_notifications.py", 
                   "schema_updates_mood.py", "schema_updates_scheduled_notifications.py"]
    for filename in schema_files:
        if os.path.exists(filename):
            dest_path = os.path.join("migrations", filename)
            copy_file(filename, dest_path)
    
    # Gamification files
    if os.path.exists("gamification_helper.py"):
        dest_path = os.path.join("src/core/services", "gamification_service.py")
        copy_file("gamification_helper.py", dest_path)
    
    # Notification scheduler
    if os.path.exists("notification_scheduler.py"):
        dest_path = os.path.join("src/core/services", "notification_service.py")
        copy_file("notification_scheduler.py", dest_path)
    
    # Setup scripts
    setup_files = ["setup.py", "setup_demo.py", "setup_gamification.py", "populate_gamification_data.py"]
    for filename in setup_files:
        if os.path.exists(filename):
            dest_path = os.path.join("scripts", filename)
            copy_file(filename, dest_path)
    
    # Main application file
    if os.path.exists("app.py"):
        # We'll need to refactor this file to fit the new structure
        # For now, just copy it to a temporary location
        copy_file("app.py", "scripts/original_app.py")

def migrate_documentation():
    """Migrate documentation files to the new structure."""
    doc_files = ["GAMIFICATION_README.md", "IMPLEMENTATION_SUMMARY.md"]
    for filename in doc_files:
        if os.path.exists(filename):
            dest_path = os.path.join("docs", filename)
            copy_file(filename, dest_path)

def main():
    """Main function to migrate the codebase."""
    print("Starting codebase migration...")
    
    # Create the new directory structure (if not already created)
    directories = [
        "src/core/models", "src/core/services", "src/core/utils",
        "src/api", "src/web/routes", "src/web/templates", "src/web/static",
        "src/ai/helpers", "src/ai/prompts",
        "tests/unit", "tests/integration",
        "scripts", "config", "docs", "migrations"
    ]
    
    for directory in directories:
        create_directory(directory)
    
    # Migrate files
    migrate_templates()
    migrate_static_files()
    migrate_python_files()
    migrate_documentation()
    
    print("\nMigration completed!")
    print("\nNext steps:")
    print("1. Review the migrated files and ensure everything is in the correct location")
    print("2. Refactor the main application code to use the new structure")
    print("3. Update import statements in all files to reflect the new structure")
    print("4. Test the application to ensure everything works correctly")

if __name__ == "__main__":
    main()
