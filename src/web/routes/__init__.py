"""
Route definitions for the Personal Growth Navigator.
"""

# Import all blueprints
from src.web.routes.auth import bp as auth_bp
from src.web.routes.index import bp as index_bp
from src.web.routes.goals import bp as goals_bp
from src.web.routes.habits import bp as habits_bp
from src.web.routes.routines import bp as routines_bp
from src.web.routes.analytics import bp as analytics_bp
from src.web.routes.ai_roadmap import bp as ai_roadmap_bp
from src.web.routes.ai_insights import bp as ai_insights_bp
from src.web.routes.ai_notifications import bp as ai_notifications_bp
from src.web.routes.gamification import bp as gamification_bp

# List of all blueprints to be registered with the app
all_blueprints = [
    auth_bp,
    index_bp,
    goals_bp,
    habits_bp,
    routines_bp,
    analytics_bp,
    ai_roadmap_bp,
    ai_insights_bp,
    ai_notifications_bp,
    gamification_bp
]
