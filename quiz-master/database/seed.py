"""Database initialisation and seeding.

Creates all tables and populates default categories, levels, an admin
account and the 200-question bank (only when the tables are empty).
"""

import sqlite3

from .schema import DEFAULT_CATEGORIES, DEFAULT_LEVELS, SCHEMA_SQL
from .questions_data import QUESTIONS

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
ADMIN_EMAIL = "admin@quizmaster.local"


def init_db(conn: sqlite3.Connection) -> None:
    """Create tables and seed default data if missing."""
    conn.executescript(SCHEMA_SQL)

    with conn:
        # Categories
        count = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO categories (name, icon, description, color) VALUES (?, ?, ?, ?)",
                DEFAULT_CATEGORIES,
            )

        # Levels
        count = conn.execute("SELECT COUNT(*) FROM levels").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO levels (level_number, name, description, color) VALUES (?, ?, ?, ?)",
                DEFAULT_LEVELS,
            )

        # Admin account
        count = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'").fetchone()[0]
        if count == 0:
            from werkzeug.security import generate_password_hash

            conn.execute(
                "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, 'admin')",
                (ADMIN_USERNAME, ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD)),
            )

        # Questions
        count = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
        if count == 0:
            conn.executemany(
                """INSERT INTO questions
                   (category, level, question, option1, option2, option3, option4, correct_option)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                QUESTIONS,
            )
