# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, g
import sqlite3
import os
import json
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from ai_helper import AIHelper, create_env_file
from gamification_helper import GamificationHelper
from ai_insights_helper import AIInsightsHelper
from ai_notification_helper import AINotificationHelper
import schema_updates_mood
import schema_updates_ai_notifications
import schema_updates_scheduled_notifications
from notification_scheduler import start_notification_scheduler
app = Flask(__name__)
app.secret_key = "personal_growth_navigator_secret_key"

# Make datetime available to all templates
app.jinja_env.globals['datetime'] = datetime

# Custom Jinja2 filters
@app.template_filter('datetime_format')
def datetime_format_filter(value):
    """Format a datetime string to a more readable format."""
    if not value:
        return ""
    try:
        dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%b %d, %Y at %I:%M %p')
    except ValueError:
        return value

# Update database schema for mood tracking, AI notifications, and scheduled notifications
schema_updates_mood.update_database_schema_for_mood()
schema_updates_ai_notifications.update_database_schema_for_ai_notifications()
schema_updates_scheduled_notifications.update_database_schema_for_scheduled_notifications()

# Start the notification scheduler
start_notification_scheduler()

# Create .env file if it doesn't exist
create_env_file()

# Initialize AI Helper
ai_helper = None

def get_ai_helper():
    global ai_helper
    if ai_helper is None:
        ai_helper = AIHelper()
    return ai_helper

# Initialize Gamification Helper
gamification_helper = None

def get_gamification_helper():
    global gamification_helper
    if gamification_helper is None:
        gamification_helper = GamificationHelper()
    return gamification_helper

# Initialize AI Insights Helper
ai_insights_helper = None

def get_ai_insights_helper():
    global ai_insights_helper
    if ai_insights_helper is None:
        ai_insights_helper = AIInsightsHelper()
    return ai_insights_helper

# Initialize AI Notification Helper
ai_notification_helper = None

def get_ai_notification_helper():
    global ai_notification_helper
    if ai_notification_helper is None:
        ai_notification_helper = AINotificationHelper()
    return ai_notification_helper

# Database setup
def get_db_connection():
    if not os.path.exists('growth_navigator.db'):
        conn = sqlite3.connect('growth_navigator.db')
        cursor = conn.cursor()

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

        # Create AI conversations table
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

        # Create AI roadmaps table
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
        return conn
    else:
        return sqlite3.connect('growth_navigator.db')

# User session management
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    if 'user_id' in session:
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()
        return user
    return None

def get_partner():
    user = get_current_user()
    if user and user[4]:  # partner_id
        conn = get_db_connection()
        partner = conn.execute('SELECT * FROM users WHERE id = ?', (user[4],)).fetchone()
        conn.close()
        return partner
    return None

# Routes
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match')
            return render_template('signup.html')

        conn = get_db_connection()

        # Check if username already exists
        existing_user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if existing_user:
            conn.close()
            flash('Username already exists. Please choose another one.')
            return render_template('signup.html')

        # Create new user
        conn.execute('INSERT INTO users (username, password, name, is_new_user) VALUES (?, ?, ?, ?)',
                    (username, generate_password_hash(password), name, 1))
        conn.commit()

        # Get the new user's ID
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        # Log in the new user
        session['user_id'] = user[0]
        session['username'] = user[1]
        session['name'] = user[3]

        flash(f'Welcome, {name}! Your account has been created.')
        return redirect(url_for('welcome'))

    return render_template('signup.html')

@app.route('/welcome')
@login_required
def welcome():
    user_id = session['user_id']
    conn = get_db_connection()

    # Mark user as not new anymore
    conn.execute('UPDATE users SET is_new_user = 0 WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

    return render_template('welcome.html', current_user=get_current_user(), partner=get_partner())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['name'] = user[3]

            # Check if this is a new user
            is_new_user = user[5]
            conn.close()

            if is_new_user:
                flash(f'Welcome back, {user[3]}!')
                return redirect(url_for('welcome'))
            else:
                flash(f'Welcome back, {user[3]}!')
                return redirect(url_for('index'))
        else:
            conn.close()
            flash('Invalid username or password')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    user_id = session['user_id']
    conn = get_db_connection()

    # Get goals
    goals = conn.execute('SELECT * FROM goals WHERE user_id = ? AND status = "active" ORDER BY priority',
                        (user_id,)).fetchall()

    # Get today's routine
    today_name = datetime.now().strftime('%A')
    routines = conn.execute('SELECT * FROM routines WHERE user_id = ? AND weekdays LIKE ? ORDER BY time_block',
                           (user_id, f'%{today_name}%')).fetchall()

    # Get habits
    habits = conn.execute('''
        SELECT h.*, g.description as goal_description,
        (SELECT COUNT(*) FROM habit_logs hl WHERE hl.habit_id = h.id AND hl.completed_date = ?) as completed_today
        FROM habits h
        LEFT JOIN goals g ON h.goal_id = g.id
        WHERE h.user_id = ?
    ''', (date.today().strftime('%Y-%m-%d'), user_id)).fetchall()

    # Get completion data for calendar view
    habit_logs = conn.execute('''
        SELECT hl.habit_id, hl.completed_date, COUNT(*) as count
        FROM habit_logs hl
        JOIN habits h ON hl.habit_id = h.id
        WHERE h.user_id = ?
        GROUP BY hl.habit_id, hl.completed_date
    ''', (user_id,)).fetchall()

    # Convert to format needed for calendar
    calendar_data = {}
    for log in habit_logs:
        habit_id = log[0]
        completed_date = log[1]

        if habit_id not in calendar_data:
            calendar_data[habit_id] = []

        calendar_data[habit_id].append(completed_date)

    # Get user level info
    helper = get_gamification_helper()
    level_info = helper.get_user_level_info(user_id)

    # Get mood history for the last 7 days
    mood_history = conn.execute('''
        SELECT mood_score, mood_note, energy_level, logged_at
        FROM mood_logs
        WHERE user_id = ?
        ORDER BY logged_at DESC
        LIMIT 7
    ''', (user_id,)).fetchall()

    # Format the mood history data
    formatted_mood_history = []
    for entry in mood_history:
        formatted_mood_history.append({
            'mood_score': entry[0],
            'mood_note': entry[1],
            'energy_level': entry[2],
            'logged_at': datetime.strptime(entry[3], '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y')
        })

    # Check if mood logged today
    today = date.today().strftime('%Y-%m-%d')
    mood_today = conn.execute('''
        SELECT mood_score FROM mood_logs
        WHERE user_id = ? AND date(logged_at) = ?
    ''', (user_id, today)).fetchone()

    conn.close()

    return render_template('index.html', goals=goals, routines=routines, habits=habits,
                          today=date.today().strftime('%Y-%m-%d'),
                          now=datetime.now(),
                          current_user=get_current_user(),
                          partner=get_partner(),
                          level_info=level_info,
                          calendar_data=calendar_data,
                          mood_history=formatted_mood_history,
                          mood_today=mood_today[0] if mood_today else None,
                          use_custom_energy_legend=True)

@app.route('/goals')
@login_required
def view_goals():
    user_id = session['user_id']
    conn = get_db_connection()
    goals = conn.execute('SELECT * FROM goals WHERE user_id = ? ORDER BY priority', (user_id,)).fetchall()

    # Debug: Print goals to console
    print(f"DEBUG - Goals for user {user_id}: {goals}")

    conn.close()
    return render_template('goals.html', goals=goals, current_user=get_current_user(), partner=get_partner())

@app.route('/goals/add', methods=['GET', 'POST'])
@login_required
def add_goal():
    user_id = session['user_id']
    if request.method == 'POST':
        category = request.form['category']
        description = request.form['description']
        deadline = request.form['deadline']
        priority = request.form['priority']

        conn = get_db_connection()
        conn.execute('INSERT INTO goals (user_id, category, description, deadline, priority, status) VALUES (?, ?, ?, ?, ?, ?)',
                    (user_id, category, description, deadline, priority, 'active'))
        conn.commit()
        conn.close()

        flash('Goal added successfully!')
        return redirect(url_for('view_goals'))

    return render_template('add_goal.html', current_user=get_current_user(), partner=get_partner())

@app.route('/goals/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_goal(id):
    user_id = session['user_id']
    conn = get_db_connection()
    goal = conn.execute('SELECT * FROM goals WHERE id = ? AND user_id = ?', (id, user_id)).fetchone()

    if not goal:
        flash('Goal not found or you do not have permission to edit it')
        conn.close()
        return redirect(url_for('view_goals'))

    if request.method == 'POST':
        category = request.form['category']
        description = request.form['description']
        deadline = request.form['deadline']
        priority = request.form['priority']
        status = request.form['status']

        conn.execute('UPDATE goals SET category = ?, description = ?, deadline = ?, priority = ?, status = ? WHERE id = ? AND user_id = ?',
                    (category, description, deadline, priority, status, id, user_id))
        conn.commit()
        conn.close()

        flash('Goal updated successfully!')
        return redirect(url_for('view_goals'))

    conn.close()
    return render_template('edit_goal.html', goal=goal, current_user=get_current_user(), partner=get_partner())

@app.route('/routines')
@login_required
def view_routines():
    user_id = session['user_id']
    conn = get_db_connection()
    routines = conn.execute('SELECT * FROM routines WHERE user_id = ? ORDER BY time_block', (user_id,)).fetchall()

    # Debug: Print routines to console
    print(f"DEBUG - Routines for user {user_id}: {routines}")

    conn.close()

    # Get current day of the week
    today_name = datetime.now().strftime('%A')

    # Pass all weekdays and highlight the current day
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    return render_template('routines.html',
                          routines=routines,
                          today_name=today_name,
                          weekdays=weekdays,
                          current_user=get_current_user(),
                          partner=get_partner(),
                          use_custom_energy_legend=True)

@app.route('/routines/add', methods=['GET', 'POST'])
@login_required
def add_routine():
    user_id = session['user_id']
    if request.method == 'POST':
        time_block = request.form['time_block']
        activity = request.form['activity']
        duration = request.form['duration']
        energy_level = request.form['energy_level']
        weekdays = ','.join(request.form.getlist('weekdays'))

        conn = get_db_connection()
        conn.execute('INSERT INTO routines (user_id, time_block, activity, duration, energy_level, weekdays) VALUES (?, ?, ?, ?, ?, ?)',
                    (user_id, time_block, activity, duration, energy_level, weekdays))
        conn.commit()
        conn.close()

        flash('Routine activity added successfully!')
        return redirect(url_for('view_routines'))

    return render_template('add_routine.html', current_user=get_current_user(), partner=get_partner())

@app.route('/routines/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_routine(id):
    user_id = session['user_id']
    conn = get_db_connection()
    routine = conn.execute('SELECT * FROM routines WHERE id = ? AND user_id = ?', (id, user_id)).fetchone()

    if not routine:
        flash('Routine not found or you do not have permission to edit it')
        conn.close()
        return redirect(url_for('view_routines'))

    if request.method == 'POST':
        time_block = request.form['time_block']
        activity = request.form['activity']
        duration = request.form['duration']
        energy_level = request.form['energy_level']
        weekdays = ','.join(request.form.getlist('weekdays'))

        conn.execute('UPDATE routines SET time_block = ?, activity = ?, duration = ?, energy_level = ?, weekdays = ? WHERE id = ? AND user_id = ?',
                    (time_block, activity, duration, energy_level, weekdays, id, user_id))
        conn.commit()
        conn.close()

        flash('Routine updated successfully!')
        return redirect(url_for('view_routines'))

    weekdays = routine[6].split(',') if routine[6] else []  # Adjusted index for user_id column
    conn.close()
    return render_template('edit_routine.html', routine=routine, selected_weekdays=weekdays, current_user=get_current_user(), partner=get_partner())

@app.route('/habits')
@login_required
def view_habits():
    user_id = session['user_id']
    conn = get_db_connection()
    habits = conn.execute('''
        SELECT h.*, g.description as goal_description
        FROM habits h
        LEFT JOIN goals g ON h.goal_id = g.id
        WHERE h.user_id = ?
        ORDER BY h.name
    ''', (user_id,)).fetchall()

    # Debug: Print habits to console
    print(f"DEBUG - Habits for user {user_id}: {habits}")

    # Get completion data for calendar view
    habit_logs = conn.execute('''
        SELECT hl.habit_id, hl.completed_date, COUNT(*) as count
        FROM habit_logs hl
        JOIN habits h ON hl.habit_id = h.id
        WHERE h.user_id = ?
        GROUP BY hl.habit_id, hl.completed_date
    ''', (user_id,)).fetchall()

    # Convert to format needed for calendar
    calendar_data = {}
    for log in habit_logs:
        habit_id = log[0]
        completed_date = log[1]

        if habit_id not in calendar_data:
            calendar_data[habit_id] = []

        calendar_data[habit_id].append(completed_date)

    # Debug: Print calendar data
    print(f"DEBUG - Calendar data: {calendar_data}")

    conn.close()

    return render_template('habits.html', habits=habits, calendar_data=calendar_data,
                          today=date.today().strftime('%Y-%m-%d'),
                          current_user=get_current_user(), partner=get_partner())

@app.route('/habits/add', methods=['GET', 'POST'])
@login_required
def add_habit():
    user_id = session['user_id']
    if request.method == 'POST':
        name = request.form['name']
        goal_id = request.form['goal_id'] if request.form['goal_id'] != '' else None
        frequency = request.form['frequency']

        conn = get_db_connection()
        conn.execute('INSERT INTO habits (user_id, name, goal_id, frequency, streak, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                    (user_id, name, goal_id, frequency, 0, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        conn.close()

        flash('Habit added successfully!')
        return redirect(url_for('view_habits'))

    conn = get_db_connection()
    goals = conn.execute('SELECT id, description FROM goals WHERE user_id = ? AND status = "active"', (user_id,)).fetchall()
    conn.close()

    return render_template('add_habit.html', goals=goals, current_user=get_current_user(), partner=get_partner())

# Original log_habit function has been replaced with the gamified version below

@app.route('/habits/add_multiple', methods=['POST'])
@login_required
def add_multiple_habits():
    user_id = session['user_id']
    goal_id = request.form.get('goal_id')
    selected_habits_json = request.form.get('selected_habits', '[]')

    try:
        selected_habits = json.loads(selected_habits_json)

        if not selected_habits:
            flash('No habits selected to add')
            return redirect(url_for('view_habits'))

        conn = get_db_connection()

        # Verify the goal belongs to the current user if provided
        if goal_id:
            goal = conn.execute('SELECT id FROM goals WHERE id = ? AND user_id = ?', (goal_id, user_id)).fetchone()
            if not goal:
                flash('Goal not found or you do not have permission to add habits to it')
                conn.close()
                return redirect(url_for('view_habits'))

        # Add each habit
        for habit in selected_habits:
            name = habit.get('name', '')
            frequency = habit.get('frequency', 'daily')

            # Handle custom frequency
            if frequency == 'custom' and 'custom_days' in habit:
                frequency = habit['custom_days']

            conn.execute('INSERT INTO habits (user_id, name, goal_id, frequency, streak, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                        (user_id, name, goal_id, frequency, 0, datetime.now().strftime('%Y-%m-%d')))

        conn.commit()
        conn.close()

        flash(f'Successfully added {len(selected_habits)} habits!')
        return redirect(url_for('view_habits'))

    except json.JSONDecodeError:
        flash('Error processing habit data')
        return redirect(url_for('view_habits'))

@app.route('/habits/quick_log')
@login_required
def quick_log_habits():
    user_id = session['user_id']
    today = date.today().strftime('%Y-%m-%d')

    conn = get_db_connection()

    # Get all habits for the user
    habits_data = conn.execute('''
        SELECT id, name, streak FROM habits WHERE user_id = ? ORDER BY name
    ''', (user_id,)).fetchall()

    # Get habits completed today
    completed_today = conn.execute('''
        SELECT habit_id FROM habit_logs
        WHERE habit_id IN (SELECT id FROM habits WHERE user_id = ?)
        AND completed_date = ?
    ''', (user_id, today)).fetchall()

    conn.close()

    # Format the data for JSON response
    habits = []
    for habit in habits_data:
        habits.append({
            'id': habit[0],
            'name': habit[1],
            'streak': habit[2]
        })

    completed_ids = [log[0] for log in completed_today]

    return jsonify({
        'habits': habits,
        'completed_today': completed_ids
    })

@app.route('/habits/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_habit(id):
    user_id = session['user_id']
    conn = get_db_connection()
    habit = conn.execute('SELECT * FROM habits WHERE id = ? AND user_id = ?', (id, user_id)).fetchone()

    if not habit:
        flash('Habit not found or you do not have permission to edit it')
        conn.close()
        return redirect(url_for('view_habits'))

    if request.method == 'POST':
        name = request.form['name']
        goal_id = request.form['goal_id'] if request.form['goal_id'] != '' else None
        frequency = request.form['frequency']
        streak = int(request.form['streak'])

        conn.execute('UPDATE habits SET name = ?, goal_id = ?, frequency = ?, streak = ? WHERE id = ? AND user_id = ?',
                    (name, goal_id, frequency, streak, id, user_id))
        conn.commit()
        conn.close()

        flash('Habit updated successfully!')
        return redirect(url_for('view_habits'))

    goals = conn.execute('SELECT id, description FROM goals WHERE user_id = ? AND status = "active"', (user_id,)).fetchall()
    conn.close()
    return render_template('edit_habit.html', habit=habit, goals=goals, current_user=get_current_user(), partner=get_partner())

@app.route('/habits/delete/<int:id>', methods=['POST'])
@login_required
def delete_habit(id):
    user_id = session['user_id']
    conn = get_db_connection()

    # Verify the habit belongs to the current user
    habit = conn.execute('SELECT * FROM habits WHERE id = ? AND user_id = ?', (id, user_id)).fetchone()
    if not habit:
        flash('Habit not found or you do not have permission to delete it')
        conn.close()
        return redirect(url_for('view_habits'))

    # Delete habit logs first (foreign key constraint)
    conn.execute('DELETE FROM habit_logs WHERE habit_id = ?', (id,))

    # Delete the habit
    conn.execute('DELETE FROM habits WHERE id = ? AND user_id = ?', (id, user_id))

    conn.commit()
    conn.close()

    flash('Habit deleted successfully!')
    return redirect(url_for('view_habits'))

@app.route('/analytics')
@login_required
def analytics():
    user_id = session['user_id']
    conn = get_db_connection()

    # Get habit completion rates
    habits = conn.execute('''
        SELECT h.id, h.name, h.created_at,
        (SELECT COUNT(*) FROM habit_logs hl WHERE hl.habit_id = h.id) as total_completions,
        (julianday('now') - julianday(h.created_at)) as days_since_creation
        FROM habits h
        WHERE h.user_id = ?
    ''', (user_id,)).fetchall()

    habit_stats = []
    for habit in habits:
        habit_id, name, created_at, total_completions, days_since_creation = habit

        if days_since_creation > 0:
            completion_rate = (total_completions / days_since_creation) * 100
        else:
            completion_rate = 0

        habit_stats.append({
            'id': habit_id,
            'name': name,
            'created_at': created_at,
            'total_completions': total_completions,
            'days_since_creation': int(days_since_creation),
            'completion_rate': round(completion_rate, 1),
            'current_streak': conn.execute('SELECT streak FROM habits WHERE id = ?', (habit_id,)).fetchone()[0]
        })

    # Get today's energy distribution
    today_name = datetime.now().strftime('%A')
    energy_distribution = conn.execute('''
        SELECT energy_level, SUM(duration) as total_minutes
        FROM routines
        WHERE user_id = ? AND weekdays LIKE ?
        GROUP BY energy_level
    ''', (user_id, f'%{today_name}%')).fetchall()

    conn.close()

    return render_template('analytics.html', habit_stats=habit_stats, energy_distribution=energy_distribution,
                          current_user=get_current_user(), partner=get_partner(),
                          use_custom_energy_legend=True)

# Partner view routes
@app.route('/partner/habits')
@login_required
def view_partner_habits():
    user = get_current_user()
    if not user or not user[4]:  # Check if user has a partner
        flash('No partner account is linked to your account')
        return redirect(url_for('index'))

    partner_id = user[4]
    conn = get_db_connection()

    # Get partner's habits
    habits = conn.execute('''
        SELECT h.*, g.description as goal_description
        FROM habits h
        LEFT JOIN goals g ON h.goal_id = g.id
        WHERE h.user_id = ?
        ORDER BY h.name
    ''', (partner_id,)).fetchall()

    # Get partner's habit completion data
    habit_logs = conn.execute('''
        SELECT hl.habit_id, hl.completed_date, COUNT(*) as count
        FROM habit_logs hl
        JOIN habits h ON hl.habit_id = h.id
        WHERE h.user_id = ?
        GROUP BY hl.habit_id, hl.completed_date
    ''', (partner_id,)).fetchall()

    # Convert to format needed for calendar
    calendar_data = {}
    for log in habit_logs:
        habit_id = log[0]
        completed_date = log[1]

        if habit_id not in calendar_data:
            calendar_data[habit_id] = []

        calendar_data[habit_id].append(completed_date)

    conn.close()

    return render_template('partner_habits.html',
                          habits=habits,
                          calendar_data=calendar_data,
                          today=date.today().strftime('%Y-%m-%d'),
                          current_user=get_current_user(),
                          partner=get_partner())

# Debug route
@app.route('/debug')
@login_required
def debug():
    user_id = session['user_id']
    conn = get_db_connection()

    # Get all data for the current user
    goals = conn.execute('SELECT * FROM goals WHERE user_id = ? ORDER BY priority', (user_id,)).fetchall()
    routines = conn.execute('SELECT * FROM routines WHERE user_id = ? ORDER BY time_block', (user_id,)).fetchall()
    habits = conn.execute('''
        SELECT h.*, g.description as goal_description
        FROM habits h
        LEFT JOIN goals g ON h.goal_id = g.id
        WHERE h.user_id = ?
        ORDER BY h.name
    ''', (user_id,)).fetchall()

    conn.close()

    return render_template('debug.html', goals=goals, routines=routines, habits=habits,
                          current_user=get_current_user(), partner=get_partner())

# AI Roadmap routes
@app.route('/ai_roadmap')
@login_required
def ai_roadmap():
    user_id = session['user_id']
    conn = get_db_connection()

    # Get saved roadmaps
    roadmaps = conn.execute('SELECT * FROM ai_roadmaps WHERE user_id = ? ORDER BY created_at DESC', (user_id,)).fetchall()

    # Get conversation history
    helper = get_ai_helper()
    conversation_history = helper.get_conversation_history(user_id)

    conn.close()

    return render_template('ai_roadmap.html',
                          roadmaps=roadmaps,
                          conversation_history=conversation_history,
                          current_user=get_current_user(),
                          partner=get_partner())

@app.route('/ai_roadmap/chat', methods=['POST'])
@login_required
def ai_roadmap_chat():
    user_id = session['user_id']
    user_message = request.form['message']

    # Get AI response
    helper = get_ai_helper()
    ai_response = helper.generate_response(user_message)

    # Save conversation
    helper.save_conversation(user_id, user_message, ai_response)

    return jsonify({
        'response': ai_response
    })

@app.route('/ai_roadmap/save', methods=['POST'])
@login_required
def save_roadmap():
    user_id = session['user_id']
    title = request.form['title']
    content = request.form['content']

    conn = get_db_connection()
    conn.execute('INSERT INTO ai_roadmaps (user_id, title, content, created_at) VALUES (?, ?, ?, ?)',
                (user_id, title, content, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

    flash('Roadmap saved successfully!')
    return redirect(url_for('ai_roadmap'))

@app.route('/ai_roadmap/view/<int:id>')
@login_required
def view_roadmap(id):
    user_id = session['user_id']
    conn = get_db_connection()
    roadmap = conn.execute('SELECT * FROM ai_roadmaps WHERE id = ? AND user_id = ?', (id, user_id)).fetchone()

    if not roadmap:
        flash('Roadmap not found or you do not have permission to view it')
        conn.close()
        return redirect(url_for('ai_roadmap'))

    conn.close()

    return render_template('view_roadmap.html',
                          roadmap=roadmap,
                          current_user=get_current_user(),
                          partner=get_partner())

@app.route('/ai_roadmap/delete/<int:id>', methods=['POST'])
@login_required
def delete_roadmap(id):
    user_id = session['user_id']
    conn = get_db_connection()

    # Verify the roadmap belongs to the current user
    roadmap = conn.execute('SELECT * FROM ai_roadmaps WHERE id = ? AND user_id = ?', (id, user_id)).fetchone()
    if not roadmap:
        flash('Roadmap not found or you do not have permission to delete it')
        conn.close()
        return redirect(url_for('ai_roadmap'))

    # Delete the roadmap
    conn.execute('DELETE FROM ai_roadmaps WHERE id = ? AND user_id = ?', (id, user_id))

    conn.commit()
    conn.close()

    flash('Roadmap deleted successfully!')
    return redirect(url_for('ai_roadmap'))

@app.route('/ai_roadmap/save_goals', methods=['POST'])
@login_required
def save_extracted_goals():
    user_id = session['user_id']
    goals_json = request.form.get('goals', '[]')

    try:
        goals = json.loads(goals_json)

        if not goals:
            flash('No goals selected to save')
            return redirect(request.referrer or url_for('ai_roadmap'))

        conn = get_db_connection()

        # Save each goal
        for goal in goals:
            # Determine a default category based on the goal content
            category = 'Personal Development'  # Default category
            if any(kw in goal.lower() for kw in ['health', 'exercise', 'fitness', 'diet', 'nutrition', 'weight']):
                category = 'Physical Fitness'
            elif any(kw in goal.lower() for kw in ['career', 'job', 'work', 'professional', 'business']):
                category = 'Career'
            elif any(kw in goal.lower() for kw in ['learn', 'study', 'education', 'knowledge', 'skill']):
                category = 'Learning'
            elif any(kw in goal.lower() for kw in ['family', 'friend', 'relationship', 'social']):
                category = 'Relationships'
            elif any(kw in goal.lower() for kw in ['finance', 'money', 'saving', 'budget', 'invest']):
                category = 'Financial'

            # Set a default deadline of 3 months from now
            deadline = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')

            # Set a medium priority by default
            priority = 2

            conn.execute('INSERT INTO goals (user_id, category, description, deadline, priority, status) VALUES (?, ?, ?, ?, ?, ?)',
                        (user_id, category, goal, deadline, priority, 'active'))

        conn.commit()
        conn.close()

        flash(f'Successfully added {len(goals)} goals to your account!')
        return redirect(url_for('view_goals'))

    except json.JSONDecodeError:
        flash('Error processing goals data')
        return redirect(request.referrer or url_for('ai_roadmap'))

@app.route('/ai_roadmap/save_habits', methods=['POST'])
@login_required
def save_extracted_habits():
    user_id = session['user_id']
    habits_json = request.form.get('habits', '[]')

    try:
        habits = json.loads(habits_json)

        if not habits:
            flash('No habits selected to save')
            return redirect(request.referrer or url_for('ai_roadmap'))

        conn = get_db_connection()

        # Get user's active goals for potential linking
        goals = conn.execute('SELECT id, description FROM goals WHERE user_id = ? AND status = "active"',
                           (user_id,)).fetchall()

        # Save each habit
        for habit in habits:
            # Try to find a related goal
            related_goal_id = None
            for goal in goals:
                # Simple matching - check if any significant words from the habit appear in the goal
                habit_words = set(w.lower() for w in habit.split() if len(w) > 3)
                goal_words = set(w.lower() for w in goal[1].split() if len(w) > 3)

                if habit_words.intersection(goal_words):
                    related_goal_id = goal[0]
                    break

            # Default frequency
            frequency = 'daily'

            conn.execute('INSERT INTO habits (user_id, name, goal_id, frequency, streak, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                        (user_id, habit, related_goal_id, frequency, 0, datetime.now().strftime('%Y-%m-%d')))

        conn.commit()
        conn.close()

        flash(f'Successfully added {len(habits)} habits to your account!')
        return redirect(url_for('view_habits'))

    except json.JSONDecodeError:
        flash('Error processing habits data')
        return redirect(request.referrer or url_for('ai_roadmap'))

@app.route('/ai_roadmap/save_routines', methods=['POST'])
@login_required
def save_extracted_routines():
    user_id = session['user_id']
    routines_json = request.form.get('routines', '[]')

    try:
        routines = json.loads(routines_json)

        if not routines:
            flash('No routines selected to save')
            return redirect(request.referrer or url_for('ai_roadmap'))

        conn = get_db_connection()

        # Save each routine
        for routine in routines:
            # Try to extract time information from the routine description
            time_block = 'Morning'  # Default
            if any(kw in routine.lower() for kw in ['morning', 'am', 'breakfast', 'wake']):
                time_block = 'Morning'
            elif any(kw in routine.lower() for kw in ['noon', 'lunch', 'midday']):
                time_block = 'Midday'
            elif any(kw in routine.lower() for kw in ['afternoon', 'evening', 'pm']):
                time_block = 'Afternoon'
            elif any(kw in routine.lower() for kw in ['night', 'bedtime', 'sleep']):
                time_block = 'Evening'

            # Default duration of 30 minutes
            duration = 30

            # Default energy level
            energy_level = 'Medium'

            # Default to all weekdays
            weekdays = 'Monday,Tuesday,Wednesday,Thursday,Friday'

            conn.execute('INSERT INTO routines (user_id, time_block, activity, duration, energy_level, weekdays) VALUES (?, ?, ?, ?, ?, ?)',
                        (user_id, time_block, routine, duration, energy_level, weekdays))

        conn.commit()
        conn.close()

        flash(f'Successfully added {len(routines)} routines to your account!')
        return redirect(url_for('view_routines'))

    except json.JSONDecodeError:
        flash('Error processing routines data')
        return redirect(request.referrer or url_for('ai_roadmap'))

# Gamification routes
@app.route('/achievements')
@login_required
def view_achievements():
    user_id = session['user_id']
    helper = get_gamification_helper()

    # Check for new achievements
    new_achievements = helper.check_achievements(user_id)

    # Get all achievements
    achievements = helper.get_user_achievements(user_id)

    # Get user level info
    level_info = helper.get_user_level_info(user_id)

    return render_template('achievements.html',
                          achievements=achievements,
                          level_info=level_info,
                          new_achievements=new_achievements,
                          current_user=get_current_user(),
                          partner=get_partner())

@app.route('/challenges')
@login_required
def view_challenges():
    user_id = session['user_id']
    helper = get_gamification_helper()

    # Get active challenges
    active_challenges = helper.get_active_challenges(user_id)

    # Get completed challenges
    conn = get_db_connection()
    completed_challenges = conn.execute('''
        SELECT c.*, uc.completed_at
        FROM challenges c
        JOIN user_challenges uc ON c.id = uc.challenge_id
        WHERE uc.user_id = ? AND uc.status = 'completed'
        ORDER BY uc.completed_at DESC
    ''', (user_id,)).fetchall()
    conn.close()

    return render_template('challenges.html',
                          active_challenges=active_challenges,
                          completed_challenges=completed_challenges,
                          current_user=get_current_user(),
                          partner=get_partner())

@app.route('/challenges/update', methods=['POST'])
@login_required
def update_challenge_progress():
    user_id = session['user_id']
    challenge_id = request.form.get('challenge_id')
    progress = int(request.form.get('progress', 0))

    if not challenge_id:
        flash('Challenge ID is required')
        return redirect(url_for('view_challenges'))

    # Validate progress
    if progress < 0:
        progress = 0
    elif progress > 100:
        progress = 100

    helper = get_gamification_helper()
    helper.update_challenge_progress(user_id, challenge_id, progress)

    flash('Challenge progress updated!')
    return redirect(url_for('view_challenges'))

@app.route('/check_achievements')
@login_required
def check_achievements():
    user_id = session['user_id']
    helper = get_gamification_helper()

    # Check for new achievements
    new_achievements = helper.check_achievements(user_id)

    return jsonify({
        'new_achievements': [dict(a) for a in new_achievements]
    })

# Award XP for completing habits
@app.route('/habits/log/<int:id>', methods=['POST'])
@login_required
def log_habit(id):
    user_id = session['user_id']
    completed = request.form.get('completed', 'false') == 'true'
    today = date.today().strftime('%Y-%m-%d')
    notes = request.form.get('notes', '')

    conn = get_db_connection()

    # Verify the habit belongs to the current user
    habit = conn.execute('SELECT * FROM habits WHERE id = ? AND user_id = ?', (id, user_id)).fetchone()
    if not habit:
        flash('Habit not found or you do not have permission to log it')
        conn.close()
        return redirect(request.referrer or url_for('index'))

    # Check if already logged today
    existing = conn.execute('SELECT id FROM habit_logs WHERE habit_id = ? AND completed_date = ?',
                        (id, today)).fetchone()

    # Get the current streak (at index 5, not 4)
    current_streak = habit[5]  # Current streak
    new_streak = int(current_streak)  # Ensure it's an integer

    # Get gamification helper
    helper = get_gamification_helper()

    if completed:
        if not existing:
            # Add log
            conn.execute('INSERT INTO habit_logs (habit_id, completed_date, notes) VALUES (?, ?, ?)',
                        (id, today, notes))

            # Update streak
            new_streak = int(current_streak) + 1
            conn.execute('UPDATE habits SET streak = ? WHERE id = ?', (new_streak, id))

            # Award XP for completing a habit (10 XP per completion)
            helper.award_xp(conn, user_id, 10, 'habit_completion', id, f"Completed habit: {habit[2]}")

            # Check for streak milestones and award bonus XP
            if new_streak in [7, 30, 66, 100]:
                bonus_xp = new_streak  # XP equal to streak milestone
                helper.award_xp(conn, user_id, bonus_xp, 'streak_milestone', id,
                               f"Reached {new_streak}-day streak for habit: {habit[2]}")

            conn.commit()
            if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                flash('Habit marked as completed!')
    else:
        if existing:
            # Remove log
            conn.execute('DELETE FROM habit_logs WHERE habit_id = ? AND completed_date = ?',
                        (id, today))

            # Update streak (not reset to 0, just decrement)
            if int(current_streak) > 0:
                new_streak = int(current_streak) - 1
                conn.execute('UPDATE habits SET streak = ? WHERE id = ?', (new_streak, id))

            conn.commit()
            if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                flash('Habit completion removed!')

    # Check for new achievements
    new_achievements = helper.check_achievements(user_id)

    # Get user level info to check for level up
    level_info = helper.get_user_level_info(user_id)

    conn.close()

    # Check for milestone
    milestone = None
    if completed and not existing and new_streak in [7, 30, 66, 100]:
        milestone = {
            'type': 'streak',
            'message': f"You've reached a {new_streak}-day streak!",
            'description': "Consistency is key to building lasting habits. Keep up the great work!",
            'value': new_streak,
            'label': 'Day Streak',
            'habit_name': habit[2]
        }

    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
        return jsonify({
            'success': True,
            'completed': completed,
            'new_streak': new_streak,
            'new_achievements': [dict(a) for a in new_achievements],
            'level_info': level_info,
            'milestone': milestone
        })

    return redirect(request.referrer or url_for('index'))

# Mood tracking routes
@app.route('/mood/log', methods=['POST'])
@login_required
def log_mood():
    user_id = session['user_id']
    mood_score = int(request.form.get('mood_score', 3))
    energy_level = int(request.form.get('energy_level', 5))
    mood_note = request.form.get('mood_note', '')

    # Validate mood score
    if mood_score < 1:
        mood_score = 1
    elif mood_score > 5:
        mood_score = 5

    # Validate energy level
    if energy_level < 1:
        energy_level = 1
    elif energy_level > 10:
        energy_level = 10

    conn = get_db_connection()

    # Check if already logged today
    today = datetime.now().strftime('%Y-%m-%d')
    existing = conn.execute('''
        SELECT id FROM mood_logs
        WHERE user_id = ? AND date(logged_at) = ?
    ''', (user_id, today)).fetchone()

    if existing:
        # Update existing entry
        conn.execute('''
            UPDATE mood_logs
            SET mood_score = ?, mood_note = ?, energy_level = ?, logged_at = ?
            WHERE id = ?
        ''', (mood_score, mood_note, energy_level, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), existing[0]))
        message = "Mood updated for today!"
    else:
        # Create new entry
        conn.execute('''
            INSERT INTO mood_logs (user_id, mood_score, mood_note, energy_level, logged_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, mood_score, mood_note, energy_level, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        message = "Mood logged successfully!"

    conn.commit()
    conn.close()

    flash(message)
    return redirect(request.referrer or url_for('index'))

@app.route('/mood/history')
@login_required
def mood_history():
    user_id = session['user_id']
    conn = get_db_connection()

    # Get mood history for the last 30 days
    mood_history = conn.execute('''
        SELECT mood_score, mood_note, energy_level, logged_at
        FROM mood_logs
        WHERE user_id = ?
        ORDER BY logged_at DESC
        LIMIT 30
    ''', (user_id,)).fetchall()

    conn.close()

    # Format the data for the template
    formatted_history = []
    for entry in mood_history:
        formatted_history.append({
            'mood_score': entry[0],
            'mood_note': entry[1],
            'energy_level': entry[2],
            'logged_at': datetime.strptime(entry[3], '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y')
        })

    return render_template('mood_history.html',
                          mood_history=formatted_history,
                          current_user=get_current_user(),
                          partner=get_partner())

@app.route('/weekly_summary')
@login_required
def weekly_summary():
    user_id = session['user_id']
    conn = get_db_connection()

    # Calculate date range for the past week
    end_date = date.today()
    start_date = end_date - timedelta(days=7)

    # Format dates for display
    start_date_str = start_date.strftime('%b %d, %Y')
    end_date_str = end_date.strftime('%b %d, %Y')

    # Get habit completion rate for the week
    total_habits = conn.execute('''
        SELECT COUNT(*) FROM habits WHERE user_id = ?
    ''', (user_id,)).fetchone()[0]

    completed_habits = conn.execute('''
        SELECT COUNT(DISTINCT habit_id) FROM habit_logs
        WHERE habit_id IN (SELECT id FROM habits WHERE user_id = ?)
        AND completed_date BETWEEN ? AND ?
    ''', (user_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))).fetchone()[0]

    habit_completion_rate = round((completed_habits / total_habits * 100) if total_habits > 0 else 0)

    # Get XP earned this week
    xp_earned = conn.execute('''
        SELECT SUM(amount) FROM xp_transactions
        WHERE user_id = ? AND created_at BETWEEN ? AND ?
    ''', (user_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))).fetchone()[0] or 0

    # Get focus minutes for the week
    focus_minutes = conn.execute('''
        SELECT SUM(duration) FROM routines
        WHERE user_id = ? AND energy_level = 'High'
    ''', (user_id,)).fetchone()[0] or 0

    # Get top habits by streak
    top_habits = conn.execute('''
        SELECT name, streak FROM habits
        WHERE user_id = ?
        ORDER BY streak DESC
        LIMIT 5
    ''', (user_id,)).fetchall()

    formatted_top_habits = []
    for habit in top_habits:
        formatted_top_habits.append({
            'name': habit[0],
            'streak': habit[1]
        })

    # Get mood data
    mood_data = conn.execute('''
        SELECT mood_score, energy_level, logged_at
        FROM mood_logs
        WHERE user_id = ? AND logged_at BETWEEN ? AND ?
        ORDER BY logged_at
    ''', (user_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))).fetchall()

    # Calculate average mood
    avg_mood = 0
    highest_energy_day = "N/A"
    highest_energy = 0

    if mood_data:
        total_mood = sum(entry[0] for entry in mood_data)
        avg_mood = round(total_mood / len(mood_data), 1)

        # Find day with highest energy
        for entry in mood_data:
            if entry[1] > highest_energy:
                highest_energy = entry[1]
                highest_energy_day = datetime.strptime(entry[2], '%Y-%m-%d %H:%M:%S').strftime('%A')

    # Map average mood to text
    mood_text_map = {
        1: "Bad",
        2: "Low",
        3: "Okay",
        4: "Good",
        5: "Great"
    }
    avg_mood_text = mood_text_map.get(round(avg_mood)) if avg_mood > 0 else "N/A"

    # Get achievements unlocked this week
    achievements = conn.execute('''
        SELECT a.name, a.description
        FROM achievements a
        JOIN user_achievements ua ON a.id = ua.achievement_id
        WHERE ua.user_id = ? AND ua.unlocked_at BETWEEN ? AND ?
    ''', (user_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))).fetchall()

    formatted_achievements = []
    for achievement in achievements:
        formatted_achievements.append({
            'name': achievement[0],
            'description': achievement[1]
        })

    # Generate focus areas for next week
    focus_areas = []

    # If habit completion rate is low, suggest focusing on consistency
    if habit_completion_rate < 70:
        focus_areas.append("Improve habit consistency - try to complete more of your daily habits")

    # If no mood logs, suggest tracking mood
    if not mood_data:
        focus_areas.append("Start tracking your mood daily to better understand your emotional patterns")

    # If no achievements, suggest working towards one
    if not achievements:
        focus_areas.append("Work towards unlocking a new achievement")

    # Always add a positive suggestion
    focus_areas.append("Celebrate your progress and reflect on what's working well")

    conn.close()

    # Dashboard URL for the email
    dashboard_url = request.url_root

    return render_template('weekly_summary.html',
                          start_date=start_date_str,
                          end_date=end_date_str,
                          habit_completion_rate=habit_completion_rate,
                          xp_earned=xp_earned,
                          focus_minutes=focus_minutes,
                          top_habits=formatted_top_habits,
                          avg_mood_text=avg_mood_text,
                          highest_energy_day=highest_energy_day,
                          achievements=formatted_achievements,
                          focus_areas=focus_areas,
                          dashboard_url=dashboard_url)

# AI Insights routes
@app.route('/ai_insights')
@login_required
def ai_insights_dashboard():
    """Render the AI Insights Dashboard."""
    return render_template('ai_insights_dashboard.html',
                          current_user=get_current_user(),
                          partner=get_partner())

@app.route('/get_ai_insights')
@login_required
def get_ai_insights():
    user_id = session['user_id']
    helper = get_ai_insights_helper()

    # Get insights
    insights = helper.get_insights(user_id)

    return jsonify({
        'insights': insights
    })

@app.route('/ai_habit_motivation/<int:habit_id>')
@login_required
def ai_habit_motivation(habit_id):
    user_id = session['user_id']
    conn = get_db_connection()

    # Get habit details
    habit = conn.execute('SELECT * FROM habits WHERE id = ? AND user_id = ?', (habit_id, user_id)).fetchone()

    if not habit:
        flash('Habit not found or you do not have permission to view it')
        conn.close()
        return redirect(url_for('view_habits'))

    # Get goal if linked
    goal = None
    if habit[3]:  # goal_id
        goal = conn.execute('SELECT description FROM goals WHERE id = ?', (habit[3],)).fetchone()

    conn.close()

    # Generate motivation content
    helper = get_ai_helper()
    prompt = f"""Generate motivational content to help the user maintain their habit of "{habit[2]}".

    {f'This habit is linked to their goal: "{goal[0]}".' if goal else 'This habit is not linked to any specific goal.'}

    The user has a current streak of {habit[5]} days.

    Provide:
    1. A brief motivational message (2-3 sentences)
    2. Three specific tips to maintain this habit
    3. A relevant quote about consistency or habit formation

    Format your response in a conversational, encouraging tone."""

    motivation = helper.generate_response(prompt)

    return render_template('ai_habit_motivation.html',
                          habit=habit,
                          goal=goal,
                          motivation=motivation,
                          current_user=get_current_user(),
                          partner=get_partner())

@app.route('/ai_suggest_habits/<int:goal_id>')
@login_required
def ai_suggest_habits(goal_id):
    user_id = session['user_id']
    conn = get_db_connection()

    # Get goal details
    goal = conn.execute('SELECT * FROM goals WHERE id = ? AND user_id = ?', (goal_id, user_id)).fetchone()

    if not goal:
        flash('Goal not found or you do not have permission to view it')
        conn.close()
        return redirect(url_for('view_goals'))

    conn.close()

    # Generate habit suggestions
    helper = get_ai_insights_helper()
    suggestions = helper.generate_ai_habit_suggestions(goal_id)

    return render_template('ai_habit_suggestions.html',
                          goal=goal,
                          suggestions=suggestions,
                          current_user=get_current_user(),
                          partner=get_partner())

@app.route('/ai_energy_optimization')
@login_required
def ai_energy_optimization():
    user_id = session['user_id']

    # Generate energy optimization
    helper = get_ai_insights_helper()
    optimization = helper.generate_energy_optimization(user_id)

    return render_template('ai_energy_optimization.html',
                          optimization=optimization,
                          current_user=get_current_user(),
                          partner=get_partner())

@app.route('/ai_mood_suggestions')
@login_required
def ai_mood_suggestions():
    user_id = session['user_id']
    conn = get_db_connection()

    # Get recent mood data
    mood_data = conn.execute('''
        SELECT mood_score, energy_level, mood_note, logged_at
        FROM mood_logs
        WHERE user_id = ?
        ORDER BY logged_at DESC
        LIMIT 7
    ''', (user_id,)).fetchall()

    conn.close()

    # Format mood data for the AI
    formatted_mood = []
    for entry in mood_data:
        formatted_mood.append({
            'mood_score': entry[0],
            'energy_level': entry[1],
            'note': entry[2],
            'date': datetime.strptime(entry[3], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
        })

    # Generate mood suggestions
    helper = get_ai_helper()
    prompt = f"""Based on the user's recent mood data, provide personalized suggestions to improve their wellbeing.

Mood data (1=lowest, 5=highest; most recent first):
{json.dumps(formatted_mood, indent=2)}

Provide:
1. A brief analysis of their mood patterns
2. Three specific, actionable suggestions to improve their wellbeing
3. One mindfulness or self-care exercise they could try today

Format your response in a supportive, empathetic tone."""

    suggestions = helper.generate_response(prompt)

    return render_template('ai_mood_suggestions.html',
                          mood_data=mood_data,
                          suggestions=suggestions,
                          now=datetime.now(),
                          current_user=get_current_user(),
                          partner=get_partner())

# AI Notification routes
@app.route('/ai/notifications/list')
@login_required
def list_notifications():
    user_id = session['user_id']
    helper = get_ai_notification_helper()

    # Get notifications
    include_read = request.args.get('include_read', 'false') == 'true'
    limit = int(request.args.get('limit', 20))

    notifications = helper.get_user_notifications(user_id, limit, include_read)

    return jsonify({
        'notifications': notifications
    })

@app.route('/ai/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    user_id = session['user_id']
    helper = get_ai_notification_helper()

    success = helper.mark_notification_read(notification_id, user_id)

    return jsonify({
        'success': success
    })

@app.route('/ai/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    user_id = session['user_id']
    helper = get_ai_notification_helper()

    success = helper.mark_all_notifications_read(user_id)

    return jsonify({
        'success': success
    })

@app.route('/ai/notifications/<int:notification_id>/snooze', methods=['POST'])
@login_required
def snooze_notification(notification_id):
    user_id = session['user_id']
    helper = get_ai_notification_helper()

    hours = request.json.get('hours', 3) if request.is_json else 3

    success = helper.snooze_notification(notification_id, user_id, hours)

    return jsonify({
        'success': success
    })

@app.route('/ai/notifications/<int:notification_id>/action', methods=['POST'])
@login_required
def notification_action(notification_id):
    user_id = session['user_id']
    helper = get_ai_notification_helper()

    if not request.is_json:
        return jsonify({'success': False, 'error': 'Invalid request format'})

    action = request.json.get('action')

    if action == 'dismiss':
        success = helper.mark_notification_read(notification_id, user_id)
    elif action == 'delete':
        success = helper.delete_notification(notification_id, user_id)
    elif action == 'complete_habit':
        # Get the habit ID from the notification metadata
        conn = get_db_connection()
        notification = conn.execute('SELECT metadata FROM ai_notifications WHERE id = ? AND user_id = ?',
                                  (notification_id, user_id)).fetchone()
        conn.close()

        if notification and notification['metadata']:
            try:
                metadata = json.loads(notification['metadata'])
                habit_id = metadata.get('habit_id')

                if habit_id:
                    # Log the habit as completed
                    conn = get_db_connection()
                    today = date.today().strftime('%Y-%m-%d')

                    # Check if already completed today
                    existing = conn.execute('SELECT id FROM habit_logs WHERE habit_id = ? AND completed_date = ?',
                                          (habit_id, today)).fetchone()

                    if not existing:
                        conn.execute('INSERT INTO habit_logs (habit_id, completed_date) VALUES (?, ?)',
                                    (habit_id, today))

                        # Update streak
                        habit = conn.execute('SELECT streak FROM habits WHERE id = ?', (habit_id,)).fetchone()
                        new_streak = habit['streak'] + 1
                        conn.execute('UPDATE habits SET streak = ? WHERE id = ?', (new_streak, habit_id))

                        conn.commit()

                    conn.close()
                    success = True
                else:
                    success = False
            except json.JSONDecodeError:
                success = False
        else:
            success = False
    elif action == 'extend_deadline':
        # Get the goal ID from the notification metadata
        conn = get_db_connection()
        notification = conn.execute('SELECT metadata FROM ai_notifications WHERE id = ? AND user_id = ?',
                                  (notification_id, user_id)).fetchone()

        if notification and notification['metadata']:
            try:
                metadata = json.loads(notification['metadata'])
                goal_id = metadata.get('goal_id')

                if goal_id:
                    # Extend deadline by 7 days
                    goal = conn.execute('SELECT deadline FROM goals WHERE id = ? AND user_id = ?',
                                      (goal_id, user_id)).fetchone()

                    if goal and goal['deadline']:
                        current_deadline = datetime.strptime(goal['deadline'], '%Y-%m-%d')
                        new_deadline = (current_deadline + timedelta(days=7)).strftime('%Y-%m-%d')

                        conn.execute('UPDATE goals SET deadline = ? WHERE id = ?', (new_deadline, goal_id))
                        conn.commit()
                        success = True
                    else:
                        success = False
                else:
                    success = False
            except json.JSONDecodeError:
                success = False
        else:
            success = False

        conn.close()
    else:
        # Generic action handling
        success = helper.mark_notification_read(notification_id, user_id)

    return jsonify({
        'success': success
    })

@app.route('/ai/notifications/settings', methods=['GET', 'POST'])
@login_required
def notification_settings():
    user_id = session['user_id']
    helper = get_ai_notification_helper()

    if request.method == 'POST':
        settings = {
            'insights_enabled': request.form.get('insights_enabled') == 'on',
            'suggestions_enabled': request.form.get('suggestions_enabled') == 'on',
            'alerts_enabled': request.form.get('alerts_enabled') == 'on',
            'reminders_enabled': request.form.get('reminders_enabled') == 'on',
            'email_notifications': request.form.get('email_notifications') == 'on',
            'push_notifications': request.form.get('push_notifications') == 'on',
            'quiet_hours_start': request.form.get('quiet_hours_start'),
            'quiet_hours_end': request.form.get('quiet_hours_end')
        }

        success = helper.update_user_notification_settings(user_id, settings)

        if success:
            flash('Notification settings updated successfully')
        else:
            flash('Error updating notification settings')

        return redirect(url_for('notification_settings'))

    # Get current settings
    settings = helper.get_user_notification_settings(user_id)

    return render_template('ai_notification_settings.html',
                          settings=settings,
                          current_user=get_current_user(),
                          partner=get_partner())

@app.route('/ai/notifications')
@login_required
def view_notifications():
    user_id = session['user_id']
    helper = get_ai_notification_helper()

    # Get notifications
    notifications = helper.get_user_notifications(user_id, 50, True)

    # Check for new notifications
    helper.check_notification_triggers(user_id)

    return render_template('ai_notifications.html',
                          notifications=notifications,
                          current_user=get_current_user(),
                          partner=get_partner())

@app.route('/check_notifications')
@login_required
def check_notifications():
    user_id = session['user_id']
    helper = get_ai_notification_helper()

    # Check for new notifications
    new_notification_ids = helper.check_notification_triggers(user_id)

    # Get the new notifications
    new_notifications = []
    if new_notification_ids:
        conn = get_db_connection()
        for notification_id in new_notification_ids:
            notification = conn.execute('SELECT * FROM ai_notifications WHERE id = ?', (notification_id,)).fetchone()
            if notification:
                notification_dict = dict(notification)

                # Parse actions JSON
                if notification_dict['actions']:
                    try:
                        notification_dict['actions'] = json.loads(notification_dict['actions'])
                    except json.JSONDecodeError:
                        notification_dict['actions'] = []
                else:
                    notification_dict['actions'] = []

                new_notifications.append(notification_dict)
        conn.close()

    return jsonify({
        'new_notifications': new_notifications
    })

# Push Notification API routes
@app.route('/api/push-public-key')
@login_required
def get_push_public_key():
    """Get the public key for push notifications."""
    # In a real implementation, this would be a proper VAPID public key
    # For now, we'll use a placeholder
    return jsonify({
        'publicKey': 'BLc4xRzKlKORovVrI_ij68zPnzUKOJrY-Ii2lCW2PrZpLOTd8sJRnqNvCwyBb-wSaS7pFKXJib2Dj_Qxp6Y3VdM'
    })

@app.route('/api/push-subscribe', methods=['POST'])
@login_required
def push_subscribe():
    """Subscribe to push notifications."""
    user_id = session['user_id']

    if not request.is_json:
        return jsonify({'success': False, 'error': 'Invalid request format'}), 400

    subscription = request.json.get('subscription')
    if not subscription:
        return jsonify({'success': False, 'error': 'Missing subscription data'}), 400

    # Save subscription to database
    conn = get_db_connection()

    try:
        # Check if subscription already exists
        existing = conn.execute('''
            SELECT id FROM push_notification_subscriptions
            WHERE user_id = ? AND endpoint = ?
        ''', (user_id, subscription.get('endpoint'))).fetchone()

        if existing:
            # Update existing subscription
            conn.execute('''
                UPDATE push_notification_subscriptions
                SET p256dh = ?, auth = ?, updated_at = ?
                WHERE user_id = ? AND endpoint = ?
            ''', (
                subscription.get('keys', {}).get('p256dh', ''),
                subscription.get('keys', {}).get('auth', ''),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                user_id,
                subscription.get('endpoint')
            ))
        else:
            # Create new subscription
            conn.execute('''
                INSERT INTO push_notification_subscriptions
                (user_id, endpoint, p256dh, auth, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id,
                subscription.get('endpoint', ''),
                subscription.get('keys', {}).get('p256dh', ''),
                subscription.get('keys', {}).get('auth', ''),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))

        # Update user settings to enable push notifications
        helper = get_ai_notification_helper()
        settings = helper.get_user_notification_settings(user_id)
        settings['push_notifications'] = True
        helper.update_user_notification_settings(user_id, settings)

        conn.commit()

        return jsonify({'success': True})

    except Exception as e:
        print(f"Error subscribing to push notifications: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

    finally:
        conn.close()

@app.route('/api/push-unsubscribe', methods=['POST'])
@login_required
def push_unsubscribe():
    """Unsubscribe from push notifications."""
    user_id = session['user_id']

    if not request.is_json:
        return jsonify({'success': False, 'error': 'Invalid request format'}), 400

    subscription = request.json.get('subscription')
    if not subscription:
        return jsonify({'success': False, 'error': 'Missing subscription data'}), 400

    # Remove subscription from database
    conn = get_db_connection()

    try:
        conn.execute('''
            DELETE FROM push_notification_subscriptions
            WHERE user_id = ? AND endpoint = ?
        ''', (user_id, subscription.get('endpoint')))

        # Update user settings to disable push notifications if no subscriptions remain
        remaining = conn.execute('''
            SELECT COUNT(*) as count FROM push_notification_subscriptions
            WHERE user_id = ?
        ''', (user_id,)).fetchone()[0]

        if remaining == 0:
            helper = get_ai_notification_helper()
            settings = helper.get_user_notification_settings(user_id)
            settings['push_notifications'] = False
            helper.update_user_notification_settings(user_id, settings)

        conn.commit()

        return jsonify({'success': True})

    except Exception as e:
        print(f"Error unsubscribing from push notifications: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)