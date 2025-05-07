# Personal Growth Navigator - Gamification Features

This document provides an overview of the gamification features added to the Personal Growth Navigator application.

## Overview

The gamification features are designed to increase user engagement and motivation by adding:

1. **Achievement System**
   - Tiered achievements (Bronze, Silver, Gold, Platinum)
   - Visual badges and notifications
   - XP rewards for unlocking achievements

2. **Points & Leveling**
   - Experience (XP) points for completing habits and goals
   - User levels with titles (Beginner → Explorer → Achiever → Master, etc.)
   - Visual level progression

3. **Challenge System**
   - Weekly challenges with different difficulty levels
   - XP rewards for completing challenges
   - Progress tracking

## Setup Instructions

To set up the gamification features:

1. Make sure the application is running at least once to create the initial database
2. Run the setup script:
   ```
   python setup_gamification.py
   ```
3. Restart the application:
   ```
   python app.py
   ```

## Features Explanation

### Achievements

Achievements are unlocked automatically as you use the application. They are organized into categories:

- **Habits**: Related to creating and maintaining habits
- **Goals**: Related to setting and achieving goals
- **Routines**: Related to creating and optimizing daily routines
- **System**: Related to general application usage

Each achievement has a tier (Bronze, Silver, Gold, Platinum) and awards XP when unlocked.

### Levels

As you earn XP, you'll progress through levels:

1. **Beginner** (0-99 XP)
2. **Explorer** (100-299 XP)
3. **Achiever** (300-599 XP)
4. **Pathfinder** (600-999 XP)
5. **Trailblazer** (1000-1499 XP)
6. **Innovator** (1500-2099 XP)
7. **Master** (2100-2799 XP)
8. **Champion** (2800-3599 XP)
9. **Luminary** (3600-4499 XP)
10. **Legend** (4500+ XP)

Your current level is displayed in the sidebar, showing your progress to the next level.

### Challenges

Challenges are weekly tasks that provide additional motivation and XP rewards. They are categorized by difficulty:

- **Easy**: Simple tasks with smaller XP rewards
- **Medium**: Moderate tasks with medium XP rewards
- **Hard**: Difficult tasks with larger XP rewards

You can track your progress on challenges and mark them as completed to earn XP.

## Earning XP

You can earn XP in several ways:

1. **Completing Habits**: 10 XP per habit completion
2. **Streak Milestones**: Bonus XP for reaching streak milestones (7, 30, 66, 100 days)
3. **Unlocking Achievements**: XP rewards vary by achievement tier
4. **Completing Challenges**: XP rewards vary by challenge difficulty

## UI Elements

The gamification features include several UI elements:

1. **Achievement Notifications**: Pop-up notifications when you unlock achievements
2. **Level Up Modal**: Celebration screen when you reach a new level
3. **User Level Display**: Shows your current level and progress in the sidebar
4. **Achievements Page**: Displays all achievements, both locked and unlocked
5. **Challenges Page**: Shows active challenges and allows tracking progress

## Customization

The gamification system is designed to be extensible. You can:

1. Add new achievements by editing `populate_gamification_data.py`
2. Adjust XP values and level thresholds
3. Create new challenges

## Technical Details

The gamification system uses several database tables:

- `achievements`: Stores available achievements
- `user_achievements`: Tracks unlocked achievements
- `levels`: Defines level thresholds and titles
- `xp_transactions`: Logs XP earnings
- `challenges`: Stores available challenges
- `user_challenges`: Tracks challenge progress

The system is implemented using:

- `gamification_helper.py`: Core logic for achievements, XP, and levels
- `templates/achievements.html`: UI for achievements
- `templates/challenges.html`: UI for challenges
- `templates/components/achievement_notification.html`: Achievement notifications
- `templates/components/level_up_modal.html`: Level up celebration
- `templates/components/user_level_sidebar.html`: User level display
