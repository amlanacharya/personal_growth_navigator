import sqlite3
from datetime import datetime
from flask import flash, session

class GamificationHelper:
    """Helper class for gamification features."""
    
    def __init__(self, db_path='growth_navigator.db'):
        """Initialize the gamification helper."""
        self.db_path = db_path
    
    def get_db_connection(self):
        """Get a connection to the database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def check_achievements(self, user_id):
        """
        Check if the user has earned any new achievements.
        Returns a list of newly unlocked achievements.
        """
        conn = self.get_db_connection()
        new_achievements = []
        
        try:
            # Get all achievements that the user hasn't unlocked yet
            unlocked_achievements = conn.execute('''
                SELECT achievement_id FROM user_achievements WHERE user_id = ?
            ''', (user_id,)).fetchall()
            
            unlocked_ids = [a['achievement_id'] for a in unlocked_achievements]
            
            # Get all available achievements
            achievements = conn.execute('SELECT * FROM achievements').fetchall()
            
            for achievement in achievements:
                if achievement['id'] in unlocked_ids:
                    continue  # Skip already unlocked achievements
                
                # Check if the user meets the requirements for this achievement
                if self._check_achievement_requirements(conn, user_id, achievement):
                    # Unlock the achievement
                    self._unlock_achievement(conn, user_id, achievement)
                    new_achievements.append(dict(achievement))
            
            conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            conn.rollback()
        finally:
            conn.close()
        
        return new_achievements
    
    def _check_achievement_requirements(self, conn, user_id, achievement):
        """Check if the user meets the requirements for an achievement."""
        requirement_type = achievement['requirement_type']
        requirement_value = achievement['requirement_value']
        
        if requirement_type == 'habit_completions':
            # Count total habit completions
            count = conn.execute('''
                SELECT COUNT(*) as count FROM habit_logs hl
                JOIN habits h ON hl.habit_id = h.id
                WHERE h.user_id = ?
            ''', (user_id,)).fetchone()['count']
            return count >= requirement_value
            
        elif requirement_type == 'streak_days':
            # Check if any habit has the required streak
            max_streak = conn.execute('''
                SELECT MAX(streak) as max_streak FROM habits
                WHERE user_id = ?
            ''', (user_id,)).fetchone()['max_streak']
            return max_streak >= requirement_value
            
        elif requirement_type == 'habit_count':
            # Count total habits
            count = conn.execute('''
                SELECT COUNT(*) as count FROM habits
                WHERE user_id = ?
            ''', (user_id,)).fetchone()['count']
            return count >= requirement_value
            
        elif requirement_type == 'goal_count':
            # Count total goals
            count = conn.execute('''
                SELECT COUNT(*) as count FROM goals
                WHERE user_id = ?
            ''', (user_id,)).fetchone()['count']
            return count >= requirement_value
            
        elif requirement_type == 'goal_completions':
            # Count completed goals
            count = conn.execute('''
                SELECT COUNT(*) as count FROM goals
                WHERE user_id = ? AND status = 'completed'
            ''', (user_id,)).fetchone()['count']
            return count >= requirement_value
            
        elif requirement_type == 'goal_categories':
            # Count unique goal categories
            categories = conn.execute('''
                SELECT COUNT(DISTINCT category) as count FROM goals
                WHERE user_id = ?
            ''', (user_id,)).fetchone()['count']
            return categories >= requirement_value
            
        elif requirement_type == 'routine_count':
            # Count total routines
            count = conn.execute('''
                SELECT COUNT(*) as count FROM routines
                WHERE user_id = ?
            ''', (user_id,)).fetchone()['count']
            return count >= requirement_value
            
        elif requirement_type == 'energy_levels':
            # Count unique energy levels in routines
            levels = conn.execute('''
                SELECT COUNT(DISTINCT energy_level) as count FROM routines
                WHERE user_id = ?
            ''', (user_id,)).fetchone()['count']
            return levels >= requirement_value
            
        elif requirement_type == 'account_created':
            # Always true if the user exists
            return True
            
        elif requirement_type == 'sections_visited':
            # This would require tracking in the session, simplified version:
            return False  # Implement actual tracking elsewhere
            
        elif requirement_type == 'analytics_visits':
            # This would require tracking in the database, simplified version:
            return False  # Implement actual tracking elsewhere
            
        elif requirement_type == 'roadmaps_created':
            # Count AI roadmaps
            count = conn.execute('''
                SELECT COUNT(*) as count FROM ai_roadmaps
                WHERE user_id = ?
            ''', (user_id,)).fetchone()['count']
            return count >= requirement_value
            
        elif requirement_type == 'login_streak':
            # This would require tracking login dates, simplified version:
            return False  # Implement actual tracking elsewhere
            
        return False
    
    def _unlock_achievement(self, conn, user_id, achievement):
        """Unlock an achievement for the user and award XP."""
        # Add to user_achievements
        conn.execute('''
            INSERT INTO user_achievements (user_id, achievement_id, unlocked_at)
            VALUES (?, ?, ?)
        ''', (user_id, achievement['id'], datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        # Award XP
        self.award_xp(conn, user_id, achievement['xp_reward'], 'achievement', achievement['id'], 
                     f"Unlocked achievement: {achievement['name']}")
    
    def award_xp(self, conn, user_id, amount, source, source_id=None, description=""):
        """Award XP to the user and check for level up."""
        # Add XP transaction
        conn.execute('''
            INSERT INTO xp_transactions (user_id, amount, source, source_id, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, amount, source, source_id, description, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        # Update user's XP
        conn.execute('''
            UPDATE users SET xp_points = xp_points + ? WHERE id = ?
        ''', (amount, user_id))
        
        # Check for level up
        self._check_level_up(conn, user_id)
    
    def _check_level_up(self, conn, user_id):
        """Check if the user has leveled up and update their level."""
        # Get user's current XP and level
        user = conn.execute('SELECT xp_points, level FROM users WHERE id = ?', (user_id,)).fetchone()
        current_xp = user['xp_points']
        current_level = user['level']
        
        # Get the level data for the user's XP
        new_level_data = conn.execute('''
            SELECT level_number, title FROM levels 
            WHERE min_xp <= ? AND max_xp >= ?
        ''', (current_xp, current_xp)).fetchone()
        
        if new_level_data and new_level_data['level_number'] > current_level:
            # Update user's level
            conn.execute('''
                UPDATE users SET level = ? WHERE id = ?
            ''', (new_level_data['level_number'], user_id))
            
            # Return level up information
            return {
                'old_level': current_level,
                'new_level': new_level_data['level_number'],
                'title': new_level_data['title']
            }
        
        return None
    
    def get_user_level_info(self, user_id):
        """Get the user's level information."""
        conn = self.get_db_connection()
        
        try:
            # Get user's current XP and level
            user = conn.execute('SELECT xp_points, level FROM users WHERE id = ?', (user_id,)).fetchone()
            if not user:
                return None
            
            current_xp = user['xp_points']
            current_level = user['level']
            
            # Get current level data
            level_data = conn.execute('''
                SELECT * FROM levels WHERE level_number = ?
            ''', (current_level,)).fetchone()
            
            if not level_data:
                return None
            
            # Get next level data if not at max level
            next_level_data = None
            if current_level < 10:  # Assuming 10 is max level
                next_level_data = conn.execute('''
                    SELECT * FROM levels WHERE level_number = ?
                ''', (current_level + 1,)).fetchone()
            
            # Calculate progress to next level
            progress = 0
            if next_level_data:
                min_xp = level_data['min_xp']
                max_xp = level_data['max_xp']
                xp_range = max_xp - min_xp
                if xp_range > 0:
                    progress = ((current_xp - min_xp) / xp_range) * 100
            
            return {
                'level': current_level,
                'title': level_data['title'],
                'xp': current_xp,
                'min_xp': level_data['min_xp'],
                'max_xp': level_data['max_xp'],
                'next_level': next_level_data['level_number'] if next_level_data else None,
                'next_title': next_level_data['title'] if next_level_data else None,
                'progress': progress
            }
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            conn.close()
    
    def get_user_achievements(self, user_id):
        """Get all achievements for the user, both unlocked and locked."""
        conn = self.get_db_connection()
        
        try:
            # Get all achievements
            all_achievements = conn.execute('SELECT * FROM achievements ORDER BY category, tier').fetchall()
            
            # Get user's unlocked achievements
            unlocked = conn.execute('''
                SELECT ua.achievement_id, ua.unlocked_at 
                FROM user_achievements ua
                WHERE ua.user_id = ?
            ''', (user_id,)).fetchall()
            
            unlocked_ids = {a['achievement_id']: a['unlocked_at'] for a in unlocked}
            
            # Prepare the result
            achievements = []
            for achievement in all_achievements:
                achievement_dict = dict(achievement)
                achievement_dict['unlocked'] = achievement['id'] in unlocked_ids
                if achievement_dict['unlocked']:
                    achievement_dict['unlocked_at'] = unlocked_ids[achievement['id']]
                achievements.append(achievement_dict)
            
            return achievements
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
        finally:
            conn.close()
    
    def get_active_challenges(self, user_id):
        """Get active challenges for the user."""
        conn = self.get_db_connection()
        
        try:
            # Get active challenges
            challenges = conn.execute('''
                SELECT c.*, uc.status, uc.progress
                FROM challenges c
                LEFT JOIN user_challenges uc ON c.id = uc.challenge_id AND uc.user_id = ?
                WHERE c.is_active = 1 AND c.end_date >= date('now')
                ORDER BY c.start_date
            ''', (user_id,)).fetchall()
            
            return [dict(c) for c in challenges]
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
        finally:
            conn.close()
    
    def update_challenge_progress(self, user_id, challenge_id, progress):
        """Update the user's progress on a challenge."""
        conn = self.get_db_connection()
        
        try:
            # Check if user is already participating in this challenge
            user_challenge = conn.execute('''
                SELECT * FROM user_challenges
                WHERE user_id = ? AND challenge_id = ?
            ''', (user_id, challenge_id)).fetchone()
            
            if not user_challenge:
                # Add user to challenge
                conn.execute('''
                    INSERT INTO user_challenges (user_id, challenge_id, progress)
                    VALUES (?, ?, ?)
                ''', (user_id, challenge_id, progress))
            else:
                # Update progress
                conn.execute('''
                    UPDATE user_challenges
                    SET progress = ?
                    WHERE user_id = ? AND challenge_id = ?
                ''', (progress, user_id, challenge_id))
            
            # Check if challenge is completed
            if progress >= 100:
                # Mark as completed
                conn.execute('''
                    UPDATE user_challenges
                    SET status = 'completed', completed_at = ?
                    WHERE user_id = ? AND challenge_id = ?
                ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id, challenge_id))
                
                # Award XP
                challenge = conn.execute('SELECT * FROM challenges WHERE id = ?', (challenge_id,)).fetchone()
                if challenge:
                    self.award_xp(conn, user_id, challenge['xp_reward'], 'challenge', challenge_id,
                                 f"Completed challenge: {challenge['title']}")
            
            conn.commit()
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            conn.rollback()
        finally:
            conn.close()
