# setup_demo.py
import sqlite3
import os
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random
import json

# AI response from the bot
AI_RESPONSE = """Goal Analysis & Prioritization
You have three clear priorities:

Physical fitness (joining a gym and establishing an exercise routine)
Data science skill development (progressing from basic knowledge to coding proficiency)
Mastering your new codebase as a software engineer (maximizing understanding efficiently)

These goals align well together - improving physical fitness can enhance cognitive function for learning, while data science skills will complement your software engineering role.
Routine Engineering Framework
Morning Routine (Leveraging 8-10 AM energy peak)

6:45 AM: Wake up (15 minutes earlier than current)
7:00-7:30 AM: Quick morning workout at home (until gym membership)
7:30-8:00 AM: Breakfast + preparation for day
8:00-10:00 AM: Deep Work Block - Dedicated to codebase learning or most complex task

Mid-Day Management (Addressing 11 AM energy dip)

10:00-11:00 AM: Team meetings/collaboration (when energy starts declining)
11:00-11:30 AM: Quick walk/movement break + healthy snack (combating energy dip)
11:30-1:00 PM: Lighter work tasks (emails, documentation, simpler coding tasks)

Afternoon Strategy

1:00-1:45 PM: Lunch + short break
1:45-4:30 PM: Mixed work tasks (balance between challenging and routine tasks)
4:30-5:30 PM: Administrative work/planning for tomorrow

Evening Optimization (Using 5:30-7:30 PM energy peak)

5:30-7:00 PM: Skill Development Block - Focused data science learning/practice
7:00-8:00 PM: Exercise (gym once joined, or home workout)
8:00-9:00 PM: Dinner + relaxation
9:00-10:30 PM: Personal time/light reading/prep for next day
10:30-11:00 PM: Wind-down routine (avoiding screens)
11:00 PM: Sleep (1 hour earlier than current for better recovery)

Implementation Strategy
Physical Fitness Goal

Immediate Action: Research gym options near home/work this week - set calendar alert for Thursday evening to investigate options
Short-Term: Until gym membership, implement daily 30-minute home workouts:

Monday/Thursday: Basic strength (push-ups, squats, planks)
Tuesday/Friday: Cardio (jumping jacks, high knees, burpees)
Wednesday/Saturday: Flexibility/mobility
Sunday: Active recovery (walking)


Habit Stacking: Attach 10-minute stretching routine to your morning coffee/breakfast

Data Science Development

Structure: Allocate the 5:30-7:00 PM energy peak to focused learning
Micro-Learning: Break down concepts into 25-minute focused sessions followed by 5-minute breaks
Progressive Challenge:

Week 1-2: Study fundamentals + modify existing code examples
Week 3-4: Work on small independent projects with guidance
Week 5+: Begin writing code from scratch on real problems



Codebase Mastery

Morning Deep Work: Use 8:00-10:00 AM peak for focused codebase exploration
Structured Approach:

Map the codebase architecture visually
Focus on one module/component at a time
Document insights and connections in a personal knowledge base


Active Learning: Implement small modifications to understand system behavior

Addressing Key Challenges
Focus Duration Issues

Start with 25-minute focused sessions (Pomodoro technique)
Gradually extend to 45-minute sessions as focus improves
Remove digital distractions during focus blocks (notifications off)
Create a dedicated workspace with minimal visual distractions

Priority Task Completion

Begin each day by identifying 1-3 "must complete" tasks
Schedule these during your energy peak hours
Use the "touch it once" principle - when you start a priority task, commit to a meaningful step forward
Create visual progress trackers for long-term projects

Adaptive Planning
I recommend starting with this framework for one week, then we can reassess based on what's working and what needs adjustment. The key is consistency with the core elements while remaining flexible about specific implementation."""

# Formatted AI response with proper sections for extraction
FORMATTED_AI_RESPONSE = """Here's your personalized growth roadmap based on your goals and current situation:

## GOALS
- Join a gym and establish exercise routine
- Progress from basic to proficient data science coding
- Master new codebase efficiently as software engineer

## HABITS
- 30-minute morning workout before breakfast
- Daily 25-minute focused data science learning
- Document codebase insights in knowledge base
- Identify 3 priority tasks each morning
- 10-minute stretching with morning coffee
- Sleep by 11:00 PM for better recovery

## ROUTINES
- 6:45 AM: Wake up (15 minutes earlier)
- 7:00-7:30 AM: Quick morning workout at home
- 8:00-10:00 AM: Deep Work Block for codebase
- 11:00-11:30 AM: Walk/movement break with snack
- 5:30-7:00 PM: Data science skill development
- 10:30-11:00 PM: Screen-free wind-down routine

## NOTES
The framework leverages your natural energy peaks (8-10 AM and 5:30-7:30 PM) for your most demanding cognitive tasks. The morning deep work block is dedicated to codebase mastery, while the evening energy peak is reserved for data science skill development.

For physical fitness, start with home workouts until you join a gym, following a structured weekly pattern (strength, cardio, flexibility). The 10-minute stretching habit stacked with your morning coffee creates an easy implementation trigger.

To address focus challenges, begin with 25-minute Pomodoro sessions and gradually extend as your concentration improves. The priority task system ensures you make progress on important goals during your peak energy periods.

I recommend following this framework for one week, then reassessing based on what's working and what needs adjustment. The key is consistency with the core elements while remaining flexible about specific implementation details.
"""

# Connect to the database
def get_db_connection():
    conn = sqlite3.connect('growth_navigator.db')
    conn.row_factory = sqlite3.Row
    return conn

# Create the database and tables if they don't exist
def create_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if tables exist
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cursor.fetchone():
            print("Tables already exist. Skipping creation.")
            conn.close()
            return
    except:
        # If there's an error, we'll proceed with creating tables
        pass

    print("Creating database tables...")

    # Create users table
    cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        partner_id INTEGER,
        is_new_user BOOLEAN DEFAULT 1,
        FOREIGN KEY (partner_id) REFERENCES users (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        deadline TEXT,
        priority INTEGER,
        status TEXT DEFAULT 'active',
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE routines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        time_block TEXT NOT NULL,
        activity TEXT NOT NULL,
        duration INTEGER,
        energy_level TEXT,
        weekdays TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE habits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        goal_id INTEGER,
        frequency TEXT,
        streak INTEGER DEFAULT 0,
        created_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (goal_id) REFERENCES goals (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE habit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        habit_id INTEGER,
        completed_date TEXT,
        notes TEXT,
        FOREIGN KEY (habit_id) REFERENCES habits (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE ai_conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        user_message TEXT NOT NULL,
        ai_response TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE ai_roadmaps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    conn.commit()
    conn.close()
    print("Database and tables created successfully.")

# Create a demo user
def create_demo_user():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if user already exists
    cursor.execute('SELECT id FROM users WHERE username = ?', ('amlan',))
    existing_user = cursor.fetchone()

    if existing_user:
        print("Demo user 'amlan' already exists.")
        user_id = existing_user[0]
    else:
        # Create the demo user
        cursor.execute(
            'INSERT INTO users (username, password, name, is_new_user) VALUES (?, ?, ?, ?)',
            ('amlan', generate_password_hash('test'), 'Amlan', 0)
        )
        conn.commit()
        user_id = cursor.lastrowid
        print(f"Demo user 'amlan' created with ID: {user_id}")

    conn.close()
    return user_id

# Add goals for the demo user
def add_demo_goals(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if goals already exist for this user
    cursor.execute('SELECT COUNT(*) FROM goals WHERE user_id = ?', (user_id,))
    if cursor.fetchone()[0] > 0:
        print("Goals already exist for this user. Skipping.")
        conn.close()
        return

    # Demo goals
    goals = [
        ('Physical Fitness', 'Join a gym and establish a consistent exercise routine', '2023-07-01', 1),
        ('Learning', 'Progress from basic to proficient data science coding skills', '2023-09-01', 2),
        ('Career', 'Master new codebase efficiently as a software engineer', '2023-06-15', 1)
    ]

    for category, description, deadline, priority in goals:
        cursor.execute(
            'INSERT INTO goals (user_id, category, description, deadline, priority, status) VALUES (?, ?, ?, ?, ?, ?)',
            (user_id, category, description, deadline, priority, 'active')
        )

    conn.commit()
    print(f"Added {len(goals)} goals for the demo user.")

    # Get the goal IDs for later use
    cursor.execute('SELECT id, category FROM goals WHERE user_id = ?', (user_id,))
    goal_ids = {row[1]: row[0] for row in cursor.fetchall()}

    conn.close()
    return goal_ids

# Add habits for the demo user
def add_demo_habits(user_id, goal_ids):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if habits already exist for this user
    cursor.execute('SELECT COUNT(*) FROM habits WHERE user_id = ?', (user_id,))
    if cursor.fetchone()[0] > 0:
        print("Habits already exist for this user. Skipping.")
        conn.close()
        return

    # Demo habits
    habits = [
        ('30-minute morning workout before breakfast', goal_ids.get('Physical Fitness'), 'daily', '2023-04-01'),
        ('Daily 25-minute focused data science learning', goal_ids.get('Learning'), 'daily', '2023-04-01'),
        ('Document codebase insights in knowledge base', goal_ids.get('Career'), 'daily', '2023-04-01'),
        ('Identify 3 priority tasks each morning', None, 'daily', '2023-04-01'),
        ('10-minute stretching with morning coffee', goal_ids.get('Physical Fitness'), 'daily', '2023-04-01'),
        ('Sleep by 11:00 PM for better recovery', goal_ids.get('Physical Fitness'), 'daily', '2023-04-01')
    ]

    habit_ids = []
    for name, goal_id, frequency, created_at in habits:
        cursor.execute(
            'INSERT INTO habits (user_id, name, goal_id, frequency, streak, created_at) VALUES (?, ?, ?, ?, ?, ?)',
            (user_id, name, goal_id, frequency, random.randint(0, 5), created_at)
        )
        habit_ids.append(cursor.lastrowid)

    conn.commit()
    print(f"Added {len(habits)} habits for the demo user.")
    conn.close()
    return habit_ids

# Add routines for the demo user
def add_demo_routines(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if routines already exist for this user
    cursor.execute('SELECT COUNT(*) FROM routines WHERE user_id = ?', (user_id,))
    if cursor.fetchone()[0] > 0:
        print("Routines already exist for this user. Skipping.")
        conn.close()
        return

    # Demo routines
    routines = [
        ('Morning', 'Wake up', 15, 'Medium', 'Monday,Tuesday,Wednesday,Thursday,Friday'),
        ('Morning', 'Quick morning workout at home', 30, 'High', 'Monday,Tuesday,Wednesday,Thursday,Friday'),
        ('Morning', 'Deep Work Block for codebase study', 120, 'High', 'Monday,Tuesday,Wednesday,Thursday,Friday'),
        ('Midday', 'Team meetings/collaboration', 60, 'Medium', 'Monday,Tuesday,Wednesday,Thursday,Friday'),
        ('Midday', 'Walk/movement break with snack', 30, 'Medium', 'Monday,Tuesday,Wednesday,Thursday,Friday'),
        ('Midday', 'Lighter work tasks', 90, 'Low', 'Monday,Tuesday,Wednesday,Thursday,Friday'),
        ('Afternoon', 'Lunch + short break', 45, 'Low', 'Monday,Tuesday,Wednesday,Thursday,Friday'),
        ('Afternoon', 'Mixed work tasks', 165, 'Medium', 'Monday,Tuesday,Wednesday,Thursday,Friday'),
        ('Afternoon', 'Administrative work/planning', 60, 'Medium', 'Monday,Tuesday,Wednesday,Thursday,Friday'),
        ('Evening', 'Data science skill development', 90, 'High', 'Monday,Tuesday,Wednesday,Thursday,Friday'),
        ('Evening', 'Exercise (gym or home workout)', 60, 'High', 'Monday,Tuesday,Wednesday,Thursday,Friday'),
        ('Evening', 'Dinner + relaxation', 60, 'Low', 'Monday,Tuesday,Wednesday,Thursday,Friday,Saturday,Sunday'),
        ('Evening', 'Personal time/reading/prep', 90, 'Low', 'Monday,Tuesday,Wednesday,Thursday,Friday,Saturday,Sunday'),
        ('Evening', 'Screen-free wind-down routine', 30, 'Low', 'Monday,Tuesday,Wednesday,Thursday,Friday,Saturday,Sunday')
    ]

    for time_block, activity, duration, energy_level, weekdays in routines:
        cursor.execute(
            'INSERT INTO routines (user_id, time_block, activity, duration, energy_level, weekdays) VALUES (?, ?, ?, ?, ?, ?)',
            (user_id, time_block, activity, duration, energy_level, weekdays)
        )

    conn.commit()
    print(f"Added {len(routines)} routines for the demo user.")
    conn.close()

# Add habit logs with some inconsistency
def add_demo_habit_logs(habit_ids):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if habit logs already exist
    cursor.execute('SELECT COUNT(*) FROM habit_logs')
    if cursor.fetchone()[0] > 0:
        print("Habit logs already exist. Skipping.")
        conn.close()
        return

    # Generate logs from April 1st to current date
    start_date = datetime(2023, 4, 1)
    end_date = datetime.now()

    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')

        for habit_id in habit_ids:
            # Add some inconsistency - 70% chance of completing a habit
            if random.random() < 0.7:
                cursor.execute(
                    'INSERT INTO habit_logs (habit_id, completed_date, notes) VALUES (?, ?, ?)',
                    (habit_id, date_str, '')
                )

        current_date += timedelta(days=1)

    conn.commit()
    print("Added habit logs with some inconsistency.")
    conn.close()

# Add AI conversation and roadmap
def add_demo_ai_data(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if AI conversations already exist for this user
    cursor.execute('SELECT COUNT(*) FROM ai_conversations WHERE user_id = ?', (user_id,))
    if cursor.fetchone()[0] > 0:
        print("AI conversations already exist for this user. Skipping.")
    else:
        # Add the conversation
        cursor.execute(
            'INSERT INTO ai_conversations (user_id, user_message, ai_response, timestamp) VALUES (?, ?, ?, ?)',
            (user_id, "I need help creating a personal growth plan that balances my physical fitness goals, data science learning, and mastering a new codebase as a software engineer.",
             AI_RESPONSE, '2023-04-01 09:15:23')
        )
        print("Added demo AI conversation.")

    # Check if AI roadmaps already exist for this user
    cursor.execute('SELECT COUNT(*) FROM ai_roadmaps WHERE user_id = ?', (user_id,))
    if cursor.fetchone()[0] > 0:
        print("AI roadmaps already exist for this user. Skipping.")
    else:
        # Add the roadmap
        cursor.execute(
            'INSERT INTO ai_roadmaps (user_id, title, content, created_at) VALUES (?, ?, ?, ?)',
            (user_id, "Personal Growth Plan - April 2023", FORMATTED_AI_RESPONSE, '2023-04-01 09:20:45')
        )
        print("Added demo AI roadmap.")

    conn.commit()
    conn.close()

# Main function to set up the demo
def setup_demo():
    print("Setting up demo for Personal Growth Navigator...")
    create_database()
    user_id = create_demo_user()
    goal_ids = add_demo_goals(user_id)
    habit_ids = add_demo_habits(user_id, goal_ids)
    add_demo_routines(user_id)
    add_demo_habit_logs(habit_ids)
    add_demo_ai_data(user_id)
    print("Demo setup complete!")

if __name__ == "__main__":
    setup_demo()
