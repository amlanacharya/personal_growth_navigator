-- Schema for the Personal Growth Navigator database

-- Drop tables if they exist
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS goals;
DROP TABLE IF EXISTS routines;
DROP TABLE IF EXISTS habits;
DROP TABLE IF EXISTS habit_logs;
DROP TABLE IF EXISTS ai_conversations;
DROP TABLE IF EXISTS ai_roadmaps;
DROP TABLE IF EXISTS achievements;
DROP TABLE IF EXISTS user_achievements;
DROP TABLE IF EXISTS levels;
DROP TABLE IF EXISTS xp_transactions;
DROP TABLE IF EXISTS challenges;
DROP TABLE IF EXISTS user_challenges;
DROP TABLE IF EXISTS growth_metaphors;
DROP TABLE IF EXISTS mood_logs;
DROP TABLE IF EXISTS ai_notifications;
DROP TABLE IF EXISTS ai_notification_settings;
DROP TABLE IF EXISTS ai_notification_triggers;
DROP TABLE IF EXISTS ai_scheduled_notifications;
DROP TABLE IF EXISTS push_notification_subscriptions;

-- Create tables
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    name TEXT NOT NULL,
    partner_id INTEGER,
    is_new_user BOOLEAN DEFAULT 1,
    level INTEGER DEFAULT 1,
    xp_points INTEGER DEFAULT 0,
    FOREIGN KEY (partner_id) REFERENCES users (id)
);

CREATE TABLE goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    deadline TEXT,
    priority INTEGER,
    status TEXT DEFAULT 'active',
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE routines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    time_block TEXT NOT NULL,
    activity TEXT NOT NULL,
    duration INTEGER,
    energy_level TEXT,
    weekdays TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

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
);

CREATE TABLE habit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id INTEGER,
    completed_date TEXT,
    notes TEXT,
    FOREIGN KEY (habit_id) REFERENCES habits (id)
);

CREATE TABLE ai_conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    user_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE ai_roadmaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    condition TEXT NOT NULL,
    icon TEXT,
    xp_reward INTEGER DEFAULT 0
);

CREATE TABLE user_achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    achievement_id INTEGER NOT NULL,
    unlocked_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (achievement_id) REFERENCES achievements (id)
);

CREATE TABLE levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level INTEGER NOT NULL,
    xp_required INTEGER NOT NULL,
    title TEXT NOT NULL
);

CREATE TABLE xp_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    source TEXT NOT NULL,
    source_id INTEGER,
    description TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    duration_days INTEGER NOT NULL,
    difficulty TEXT NOT NULL,
    xp_reward INTEGER DEFAULT 0
);

CREATE TABLE user_challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    challenge_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    progress INTEGER DEFAULT 0,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (challenge_id) REFERENCES challenges (id)
);

CREATE TABLE growth_metaphors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    levels_json TEXT NOT NULL
);

CREATE TABLE mood_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    mood_score INTEGER NOT NULL,
    mood_note TEXT,
    energy_level INTEGER,
    logged_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE ai_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    type TEXT NOT NULL,
    priority TEXT DEFAULT 'normal',
    read INTEGER DEFAULT 0,
    snoozed_until TEXT,
    actions TEXT,
    metadata TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE ai_notification_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    insights_enabled INTEGER DEFAULT 1,
    suggestions_enabled INTEGER DEFAULT 1,
    alerts_enabled INTEGER DEFAULT 1,
    reminders_enabled INTEGER DEFAULT 1,
    email_notifications INTEGER DEFAULT 0,
    push_notifications INTEGER DEFAULT 0,
    quiet_hours_start TEXT,
    quiet_hours_end TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE ai_notification_triggers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    condition TEXT NOT NULL,
    notification_template TEXT NOT NULL,
    enabled INTEGER DEFAULT 1
);

CREATE TABLE ai_scheduled_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    scheduled_for TEXT NOT NULL,
    sent INTEGER DEFAULT 0,
    notification_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (notification_id) REFERENCES ai_notifications (id)
);

CREATE TABLE push_notification_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    endpoint TEXT NOT NULL,
    p256dh TEXT NOT NULL,
    auth TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
