import sqlite3
import json
from datetime import datetime, timedelta
import random
from src.ai.helpers.ai_helper import AIHelper

class AIInsightsHelper:
    def __init__(self):
        """Initialize the AI Insights Helper."""
        self.db_path = 'growth_navigator.db'
        self.ai_helper = AIHelper()
        
    def get_insights(self, user_id):
        """
        Generate personalized insights for the user based on their data.
        
        Args:
            user_id (int): The user's ID
            
        Returns:
            list: A list of insight objects
        """
        insights = []
        
        # Get habit insights
        habit_insights = self.get_habit_insights(user_id)
        if habit_insights:
            insights.extend(habit_insights)
            
        # Get goal insights
        goal_insights = self.get_goal_insights(user_id)
        if goal_insights:
            insights.extend(goal_insights)
            
        # Get routine insights
        routine_insights = self.get_routine_insights(user_id)
        if routine_insights:
            insights.extend(routine_insights)
            
        # Get mood insights
        mood_insights = self.get_mood_insights(user_id)
        if mood_insights:
            insights.extend(mood_insights)
            
        # If we have too many insights, prioritize and limit them
        if len(insights) > 5:
            # Sort by priority (if available) or randomly sample
            insights = sorted(insights, key=lambda x: x.get('priority', 5))[:5]
            
        # If we have no insights, generate some generic ones
        if not insights:
            insights = self.get_generic_insights(user_id)
            
        return insights
    
    def get_habit_insights(self, user_id):
        """Generate insights related to habits."""
        insights = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get habits with completion data
            habits_data = conn.execute('''
                SELECT h.id, h.name, h.streak, COUNT(hl.id) as completion_count,
                       (SELECT COUNT(*) FROM habit_logs WHERE habit_id = h.id AND completed_date >= date('now', '-7 days')) as recent_completions
                FROM habits h
                LEFT JOIN habit_logs hl ON h.id = hl.habit_id
                WHERE h.user_id = ?
                GROUP BY h.id
            ''', (user_id,)).fetchall()
            
            for habit in habits_data:
                # Check for habits with low recent completion
                if habit['recent_completions'] == 0 and habit['completion_count'] > 0:
                    insights.append({
                        'title': 'Habit Needs Attention',
                        'content': f"You haven't completed '{habit['name']}' in the last week. Would you like to adjust this habit or get motivation tips?",
                        'icon': 'fa-exclamation-triangle',
                        'color': 'warning',
                        'priority': 1,
                        'actions': [
                            {
                                'text': 'Adjust Habit',
                                'url': f"/edit_habit/{habit['id']}",
                                'icon': 'fa-edit'
                            },
                            {
                                'text': 'Get Motivation',
                                'url': f"/ai_habit_motivation/{habit['id']}",
                                'icon': 'fa-bolt'
                            }
                        ]
                    })
                
                # Check for habits with good streaks
                elif habit['streak'] >= 5:
                    insights.append({
                        'title': 'Streak Building!',
                        'content': f"Great job maintaining '{habit['name']}' for {habit['streak']} days in a row! Keep it up!",
                        'icon': 'fa-fire',
                        'color': 'success',
                        'priority': 3,
                        'actions': [
                            {
                                'text': 'View Habit',
                                'url': f"/view_habits",
                                'icon': 'fa-eye'
                            }
                        ]
                    })
            
            conn.close()
            
        except Exception as e:
            print(f"Error generating habit insights: {e}")
            
        return insights
    
    def get_goal_insights(self, user_id):
        """Generate insights related to goals."""
        insights = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get goals with no linked habits
            goals_without_habits = conn.execute('''
                SELECT g.id, g.description 
                FROM goals g
                LEFT JOIN habits h ON g.id = h.goal_id
                WHERE g.user_id = ? AND g.status = 'active' AND h.id IS NULL
                GROUP BY g.id
            ''', (user_id,)).fetchall()
            
            for goal in goals_without_habits:
                insights.append({
                    'title': 'Goal Missing Habits',
                    'content': f"Your goal '{goal['description']}' doesn't have any habits linked to it. Adding daily habits can help you make consistent progress.",
                    'icon': 'fa-link-slash',
                    'color': 'primary',
                    'priority': 2,
                    'actions': [
                        {
                            'text': 'Add Habit',
                            'url': f"/add_habit?goal_id={goal['id']}",
                            'icon': 'fa-plus'
                        },
                        {
                            'text': 'AI Suggestions',
                            'url': f"/ai_suggest_habits/{goal['id']}",
                            'icon': 'fa-robot'
                        }
                    ]
                })
            
            conn.close()
            
        except Exception as e:
            print(f"Error generating goal insights: {e}")
            
        return insights
    
    def get_routine_insights(self, user_id):
        """Generate insights related to routines."""
        insights = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Check if user has any routines
            routine_count = conn.execute('SELECT COUNT(*) as count FROM routines WHERE user_id = ?', (user_id,)).fetchone()['count']
            
            if routine_count == 0:
                insights.append({
                    'title': 'Create Your First Routine',
                    'content': "Routines help structure your day for maximum productivity. Would you like help creating your first routine?",
                    'icon': 'fa-clock',
                    'color': 'info',
                    'priority': 2,
                    'actions': [
                        {
                            'text': 'Create Routine',
                            'url': "/add_routine",
                            'icon': 'fa-plus'
                        },
                        {
                            'text': 'AI Suggestions',
                            'url': "/ai_roadmap",
                            'icon': 'fa-robot'
                        }
                    ]
                })
            
            conn.close()
            
        except Exception as e:
            print(f"Error generating routine insights: {e}")
            
        return insights
    
    def get_mood_insights(self, user_id):
        """Generate insights related to mood tracking."""
        insights = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Check for mood patterns
            mood_data = conn.execute('''
                SELECT mood_score, energy_level, logged_at
                FROM mood_logs
                WHERE user_id = ?
                ORDER BY logged_at DESC
                LIMIT 7
            ''', (user_id,)).fetchall()
            
            if len(mood_data) >= 3:
                # Calculate average mood and energy
                avg_mood = sum(m['mood_score'] for m in mood_data) / len(mood_data)
                avg_energy = sum(m['energy_level'] for m in mood_data) / len(mood_data)
                
                if avg_mood < 3 and len(mood_data) >= 3:
                    insights.append({
                        'title': 'Mood Trend Detected',
                        'content': "I've noticed your mood has been lower than usual lately. Would you like some suggestions to boost your wellbeing?",
                        'icon': 'fa-heart',
                        'color': 'danger',
                        'priority': 1,
                        'actions': [
                            {
                                'text': 'Get Suggestions',
                                'url': "/ai_mood_suggestions",
                                'icon': 'fa-lightbulb'
                            },
                            {
                                'text': 'View Mood History',
                                'url': "/mood/history",
                                'icon': 'fa-chart-line'
                            }
                        ]
                    })
                elif avg_energy < 3 and len(mood_data) >= 3:
                    insights.append({
                        'title': 'Energy Optimization',
                        'content': "Your energy levels have been lower recently. I can help optimize your routines to match your energy patterns.",
                        'icon': 'fa-battery-quarter',
                        'color': 'warning',
                        'priority': 2,
                        'actions': [
                            {
                                'text': 'Optimize Schedule',
                                'url': "/ai_energy_optimization",
                                'icon': 'fa-bolt'
                            }
                        ]
                    })
            
            conn.close()
            
        except Exception as e:
            print(f"Error generating mood insights: {e}")
            
        return insights
    
    def get_generic_insights(self, user_id):
        """Generate generic insights when no specific insights are available."""
        generic_insights = [
            {
                'title': 'Welcome to AI Insights',
                'content': "As you use the app more, I'll provide personalized suggestions here based on your habits, goals, and routines.",
                'icon': 'fa-magic',
                'color': 'primary',
                'actions': [
                    {
                        'text': 'Create a Roadmap',
                        'url': "/ai_roadmap",
                        'icon': 'fa-map'
                    }
                ]
            },
            {
                'title': 'Track Your Mood',
                'content': "Logging your mood and energy levels helps me provide better recommendations tailored to your patterns.",
                'icon': 'fa-smile',
                'color': 'info',
                'actions': [
                    {
                        'text': 'Log Mood',
                        'url': "/mood/log",
                        'icon': 'fa-plus'
                    }
                ]
            },
            {
                'title': 'Set Your First Goal',
                'content': "Goals give direction to your growth journey. What would you like to achieve in the next few months?",
                'icon': 'fa-bullseye',
                'color': 'success',
                'actions': [
                    {
                        'text': 'Add Goal',
                        'url': "/add_goal",
                        'icon': 'fa-plus'
                    }
                ]
            }
        ]
        
        # Return 2 random generic insights
        return random.sample(generic_insights, min(2, len(generic_insights)))
    
    def generate_ai_habit_suggestions(self, goal_id):
        """
        Generate AI suggestions for habits based on a goal.
        
        Args:
            goal_id (int): The goal ID
            
        Returns:
            list: A list of suggested habits
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get goal details
            goal = conn.execute('SELECT description FROM goals WHERE id = ?', (goal_id,)).fetchone()
            
            if not goal:
                return []
                
            # Get user's existing habits
            existing_habits = conn.execute('''
                SELECT name FROM habits WHERE user_id = (
                    SELECT user_id FROM goals WHERE id = ?
                )
            ''', (goal_id,)).fetchall()
            
            existing_habits_list = [h['name'] for h in existing_habits]
            
            conn.close()
            
            # Create prompt for AI
            prompt = f"""Based on the goal "{goal['description']}", suggest 5 specific, actionable daily habits that would help achieve this goal. 
            
The user already has these habits: {', '.join(existing_habits_list) if existing_habits_list else 'none yet'}.

Format your response as a JSON array of habit objects with these properties:
- name: The habit name (short, actionable)
- frequency: How often to do it (daily, weekdays, weekends, or specific days)
- description: A brief explanation of why this habit helps the goal

ONLY return the JSON array, nothing else."""
            
            # Get AI response
            response = self.ai_helper.generate_response(prompt)
            
            # Try to parse the JSON response
            try:
                # Clean up the response to extract just the JSON part
                json_str = response
                if "```json" in response:
                    json_str = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    json_str = response.split("```")[1].split("```")[0].strip()
                
                suggestions = json.loads(json_str)
                return suggestions
            except Exception as e:
                print(f"Error parsing AI habit suggestions: {e}")
                print(f"Raw response: {response}")
                return []
                
        except Exception as e:
            print(f"Error generating AI habit suggestions: {e}")
            return []
    
    def generate_energy_optimization(self, user_id):
        """
        Generate an optimized schedule based on the user's energy patterns.
        
        Args:
            user_id (int): The user's ID
            
        Returns:
            dict: Optimized schedule suggestions
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get user's mood and energy data
            mood_data = conn.execute('''
                SELECT mood_score, energy_level, logged_at,
                       strftime('%H', logged_at) as hour
                FROM mood_logs
                WHERE user_id = ?
                ORDER BY logged_at DESC
                LIMIT 14
            ''', (user_id,)).fetchall()
            
            # Get user's routines
            routines = conn.execute('''
                SELECT activity, time_block, energy_required, day_of_week
                FROM routines
                WHERE user_id = ?
            ''', (user_id,)).fetchall()
            
            # Get user's habits
            habits = conn.execute('''
                SELECT name, frequency
                FROM habits
                WHERE user_id = ?
            ''', (user_id,)).fetchall()
            
            conn.close()
            
            # Format data for the AI
            mood_data_formatted = [dict(m) for m in mood_data]
            routines_formatted = [dict(r) for r in routines]
            habits_formatted = [dict(h) for h in habits]
            
            # Create prompt for AI
            prompt = f"""Based on the user's energy patterns, routines, and habits, suggest an optimized daily schedule.

Energy Data (most recent first):
{json.dumps(mood_data_formatted, indent=2)}

Current Routines:
{json.dumps(routines_formatted, indent=2)}

Current Habits:
{json.dumps(habits_formatted, indent=2)}

Analyze the data and provide:
1. The user's peak energy hours
2. Suggested time blocks for high-focus activities
3. Recommended routine adjustments
4. Optimal habit timing

Format your response as a JSON object with these properties:
- peak_hours: Array of hour ranges (e.g. ["8-10", "15-17"])
- focus_blocks: Array of suggested focus time blocks
- routine_adjustments: Array of specific routine change suggestions
- habit_timing: Object mapping habit types to optimal times

ONLY return the JSON object, nothing else."""
            
            # Get AI response
            response = self.ai_helper.generate_response(prompt)
            
            # Try to parse the JSON response
            try:
                # Clean up the response to extract just the JSON part
                json_str = response
                if "```json" in response:
                    json_str = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    json_str = response.split("```")[1].split("```")[0].strip()
                
                optimization = json.loads(json_str)
                return optimization
            except Exception as e:
                print(f"Error parsing AI energy optimization: {e}")
                print(f"Raw response: {response}")
                return {}
                
        except Exception as e:
            print(f"Error generating energy optimization: {e}")
            return {}
