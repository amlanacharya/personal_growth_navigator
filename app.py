# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, g
import sqlite3
import os
import json
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from ai_helper import AIHelper, create_env_file

app = Flask(__name__)
app.secret_key = "personal_growth_navigator_secret_key"

# Create .env file if it doesn't exist
create_env_file()

# Initialize AI Helper
ai_helper = None

def get_ai_helper():
    global ai_helper
    if ai_helper is None:
        ai_helper = AIHelper()
    return ai_helper

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

    conn.close()

    return render_template('index.html', goals=goals, routines=routines, habits=habits,
                          today=date.today().strftime('%Y-%m-%d'),
                          current_user=get_current_user(),
                          partner=get_partner(),
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

    if completed:
        if not existing:
            # Add log
            conn.execute('INSERT INTO habit_logs (habit_id, completed_date, notes) VALUES (?, ?, ?)',
                        (id, today, notes))

            # Update streak
            new_streak = int(current_streak) + 1
            conn.execute('UPDATE habits SET streak = ? WHERE id = ?', (new_streak, id))

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

    conn.close()

    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
        return jsonify({
            'success': True,
            'completed': completed,
            'new_streak': new_streak
        })

    return redirect(request.referrer or url_for('index'))

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

if __name__ == '__main__':
    app.run(debug=True)