#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Helper service initialization for the Personal Growth Navigator.
"""

from src.ai.helpers.ai_helper import AIHelper, create_env_file
from src.ai.helpers.ai_insights_helper import AIInsightsHelper
from src.ai.helpers.ai_notification_helper import AINotificationHelper
from src.core.services.gamification_service import GamificationHelper

# Singleton instances
ai_helper = None
gamification_helper = None
ai_insights_helper = None
ai_notification_helper = None

def get_ai_helper():
    """Get or create the AI helper instance."""
    global ai_helper
    if ai_helper is None:
        ai_helper = AIHelper()
    return ai_helper

def get_gamification_helper():
    """Get or create the gamification helper instance."""
    global gamification_helper
    if gamification_helper is None:
        gamification_helper = GamificationHelper()
    return gamification_helper

def get_ai_insights_helper():
    """Get or create the AI insights helper instance."""
    global ai_insights_helper
    if ai_insights_helper is None:
        ai_insights_helper = AIInsightsHelper()
    return ai_insights_helper

def get_ai_notification_helper():
    """Get or create the AI notification helper instance."""
    global ai_notification_helper
    if ai_notification_helper is None:
        ai_notification_helper = AINotificationHelper()
    return ai_notification_helper

def init_app(app):
    """Initialize helper services."""
    # Create .env file if it doesn't exist
    create_env_file()
    
    # Initialize helpers
    get_ai_helper()
    get_gamification_helper()
    get_ai_insights_helper()
    get_ai_notification_helper()
