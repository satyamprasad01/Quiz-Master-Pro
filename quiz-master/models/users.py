"""Data access helpers for users."""

import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db


def create_user(username: str, email: str, password: str, role: str = "user") -> int:
    """Create a user and return the new id."""
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
        (username, email, generate_password_hash(password), role),
    )
    conn.commit()
    return cur.lastrowid


def get_by_username(username: str):
    return get_db().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()


def get_by_email(email: str):
    return get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()


def get_by_id(user_id: int):
    return get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def verify_password(user, password: str) -> bool:
    return check_password_hash(user["password"], password)


def update_password(user_id: int, new_password: str) -> None:
    conn = get_db()
    conn.execute(
        "UPDATE users SET password = ? WHERE id = ?",
        (generate_password_hash(new_password), user_id),
    )
    conn.commit()


def all_users():
    return get_db().execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()


def reset_user_progress(user_id: int) -> None:
    """Delete all results and progress for a user (start over)."""
    conn = get_db()
    conn.execute("DELETE FROM results WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM progress WHERE user_id = ?", (user_id,))
    conn.commit()


def user_count() -> int:
    return get_db().execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
