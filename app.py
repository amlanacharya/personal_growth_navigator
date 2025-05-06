# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import os
import json
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = "personal_growth_navigator_secret_key"

# Database setup
def get_db_connection():
    if not os.path.exists('growth_navigator.db'):
        conn = sqlite3.connect('growth_navigator.db')
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            deadline TEXT,
            priority INTEGER,
            status TEXT DEFAULT 'active'
        )
        ''')
        cursor.execute('''
        CREATE TABLE routines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time_block TEXT NOT NULL,
            activity TEXT NOT NULL,
            duration INTEGER,
            energy_level TEXT,
            weekdays TEXT
        )
        ''')
        cursor.execute('''
        CREATE TABLE habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            goal_id INTEGER,
            frequency TEXT,
            streak INTEGER DEFAULT 0,
            created_at TEXT,
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

        # Insert initial data
        cursor.execute('''
        INSERT INTO goals (category, description, deadline, priority, status)
        VALUES
        ('Physical Fitness', 'Join gym and exercise regularly to keep body fit', '2025-06-01', 1, 'active'),
        ('Professional Development', 'Get very good at data science oriented roles and skill building', '2025-08-01', 2, 'active'),
        ('Professional Development', 'Master new codebase at job', '2025-07-01', 3, 'active')
        ''')

        # Insert initial routine
        cursor.execute('''
        INSERT INTO routines (time_block, activity, duration, energy_level, weekdays)
        VALUES
        ('6:45 AM', 'Wake up', 15, 'Medium', 'Monday,Tuesday,Wednesday,Thursday,Friday'),
        ('7:00 AM - 7:30 AM', 'Quick morning workout', 30, 'Medium', 'Monday,Tuesday,Wednesday,Thursday,Friday'),
        ('7:30 AM - 8:00 AM', 'Breakfast + preparation', 30, 'Medium', 'Monday,Tuesday,Wednesday,Thursday,Friday'),
        ('8:00 AM - 10:00 AM', 'Deep Work: Codebase learning', 120, 'High', 'Monday,Tuesday,Wednesday,Thursday,Friday'),
        ('10:00 AM - 11:00 AM', 'Team meetings/collaboration', 60, 'Medium', 'Monday,Tuesday,Wednesday,Thursday,Friday'),
        ('11:00 AM - 11:30 AM', 'Walk/movement break', 30, 'Low', 'Monday,Tuesday,Wednesday,Thursday,Friday'),
        ('11:30 AM - 1:00 PM', 'Lighter work tasks', 90, 'Low', 'Monday,Tuesday,Wednesday,Thursday,Friday'),
        ('1:00 PM - 1:45 PM', 'Lunch break', 45, 'Low', 'Monday,Tuesday,Wednesday,Thursday,Friday'),
        ('1:45 PM - 4:30 PM', 'Mixed work tasks', 165, 'Medium', 'Monday,Tuesday,Wednesday,Thursday,Friday'),
        ('4:30 PM - 5:30 PM', 'Admin work/planning', 60, 'Medium', 'Monday,Tuesday,Wednesday,Thursday,Friday'),
        ('5:30 PM - 7:00 PM', 'Data Science learning', 90, 'High', 'Monday,Tuesday,Wednesday,Thursday,Friday'),
        ('7:00 PM - 8:00 PM', 'Exercise', 60, 'Medium', 'Monday,Tuesday,Wednesday,Thursday,Friday'),
        ('8:00 PM - 9:00 PM', 'Dinner + relaxation', 60, 'Low', 'Monday,Tuesday,Wednesday,Thursday,Friday'),
        ('9:00 PM - 10:30 PM', 'Personal time', 90, 'Low', 'Monday,Tuesday,Wednesday,Thursday,Friday'),
        ('10:30 PM - 11:00 PM', 'Wind-down routine', 30, 'Low', 'Monday,Tuesday,Wednesday,Thursday,Friday'),
        ('11:00 PM', 'Sleep', 0, 'Low', 'Monday,Tuesday,Wednesday,Thursday,Friday')
        ''')

        # Insert initial habits
        cursor.execute('''
        INSERT INTO habits (name, goal_id, frequency, streak, created_at)
        VALUES
        ('Morning workout', 1, 'daily', 0, ?),
        ('Study data science', 2, 'daily', 0, ?),
        ('Codebase review', 3, 'weekdays', 0, ?)
        ''', (datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y-%m-%d')))

        conn.commit()
        return conn
    else:
        return sqlite3.connect('growth_navigator.db')

# Routes
@app.route('/')
def index():
    conn = get_db_connection()

    # Get goals
    goals = conn.execute('SELECT * FROM goals WHERE status = "active" ORDER BY priority').fetchall()

    # Get today's routine
    today_name = datetime.now().strftime('%A')
    routines = conn.execute('SELECT * FROM routines WHERE weekdays LIKE ? ORDER BY time_block', (f'%{today_name}%',)).fetchall()

    # Get habits
    habits = conn.execute('''
        SELECT h.*, g.description as goal_description,
        (SELECT COUNT(*) FROM habit_logs hl WHERE hl.habit_id = h.id AND hl.completed_date = ?) as completed_today
        FROM habits h
        LEFT JOIN goals g ON h.goal_id = g.id
    ''', (date.today().strftime('%Y-%m-%d'),)).fetchall()

    conn.close()

    return render_template('index.html', goals=goals, routines=routines, habits=habits, today=date.today().strftime('%Y-%m-%d'))

@app.route('/goals')
def view_goals():
    conn = get_db_connection()
    goals = conn.execute('SELECT * FROM goals ORDER BY priority').fetchall()
    conn.close()
    return render_template('goals.html', goals=goals)

@app.route('/goals/add', methods=['GET', 'POST'])
def add_goal():
    if request.method == 'POST':
        category = request.form['category']
        description = request.form['description']
        deadline = request.form['deadline']
        priority = request.form['priority']

        conn = get_db_connection()
        conn.execute('INSERT INTO goals (category, description, deadline, priority, status) VALUES (?, ?, ?, ?, ?)',
                    (category, description, deadline, priority, 'active'))
        conn.commit()
        conn.close()

        flash('Goal added successfully!')
        return redirect(url_for('view_goals'))

    return render_template('add_goal.html')

@app.route('/goals/edit/<int:id>', methods=['GET', 'POST'])
def edit_goal(id):
    conn = get_db_connection()
    goal = conn.execute('SELECT * FROM goals WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        category = request.form['category']
        description = request.form['description']
        deadline = request.form['deadline']
        priority = request.form['priority']
        status = request.form['status']

        conn.execute('UPDATE goals SET category = ?, description = ?, deadline = ?, priority = ?, status = ? WHERE id = ?',
                    (category, description, deadline, priority, status, id))
        conn.commit()
        conn.close()

        flash('Goal updated successfully!')
        return redirect(url_for('view_goals'))

    conn.close()
    return render_template('edit_goal.html', goal=goal)

@app.route('/routines')
def view_routines():
    conn = get_db_connection()
    routines = conn.execute('SELECT * FROM routines ORDER BY time_block').fetchall()
    conn.close()
    return render_template('routines.html', routines=routines)

@app.route('/routines/add', methods=['GET', 'POST'])
def add_routine():
    if request.method == 'POST':
        time_block = request.form['time_block']
        activity = request.form['activity']
        duration = request.form['duration']
        energy_level = request.form['energy_level']
        weekdays = ','.join(request.form.getlist('weekdays'))

        conn = get_db_connection()
        conn.execute('INSERT INTO routines (time_block, activity, duration, energy_level, weekdays) VALUES (?, ?, ?, ?, ?)',
                    (time_block, activity, duration, energy_level, weekdays))
        conn.commit()
        conn.close()

        flash('Routine activity added successfully!')
        return redirect(url_for('view_routines'))

    return render_template('add_routine.html')

@app.route('/routines/edit/<int:id>', methods=['GET', 'POST'])
def edit_routine(id):
    conn = get_db_connection()
    routine = conn.execute('SELECT * FROM routines WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        time_block = request.form['time_block']
        activity = request.form['activity']
        duration = request.form['duration']
        energy_level = request.form['energy_level']
        weekdays = ','.join(request.form.getlist('weekdays'))

        conn.execute('UPDATE routines SET time_block = ?, activity = ?, duration = ?, energy_level = ?, weekdays = ? WHERE id = ?',
                    (time_block, activity, duration, energy_level, weekdays, id))
        conn.commit()
        conn.close()

        flash('Routine updated successfully!')
        return redirect(url_for('view_routines'))

    weekdays = routine[5].split(',') if routine[5] else []
    conn.close()
    return render_template('edit_routine.html', routine=routine, selected_weekdays=weekdays)

@app.route('/habits')
def view_habits():
    conn = get_db_connection()
    habits = conn.execute('''
        SELECT h.*, g.description as goal_description
        FROM habits h
        LEFT JOIN goals g ON h.goal_id = g.id
        ORDER BY h.name
    ''').fetchall()

    # Get completion data for calendar view
    habit_logs = conn.execute('''
        SELECT habit_id, completed_date, COUNT(*) as count
        FROM habit_logs
        GROUP BY habit_id, completed_date
    ''').fetchall()

    # Convert to format needed for calendar
    calendar_data = {}
    for log in habit_logs:
        habit_id = log[0]
        completed_date = log[1]

        if habit_id not in calendar_data:
            calendar_data[habit_id] = []

        calendar_data[habit_id].append(completed_date)

    conn.close()

    return render_template('habits.html', habits=habits, calendar_data=json.dumps(calendar_data), today=date.today().strftime('%Y-%m-%d'))

@app.route('/habits/add', methods=['GET', 'POST'])
def add_habit():
    if request.method == 'POST':
        name = request.form['name']
        goal_id = request.form['goal_id'] if request.form['goal_id'] != '' else None
        frequency = request.form['frequency']

        conn = get_db_connection()
        conn.execute('INSERT INTO habits (name, goal_id, frequency, streak, created_at) VALUES (?, ?, ?, ?, ?)',
                    (name, goal_id, frequency, 0, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        conn.close()

        flash('Habit added successfully!')
        return redirect(url_for('view_habits'))

    conn = get_db_connection()
    goals = conn.execute('SELECT id, description FROM goals WHERE status = "active"').fetchall()
    conn.close()

    return render_template('add_habit.html', goals=goals)

@app.route('/habits/log/<int:id>', methods=['POST'])
def log_habit(id):
    completed = request.form.get('completed', 'false') == 'true'
    today = date.today().strftime('%Y-%m-%d')
    notes = request.form.get('notes', '')

    conn = get_db_connection()

    # Check if already logged today
    existing = conn.execute('SELECT id FROM habit_logs WHERE habit_id = ? AND completed_date = ?',
                        (id, today)).fetchone()

    if completed:
        if not existing:
            # Add log
            conn.execute('INSERT INTO habit_logs (habit_id, completed_date, notes) VALUES (?, ?, ?)',
                        (id, today, notes))

            # Update streak
            habit = conn.execute('SELECT streak FROM habits WHERE id = ?', (id,)).fetchone()
            new_streak = int(habit[0]) + 1
            conn.execute('UPDATE habits SET streak = ? WHERE id = ?', (new_streak, id))

            conn.commit()
            flash('Habit marked as completed!')
    else:
        if existing:
            # Remove log
            conn.execute('DELETE FROM habit_logs WHERE habit_id = ? AND completed_date = ?',
                        (id, today))

            # Reset streak
            conn.execute('UPDATE habits SET streak = 0 WHERE id = ?', (id,))

            conn.commit()
            flash('Habit completion removed!')

    conn.close()
    return redirect(request.referrer or url_for('index'))

@app.route('/habits/edit/<int:id>', methods=['GET', 'POST'])
def edit_habit(id):
    conn = get_db_connection()
    habit = conn.execute('SELECT * FROM habits WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        goal_id = request.form['goal_id'] if request.form['goal_id'] != '' else None
        frequency = request.form['frequency']
        streak = int(request.form['streak'])

        conn.execute('UPDATE habits SET name = ?, goal_id = ?, frequency = ?, streak = ? WHERE id = ?',
                    (name, goal_id, frequency, streak, id))
        conn.commit()
        conn.close()

        flash('Habit updated successfully!')
        return redirect(url_for('view_habits'))

    goals = conn.execute('SELECT id, description FROM goals WHERE status = "active"').fetchall()
    conn.close()
    return render_template('edit_habit.html', habit=habit, goals=goals)

@app.route('/habits/delete/<int:id>', methods=['POST'])
def delete_habit(id):
    conn = get_db_connection()

    # Delete habit logs first (foreign key constraint)
    conn.execute('DELETE FROM habit_logs WHERE habit_id = ?', (id,))

    # Delete the habit
    conn.execute('DELETE FROM habits WHERE id = ?', (id,))

    conn.commit()
    conn.close()

    flash('Habit deleted successfully!')
    return redirect(url_for('view_habits'))

@app.route('/analytics')
def analytics():
    conn = get_db_connection()

    # Get habit completion rates
    habits = conn.execute('''
        SELECT h.id, h.name, h.created_at,
        (SELECT COUNT(*) FROM habit_logs hl WHERE hl.habit_id = h.id) as total_completions,
        (julianday('now') - julianday(h.created_at)) as days_since_creation
        FROM habits h
    ''').fetchall()

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
        WHERE weekdays LIKE ?
        GROUP BY energy_level
    ''', (f'%{today_name}%',)).fetchall()

    conn.close()

    return render_template('analytics.html', habit_stats=habit_stats, energy_distribution=energy_distribution)

if __name__ == '__main__':
    app.run(debug=True)