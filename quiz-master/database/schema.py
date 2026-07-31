"""Database schema for Quiz Master Pro.

Core tables follow the project specification:
    Users, Questions, Results, Progress
plus two metadata tables that power the Admin panel:
    Categories (name, icon, description, colour)
    Levels    (level number, display name, description, colour)
"""

SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT NOT NULL UNIQUE,
    email       TEXT NOT NULL UNIQUE,
    password    TEXT NOT NULL,
    role        TEXT NOT NULL DEFAULT 'user',
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS categories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    icon        TEXT NOT NULL DEFAULT 'fa-flask',
    description TEXT NOT NULL DEFAULT '',
    color       TEXT NOT NULL DEFAULT '#6c5ce7'
);

CREATE TABLE IF NOT EXISTS levels (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    level_number INTEGER NOT NULL UNIQUE,
    name         TEXT NOT NULL,
    description  TEXT NOT NULL DEFAULT '',
    color        TEXT NOT NULL DEFAULT '#00b894'
);

CREATE TABLE IF NOT EXISTS questions (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    category       TEXT NOT NULL,
    level          INTEGER NOT NULL,
    question       TEXT NOT NULL,
    option1        TEXT NOT NULL,
    option2        TEXT NOT NULL,
    option3        TEXT NOT NULL,
    option4        TEXT NOT NULL,
    correct_option INTEGER NOT NULL CHECK (correct_option BETWEEN 1 AND 4)
);

CREATE TABLE IF NOT EXISTS attempts (
    id         TEXT PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category   TEXT NOT NULL,
    level      INTEGER NOT NULL,
    state      TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS results (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category    TEXT NOT NULL,
    level       INTEGER NOT NULL,
    score       INTEGER NOT NULL,
    total       INTEGER NOT NULL DEFAULT 10,
    percentage  REAL NOT NULL,
    time_taken  INTEGER NOT NULL DEFAULT 0,
    attempt_id  TEXT,
    date        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS progress (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id               INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category              TEXT NOT NULL,
    highest_level_unlocked INTEGER NOT NULL DEFAULT 1,
    UNIQUE(user_id, category)
);

CREATE INDEX IF NOT EXISTS idx_questions_cat_level ON questions(category, level);
CREATE INDEX IF NOT EXISTS idx_results_user ON results(user_id);
CREATE INDEX IF NOT EXISTS idx_results_cat_level ON results(category, level);
"""

# Default level metadata (Very Easy -> Expert)
DEFAULT_LEVELS = [
    (1, "Very Easy", "Warm-up questions to build confidence.", "#00b894"),
    (2, "Easy", "Basic concepts, slightly more challenging.", "#00cec9"),
    (3, "Medium", "Solid understanding required.", "#0984e3"),
    (4, "Hard", "Tricky, needs deep knowledge.", "#e17055"),
    (5, "Expert", "The ultimate challenge. Only masters pass.", "#d63031"),
]

# Default category metadata
DEFAULT_CATEGORIES = [
    ("Science", "fa-flask-vial", "Physics, Chemistry, Biology & Astronomy.", "#6c5ce7"),
    ("Mathematics", "fa-calculator", "Numbers, algebra, geometry & logic.", "#0984e3"),
    ("General Knowledge", "fa-earth-americas", "World, history, geography & more.", "#00b894"),
    ("Computer", "fa-computer", "Hardware, software & computing concepts.", "#e17055"),
]
