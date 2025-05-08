import sqlite3
from datetime import datetime, timedelta

def populate_gamification_data():
    """
    Populate the database with initial gamification data.
    This includes achievements, levels, and challenges.
    """
    # Connect to the database
    conn = sqlite3.connect('growth_navigator.db')
    cursor = conn.cursor()
    
    try:
        # 1. Populate levels table
        levels_data = [
            (1, 'Beginner', 0, 99),
            (2, 'Explorer', 100, 299),
            (3, 'Achiever', 300, 599),
            (4, 'Pathfinder', 600, 999),
            (5, 'Trailblazer', 1000, 1499),
            (6, 'Innovator', 1500, 2099),
            (7, 'Master', 2100, 2799),
            (8, 'Champion', 2800, 3599),
            (9, 'Luminary', 3600, 4499),
            (10, 'Legend', 4500, 999999)
        ]
        
        cursor.executemany('''
        INSERT INTO levels (level_number, title, min_xp, max_xp)
        VALUES (?, ?, ?, ?)
        ''', levels_data)
        
        # 2. Populate achievements table
        achievements_data = [
            # Habit achievements - Bronze tier
            ('First Step', 'Complete your first habit', 'footprint', 'habits', 'bronze', 10, 'habit_completions', 1),
            ('Habit Starter', 'Complete 10 habits', 'calendar-check', 'habits', 'bronze', 25, 'habit_completions', 10),
            ('Consistency Beginner', 'Maintain a 3-day streak', 'fire', 'streaks', 'bronze', 15, 'streak_days', 3),
            
            # Habit achievements - Silver tier
            ('Habit Builder', 'Complete 50 habits', 'calendar-check', 'habits', 'silver', 50, 'habit_completions', 50),
            ('Consistency Enthusiast', 'Maintain a 7-day streak', 'fire', 'streaks', 'silver', 35, 'streak_days', 7),
            ('Diverse Habits', 'Create 5 different habits', 'list-check', 'habits', 'silver', 30, 'habit_count', 5),
            
            # Habit achievements - Gold tier
            ('Habit Master', 'Complete 200 habits', 'calendar-check', 'habits', 'gold', 100, 'habit_completions', 200),
            ('Consistency Champion', 'Maintain a 30-day streak', 'fire', 'streaks', 'gold', 150, 'streak_days', 30),
            ('Habit Diversity', 'Create 10 different habits', 'list-check', 'habits', 'gold', 75, 'habit_count', 10),
            
            # Habit achievements - Platinum tier
            ('Habit Legend', 'Complete 1000 habits', 'trophy', 'habits', 'platinum', 300, 'habit_completions', 1000),
            ('Consistency Legend', 'Maintain a 66-day streak', 'crown', 'streaks', 'platinum', 500, 'streak_days', 66),
            
            # Goal achievements - Bronze tier
            ('Goal Setter', 'Create your first goal', 'bullseye', 'goals', 'bronze', 10, 'goal_count', 1),
            ('Goal Achiever', 'Complete your first goal', 'flag-checkered', 'goals', 'bronze', 25, 'goal_completions', 1),
            
            # Goal achievements - Silver tier
            ('Goal Enthusiast', 'Create 5 goals', 'bullseye', 'goals', 'silver', 30, 'goal_count', 5),
            ('Goal Champion', 'Complete 5 goals', 'flag-checkered', 'goals', 'silver', 75, 'goal_completions', 5),
            
            # Goal achievements - Gold tier
            ('Goal Master', 'Complete 15 goals', 'flag-checkered', 'goals', 'gold', 150, 'goal_completions', 15),
            ('Diverse Goals', 'Create goals in 3 different categories', 'layer-group', 'goals', 'gold', 100, 'goal_categories', 3),
            
            # Routine achievements - Bronze tier
            ('Routine Starter', 'Create your first routine', 'clock', 'routines', 'bronze', 10, 'routine_count', 1),
            ('Energy Aware', 'Create routines with different energy levels', 'battery-half', 'routines', 'bronze', 15, 'energy_levels', 2),
            
            # Routine achievements - Silver tier
            ('Routine Builder', 'Create 10 routine activities', 'clock', 'routines', 'silver', 40, 'routine_count', 10),
            ('Energy Master', 'Optimize your routine with all energy levels', 'battery-full', 'routines', 'silver', 50, 'energy_levels', 3),
            
            # System achievements - Bronze tier
            ('Welcome Aboard', 'Create your account', 'user', 'system', 'bronze', 5, 'account_created', 1),
            ('Growth Explorer', 'Visit all main sections of the app', 'compass', 'system', 'bronze', 20, 'sections_visited', 5),
            
            # System achievements - Silver tier
            ('Data Driven', 'Check your analytics page 5 times', 'chart-line', 'system', 'silver', 25, 'analytics_visits', 5),
            ('AI Explorer', 'Generate your first AI roadmap', 'robot', 'system', 'silver', 30, 'roadmaps_created', 1),
            
            # System achievements - Gold tier
            ('Growth Committed', 'Use the app for 30 consecutive days', 'calendar-alt', 'system', 'gold', 200, 'login_streak', 30),
            ('AI Master', 'Generate 10 different AI roadmaps', 'robot', 'system', 'gold', 100, 'roadmaps_created', 10),
        ]
        
        cursor.executemany('''
        INSERT INTO achievements (name, description, icon, category, tier, xp_reward, requirement_type, requirement_value)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', achievements_data)
        
        # 3. Create initial challenges
        today = datetime.now()
        next_week = today + timedelta(days=7)
        
        challenges_data = [
            ('Morning Routine Mastery', 'Complete your morning routine every day this week', 'routines', 'easy', 50, 
             today.strftime('%Y-%m-%d'), next_week.strftime('%Y-%m-%d')),
            ('Streak Builder', 'Achieve a 7-day streak on any habit', 'habits', 'medium', 75, 
             today.strftime('%Y-%m-%d'), next_week.strftime('%Y-%m-%d')),
            ('Goal Progress Push', 'Make significant progress on your highest priority goal', 'goals', 'hard', 100, 
             today.strftime('%Y-%m-%d'), next_week.strftime('%Y-%m-%d')),
        ]
        
        cursor.executemany('''
        INSERT INTO challenges (title, description, category, difficulty, xp_reward, start_date, end_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', challenges_data)
        
        # Commit the changes
        conn.commit()
        print("Gamification data populated successfully!")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    populate_gamification_data()
