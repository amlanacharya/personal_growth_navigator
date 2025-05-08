# Personal Growth Navigator Codebase Structure

This document describes the structure of the Personal Growth Navigator codebase after reorganization.

## Overview

The codebase follows a modular, production-grade structure with clear separation of concerns:

```
personal_growth_navigator/
├── src/                      # Main source code
│   ├── core/                 # Core application logic
│   │   ├── models/           # Database models
│   │   ├── services/         # Business logic services
│   │   └── utils/            # Utility functions
│   ├── api/                  # API endpoints
│   ├── web/                  # Web interface
│   │   ├── routes/           # Route definitions
│   │   ├── templates/        # HTML templates
│   │   │   └── components/   # Reusable template components
│   │   └── static/           # Static assets
│   │       ├── js/           # JavaScript files
│   │       ├── css/          # CSS files
│   │       └── images/       # Image files
│   └── ai/                   # AI-related functionality
│       ├── helpers/          # AI helper modules
│       └── prompts/          # AI prompt templates
├── tests/                    # Test suite
│   ├── unit/                 # Unit tests
│   └── integration/          # Integration tests
├── scripts/                  # Utility scripts
├── config/                   # Configuration files
├── docs/                     # Documentation
├── migrations/               # Database migrations
├── instance/                 # Instance-specific files (database)
├── .env                      # Environment variables
├── requirements.txt          # Dependencies
├── setup.py                  # Package setup
└── run.py                    # Application entry point
```

## Key Components

### Application Entry Point

The `run.py` file serves as the main entry point for the application. It imports the Flask application factory from `src/web/app.py` and runs the application.

### Core Module

The `src/core` module contains the core application logic:

- **Models**: Database models and ORM-like functionality
- **Services**: Business logic services that implement the application's features
- **Utils**: Utility functions and helpers used throughout the application

### Web Module

The `src/web` module handles the web interface:

- **Routes**: Flask route definitions organized by feature
- **Templates**: HTML templates using Jinja2
- **Static**: Static assets like JavaScript, CSS, and images

### AI Module

The `src/ai` module contains AI-related functionality:

- **Helpers**: Helper classes for AI features like roadmap generation, insights, and notifications
- **Prompts**: System prompts and templates for the AI models

### Configuration

The `config` directory contains configuration files for different environments (development, testing, production).

### Scripts

The `scripts` directory contains utility scripts for tasks like database migration, setup, and testing.

### Migrations

The `migrations` directory contains database migration scripts to manage schema changes.

## Blueprint Structure

The application uses Flask blueprints to organize routes by feature:

- **auth**: Authentication routes (login, register, logout)
- **index**: Main index and dashboard routes
- **goals**: Goal management routes
- **habits**: Habit tracking routes
- **routines**: Routine management routes
- **analytics**: Data analysis and visualization routes
- **ai_roadmap**: AI roadmap generation routes
- **ai_insights**: AI insights and suggestions routes
- **ai_notifications**: AI notification routes
- **gamification**: Gamification features (achievements, challenges, levels)

## Database Structure

The database is stored in the `instance` directory and contains tables for:

- Users and authentication
- Goals, habits, and routines
- Tracking data for habits and mood
- AI-generated content (roadmaps, insights)
- Gamification elements (achievements, challenges, levels)

## Configuration

The application uses environment variables loaded from a `.env` file for configuration. Key settings include:

- Secret key for session security
- API keys for external services (Groq)
- Feature flags for enabling/disabling features
- Database configuration

## Testing

The `tests` directory contains unit and integration tests for the application. The test suite can be run using pytest.

## Documentation

The `docs` directory contains documentation for the application, including:

- This codebase structure document
- Feature-specific documentation (gamification, AI features)
- Implementation summaries and guides
