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

IMPORTANT FORMATTING INSTRUCTIONS:
When providing a roadmap or plan, you MUST structure your response in this exact format:

1. Start with a VERY brief introduction (maximum 2 sentences).

2. Then provide a structured roadmap with these EXACT section headers:

## GOALS
- [Specific, measurable goal - maximum 12 words]
- [Specific, measurable goal - maximum 12 words]
- [Specific, measurable goal - maximum 12 words]

## HABITS
- [Single concrete daily action - maximum 8 words]
- [Single concrete daily action - maximum 8 words]
- [Single concrete daily action - maximum 8 words]

## ROUTINES
- [Time]: [Specific activity]
- [Time]: [Specific activity]
- [Time]: [Specific activity]

3. Only AFTER these structured sections, you may provide additional context, explanations, or implementation strategies in a separate section:

## NOTES
- Additional context or explanations here
- Implementation strategies here

ALL goals, habits, and routines MUST be formatted as single-line bullet points starting with a hyphen (-).
Do NOT include explanatory text within these sections.
Each item should be specific, actionable, and concise.

This structured format is essential as it allows the system to properly extract and display your recommendations to the user. Always use the exact section headers (## GOALS, ## HABITS, ## ROUTINES) and bullet points as shown above.

When responding, always start by analyzing the current situation before offering recommendations. Focus on providing actionable insights rather than general productivity advice. Remember that the goal is sustainable growth, not burnout-inducing perfectionism."""

class AIHelper:
    def __init__(self):
        """Initialize the AI Helper."""
        # Store the path to the database
        self.db_path = 'growth_navigator.db'
        self.model = "llama3-70b-8192"  # Default model - using 8B parameter version

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
        Extract goals, habits, and routines from the AI response with improved parsing.

        Args:
            ai_response (str): The AI's response

        Returns:
            dict: Dictionary containing extracted goals, habits, and routines
        """
        roadmap = {
            "goals": [],
            "habits": [],
            "routines": []
        }

        # Split the response into lines for processing
        lines = ai_response.split('\n')

        # First identify section boundaries
        section_starts = {
            "goals": -1,
            "habits": -1,
            "routines": -1
        }

        section_ends = {
            "goals": -1,
            "habits": -1,
            "routines": -1
        }

        for i, line in enumerate(lines):
            line = line.strip().lower()

            if line == "## goals":
                section_starts["goals"] = i
            elif line == "## habits":
                if section_starts["goals"] >= 0 and section_ends["goals"] < 0:
                    section_ends["goals"] = i
                section_starts["habits"] = i
            elif line == "## routines":
                if section_starts["habits"] >= 0 and section_ends["habits"] < 0:
                    section_ends["habits"] = i
                section_starts["routines"] = i
            elif line.startswith("##") and section_starts["routines"] >= 0 and section_ends["routines"] < 0:
                # Another section after routines (like ## NOTES)
                section_ends["routines"] = i

        # Set end boundaries for sections without explicit end
        if section_ends["goals"] < 0 and section_starts["habits"] >= 0:
            section_ends["goals"] = section_starts["habits"]
        if section_ends["habits"] < 0 and section_starts["routines"] >= 0:
            section_ends["habits"] = section_starts["routines"]
        if section_ends["routines"] < 0:
            section_ends["routines"] = len(lines)

        # Extract items from each section
        for section_name in ["goals", "habits", "routines"]:
            start = section_starts[section_name]
            end = section_ends[section_name]

            if start >= 0 and end > start:
                for i in range(start + 1, end):
                    line = lines[i].strip()

                    # Skip empty lines
                    if not line:
                        continue

                    # Only extract properly formatted items (bullet points)
                    if line.startswith('-'):
                        item = line[1:].strip()

                        # Filter out non-actionable items
                        if self._is_valid_item(item):
                            roadmap[section_name].append(item)

        # If the structured format wasn't found, try a more flexible approach
        if not any(roadmap.values()):
            current_section = None
            for line in lines:
                line = line.strip()

                # Skip empty lines
                if not line:
                    continue

                # Look for section headers in a more flexible way
                if "goal" in line.lower() and (":" in line or line.endswith("s")):
                    current_section = "goals"
                    continue
                elif "habit" in line.lower() and (":" in line or line.endswith("s")):
                    current_section = "habits"
                    continue
                elif "routine" in line.lower() and (":" in line or line.endswith("s")):
                    current_section = "routines"
                    continue

                # Add items to the appropriate section
                if current_section and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                    # Remove the bullet point character and any leading/trailing whitespace
                    item = line[1:].strip()
                    if self._is_valid_item(item):
                        roadmap[current_section].append(item)
                # Also try to capture numbered items
                elif current_section and (line[0].isdigit() and line[1:3] in ['. ', ') ']):
                    item = line[line.find(' ')+1:].strip()
                    if self._is_valid_item(item):
                        roadmap[current_section].append(item)

        return roadmap

    def _is_valid_item(self, text):
        """
        Validate if an extracted item is actionable and properly formatted.

        Args:
            text (str): The text to validate

        Returns:
            bool: True if the item is valid, False otherwise
        """
        # Skip empty items
        if not text or len(text) < 3:
            return False

        # Exclude explanatory phrases often seen in AI responses
        exclude_phrases = ["here are", "these are", "you can", "for example", "etc.", "such as"]
        for phrase in exclude_phrases:
            if phrase in text.lower():
                return False

        # Skip very lengthy items (likely paragraphs)
        if len(text) > 100:
            return False

        return True

# Helper function to create a .env file if it doesn't exist
def create_env_file():
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write("# .env file for Personal Growth Navigator\n")
            f.write("GROQ_API_KEY=your_groq_api_key_here\n")
        print("Created .env file. Please edit it to add your Groq API key.")
