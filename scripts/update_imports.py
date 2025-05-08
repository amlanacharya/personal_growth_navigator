#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to update import statements in the migrated files.

This script should be run after the migrate_codebase.py script.
"""

import os
import re

def update_file_imports(file_path):
    """Update import statements in a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update imports
    # These are just examples, you'll need to customize based on your actual imports
    replacements = [
        # Database imports
        (r'from src.core.models.db import', r'from src.core.models.db import'),
        
        # Helper imports
        (r'from src.ai.helpers import ai_helper', r'from src.ai.helpers from src.ai.helpers import ai_helper'),
        (r'from src.ai.helpers.ai_helper import', r'from src.ai.helpers.ai_helper import'),
        (r'from src.ai.helpers import ai_insights_helper', r'from src.ai.helpers from src.ai.helpers import ai_insights_helper'),
        (r'from src.ai.helpers.ai_insights_helper import', r'from src.ai.helpers.ai_insights_helper import'),
        (r'from src.ai.helpers import ai_notification_helper', r'from src.ai.helpers from src.ai.helpers import ai_notification_helper'),
        (r'from src.ai.helpers.ai_notification_helper import', r'from src.ai.helpers.ai_notification_helper import'),
        (r'from src.core.services import gamification_service', r'from src.core.services import gamification_service'),
        (r'from src.core.services.gamification_service import', r'from src.core.services.gamification_service import'),
        (r'from src.core.services import notification_service', r'from src.core.services import notification_service'),
        (r'from src.core.services.notification_service import', r'from src.core.services.notification_service import'),
        
        # Model imports
        (r'from src.core.models import user', r'from src.core.models from src.core.models import user'),
        (r'from src.core.models.user import', r'from src.core.models.user import'),
        (r'from src.core.models import goal', r'from src.core.models from src.core.models import goal'),
        (r'from src.core.models.goal import', r'from src.core.models.goal import'),
        
        # Route imports
        (r'from src.web.routes import auth', r'from src.web.routes from src.web.routes import auth'),
        (r'from src.web.routes.auth import', r'from src.web.routes.auth import'),
    ]
    
    # Apply replacements
    for old, new in replacements:
        content = re.sub(old, new, content)
    
    # Write updated content back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Updated imports in: {file_path}")

def process_directory(directory):
    """Process all Python files in a directory recursively."""
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                update_file_imports(file_path)

def main():
    """Main function to update imports."""
    print("Updating import statements...")
    
    # Process all Python files in the src directory
    process_directory('src')
    
    # Process all Python files in the scripts directory
    process_directory('scripts')
    
    print("Import statements updated!")

if __name__ == "__main__":
    main()
