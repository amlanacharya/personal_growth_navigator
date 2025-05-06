# ai_helper.py
import os
import json
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Groq client with error handling
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    print("WARNING: GROQ_API_KEY not found in environment variables. Please add it to your .env file.")
    client = None
else:
    client = Groq(api_key=groq_api_key)

# System prompt for the Personal Growth Navigator
SYSTEM_PROMPT = """You are now my Personal Growth Navigator, an expert system designed to help me create, manage, and optimize my daily routines to achieve both personal and professional growth. Your primary function is to transform my goals into actionable daily habits and schedules while adapting to my changing needs and circumstances.
Core Responsibilities:
1. Goal Analysis & Prioritization: Help me clarify and prioritize my short-term and long-term goals across all life domains (career, health, relationships, learning, etc.).
2. Routine Engineering: Create personalized daily/weekly routines that integrate tasks and habits aligned with my prioritized goals.
3. Time Management Optimization: Analyze how I spend my time and suggest improvements to maximize productivity while ensuring adequate rest and recovery.
4. Progress Tracking: Maintain records of my progress toward goals and adjust routines based on what's working and what isn't.
5. Adaptive Planning: Regularly update routines based on changing priorities, energy levels, unexpected events, and feedback.
6. Contextual Intelligence: Account for my unique circumstances including work schedule, family obligations, health considerations, and energy fluctuations.
Interaction Protocol:
Initial Setup:
* Ask me about my personal and professional goals with clear timelines
* Inquire about my current routine, sleep patterns, and energy cycles
* Identify potential obstacles, commitments, and constraints
* Determine my productivity preferences (time blocking, pomodoro, etc.)
* Assess my current habits that help or hinder my goals
Ongoing Support:
* Begin each session with a brief review of progress and challenges since last interaction
* Allow me to easily update you on changing priorities or circumstances
* Provide recommendations for routine adjustments based on feedback
* Offer strategies for overcoming specific obstacles
* Suggest small, incremental improvements rather than complete routine overhauls
Daily/Weekly Planning:
* Create detailed daily schedules with specific time blocks
* Balance goal-oriented activities with necessary maintenance tasks
* Include dedicated time for rest, recreation, and relationships
* Build in buffer time for unexpected events
* Recommend context-specific habits that compound toward my larger goals
Advanced Features:
* Skill Acquisition Pathways: Break down learning goals into daily practice components
* Energy Management: Align high-focus tasks with my peak energy periods
* Decision Fatigue Reduction: Suggest routinization of minor decisions
* Milestone Celebration: Acknowledge progress and achievements
* Habit Stacking: Identify opportunities to link new habits with established ones
* Deep Work Facilitation: Schedule uninterrupted blocks for focused work on high-value tasks
* Seasonal Adaptations: Adjust recommendations based on seasonal changes, travel, or major life events
* Recovery Protocols: Provide strategies for getting back on track after disruptions
Communication Style:
* Be direct and action-oriented
* Provide specific, actionable advice rather than generalities
* Use visual aids when appropriate (tables, charts, diagrams)
* Challenge me when necessary, but remain supportive
* Balance optimization with well-being and sustainability
When responding, always start by analyzing my current situation before offering recommendations. Focus on providing actionable insights rather than general productivity advice. Remember that the goal is sustainable growth, not burnout-inducing perfectionism."""

class AIHelper:
    def __init__(self):
        """Initialize the AI Helper."""
        # Store the path to the database
        self.db_path = 'growth_navigator.db'
        self.model = "llama3-8b-8192"  # Default model - using 8B parameter version

    def set_model(self, model_name):
        """Set the model to use for generation."""
        self.model = model_name

    def generate_response(self, user_message, conversation_history=None):
        """
        Generate a response from the AI model.

        Args:
            user_message (str): The user's message
            conversation_history (list): Optional list of previous messages

        Returns:
            str: The AI's response
        """
        if conversation_history is None:
            conversation_history = []

        # Prepare the messages for the API call
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        # Add conversation history
        for msg in conversation_history:
            messages.append(msg)

        # Add the current user message
        messages.append({"role": "user", "content": user_message})

        try:
            # Check if client is initialized
            if client is None:
                return "AI service is not available. Please make sure you have set up your GROQ_API_KEY in the .env file."

            # Call the Groq API
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=4096,
                top_p=1,
                stream=False
            )

            # Extract and return the response text
            ai_response = response.choices[0].message.content
            return ai_response

        except Exception as e:
            print(f"Error generating AI response: {e}")
            error_message = str(e)
            if "invalid_api_key" in error_message:
                return "There's an issue with the API key. Please make sure you have set up a valid GROQ_API_KEY in the .env file."
            elif "model" in error_message.lower():
                return f"There's an issue with the selected model ({self.model}). The model might not be available or supported."
            else:
                return "I'm sorry, I encountered an error while processing your request. Please try again later."

    def save_conversation(self, user_id, user_message, ai_response):
        """
        Save the conversation to the database.

        Args:
            user_id (int): The user's ID
            user_message (str): The user's message
            ai_response (str): The AI's response

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create a new connection for this operation
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute(
                'INSERT INTO ai_conversations (user_id, user_message, ai_response, timestamp) VALUES (?, ?, ?, ?)',
                (user_id, user_message, ai_response, timestamp)
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Error saving conversation: {e}")
            return False

    def get_conversation_history(self, user_id, limit=10):
        """
        Get the conversation history for a user.

        Args:
            user_id (int): The user's ID
            limit (int): Maximum number of conversations to retrieve

        Returns:
            list: List of conversation dictionaries
        """
        try:
            # Create a new connection for this operation
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                'SELECT user_message, ai_response, timestamp FROM ai_conversations WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?',
                (user_id, limit)
            )

            conversations = cursor.fetchall()

            # Convert to list of dictionaries
            history = []
            for conv in conversations:
                history.append({
                    "user_message": conv[0],
                    "ai_response": conv[1],
                    "timestamp": conv[2]
                })

            conn.close()
            return history

        except Exception as e:
            print(f"Error retrieving conversation history: {e}")
            return []

    def extract_roadmap_items(self, ai_response):
        """
        Extract goals, habits, and routines from the AI response.
        This is a simple implementation and might need refinement.

        Args:
            ai_response (str): The AI's response

        Returns:
            dict: Dictionary containing extracted goals, habits, and routines
        """
        # This is a simplified extraction - in a real implementation,
        # you might want to use more sophisticated NLP or ask the LLM to format its response
        # in a specific way that's easier to parse

        roadmap = {
            "goals": [],
            "habits": [],
            "routines": []
        }

        # Simple keyword-based extraction
        lines = ai_response.split('\n')
        current_section = None

        for line in lines:
            line = line.strip()

            # Check for section headers
            if "goal" in line.lower() and not current_section:
                current_section = "goals"
                continue
            elif "habit" in line.lower() and not current_section:
                current_section = "habits"
                continue
            elif "routine" in line.lower() and not current_section:
                current_section = "routines"
                continue

            # Skip empty lines
            if not line:
                continue

            # Add items to the appropriate section
            if current_section and line.startswith('-'):
                item = line[1:].strip()
                roadmap[current_section].append(item)

        return roadmap

# Helper function to create a .env file if it doesn't exist
def create_env_file():
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write("# .env file for Personal Growth Navigator\n")
            f.write("GROQ_API_KEY=your_groq_api_key_here\n")
        print("Created .env file. Please edit it to add your Groq API key.")
