# Personal Growth Navigator

A web application for personal growth tracking, habit formation, and routine optimization with AI assistance.

## Project Structure

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
├── .env                      # Environment variables
├── requirements.txt          # Dependencies
├── setup.py                  # Package setup
└── run.py                    # Application entry point
```

## Features

- User authentication and profile management
- Goal setting and tracking
- Habit formation and monitoring
- Daily routine creation and optimization
- AI-powered roadmap generation
- AI insights and analytics
- Personalized notifications and reminders
- Gamification elements (achievements, challenges, levels)
- Mood and energy tracking
- Social features for accountability

## Setup and Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Set up environment variables in `.env` file
6. Initialize the database: `flask init-db`
7. Run the application: `python run.py`

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```
SECRET_KEY=your_secret_key
GROQ_API_KEY=your_groq_api_key
AI_MODEL=llama3-8b-8192
DEBUG=True
ENABLE_NOTIFICATIONS=True
NOTIFICATION_FREQUENCY=daily
ENABLE_GAMIFICATION=True
```

## Development

To set up a development environment:

1. Install development dependencies: `pip install -r requirements-dev.txt`
2. Run tests: `pytest`
3. Check code style: `flake8`

## Demo Data

To populate the application with demo data:

```
flask setup-demo
```

This will create a demo user with sample goals, habits, routines, and tracking data.

## License

[MIT License](LICENSE)
