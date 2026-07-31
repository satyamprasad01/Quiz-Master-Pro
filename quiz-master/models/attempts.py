"""Data access helpers for in-progress quiz attempts.

Attempts are stored in the database (keyed by a random token) so that a quiz
can be resumed after a page refresh and its full state is available for the
post-submission answer review.
"""

import json
import secrets
import time

from .db import get_db

ATTEMPT_TTL_SECONDS = 24 * 60 * 60  # abandon attempts older than 1 day


def _now() -> float:
    return time.time()


def create_attempt(user_id: int, category: str, level: int, questions: list, duration: int) -> str:
    """Create a new attempt and return its token."""
    token = secrets.token_urlsafe(24)
    state = {
        "questions": questions,  # [{id, question, options, correct}]
        "answers": {},           # {question_index: selected_option_index}
        "started_at": _now(),
        "duration": duration,
        "submitted": False,
        "submitted_at": None,
        "time_taken": None,
        "result_id": None,
    }
    conn = get_db()
    # Clean up stale attempts for this user+category+level to keep things tidy.
    conn.execute(
        "DELETE FROM attempts WHERE user_id = ? AND category = ? AND level = ? AND state LIKE '%\"submitted\": false%'",
        (user_id, category, level),
    )
    conn.execute(
        "INSERT INTO attempts (id, user_id, category, level, state) VALUES (?, ?, ?, ?, ?)",
        (token, user_id, category, level, json.dumps(state)),
    )
    conn.commit()
    return token


def get_attempt(token: str):
    return get_db().execute("SELECT * FROM attempts WHERE id = ?", (token,)).fetchone()


def get_active_attempt_for(user_id: int, category: str, level: int):
    """Return the most recent unfinished attempt for a user/category/level."""
    row = get_db().execute(
        """SELECT * FROM attempts
           WHERE user_id = ? AND category = ? AND level = ?
           ORDER BY updated_at DESC LIMIT 1""",
        (user_id, category, level),
    ).fetchone()
    if not row:
        return None
    state = json.loads(row["state"])
    if state.get("submitted"):
        return None
    if _now() - state.get("started_at", 0) > ATTEMPT_TTL_SECONDS:
        return None
    return row


def get_attempt_by_result(result_id: int, user_id: int):
    """Return an attempt linked to a given result (for the answer review)."""
    row = get_db().execute(
        "SELECT * FROM attempts WHERE user_id = ? AND state LIKE ? ORDER BY updated_at DESC LIMIT 1",
        (user_id, f"%\"result_id\": {result_id}%"),
    ).fetchone()
    return row


def load_state(attempt) -> dict:
    return json.loads(attempt["state"])


def save_state(attempt_id: str, state: dict) -> None:
    conn = get_db()
    conn.execute(
        "UPDATE attempts SET state = ?, updated_at = datetime('now') WHERE id = ?",
        (json.dumps(state), attempt_id),
    )
    conn.commit()


def remaining_seconds(attempt, state: dict) -> int:
    """Seconds left before auto-submit (0 when time is up)."""
    elapsed = _now() - state.get("started_at", _now())
    return max(0, int(state["duration"] - elapsed))


def finish_attempt(attempt_id: str, state: dict, result_id: int) -> None:
    """Mark an attempt submitted and link its result."""
    state["submitted"] = True
    state["submitted_at"] = _now()
    state["result_id"] = result_id
    save_state(attempt_id, state)


def cleanup_stale() -> None:
    conn = get_db()
    conn.execute("DELETE FROM attempts WHERE (julianday('now') - julianday(created_at)) * 86400 > ?", (ATTEMPT_TTL_SECONDS,))
    conn.commit()


def attempt_count() -> int:
    return get_db().execute("SELECT COUNT(*) AS c FROM attempts").fetchone()["c"]
