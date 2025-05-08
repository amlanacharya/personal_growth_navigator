#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configuration settings for the Personal Growth Navigator.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory of the application
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# Flask configuration
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key_for_development_only')
TESTING = False

# Database configuration
DATABASE = os.path.join(BASE_DIR, 'instance', 'growth_navigator.db')

# AI configuration
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
AI_MODEL = os.environ.get('AI_MODEL', 'llama3-8b-8192')

# Notification configuration
ENABLE_NOTIFICATIONS = os.environ.get('ENABLE_NOTIFICATIONS', 'True') == 'True'
NOTIFICATION_FREQUENCY = os.environ.get('NOTIFICATION_FREQUENCY', 'daily')

# Gamification configuration
ENABLE_GAMIFICATION = os.environ.get('ENABLE_GAMIFICATION', 'True') == 'True'
