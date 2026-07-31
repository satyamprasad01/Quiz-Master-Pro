"""Data access helpers for per-user per-category progress / unlock logic."""

from .db import get_db

PASS_PERCENTAGE = 60.0


def get_unlocked_level(user_id: int, category: str) -> int:
    """Return the highest unlocked level (defaults to 1)."""
    row = get_db().execute(
        "SELECT highest_level_unlocked FROM progress WHERE user_id = ? AND category = ?",
        (user_id, category),
    ).fetchone()
    return row["highest_level_unlocked"] if row else 1


def _row(user_id: int, category: str):
    return get_db().execute(
        "SELECT * FROM progress WHERE user_id = ? AND category = ?", (user_id, category)
    ).fetchone()


def unlock_if_passed(user_id: int, category: str, level: int, percentage: float, max_level: int) -> int:
    """If a level is passed, unlock the next one. Returns the new unlocked level."""
    current = get_unlocked_level(user_id, category)
    target = min(level + 1, max_level)

    if percentage >= PASS_PERCENTAGE and target > current:
        conn = get_db()
        if _row(user_id, category):
            conn.execute(
                "UPDATE progress SET highest_level_unlocked = ? WHERE user_id = ? AND category = ?",
                (target, user_id, category),
            )
        else:
            conn.execute(
                "INSERT INTO progress (user_id, category, highest_level_unlocked) VALUES (?, ?, ?)",
                (user_id, category, target),
            )
        conn.commit()
        return target
    return current


def reset_all_progress() -> None:
    conn = get_db()
    conn.execute("DELETE FROM progress")
    conn.commit()


def category_progress_for_user(user_id: int):
    """Progress dict per category for the dashboard/levels pages."""
    categories = get_db().execute("SELECT name FROM categories ORDER BY name").fetchall()
    progress = {}
    for cat in categories:
        unlocked = get_unlocked_level(user_id, cat["name"])
        completed = get_db().execute(
            "SELECT DISTINCT level FROM results WHERE user_id = ? AND category = ? AND percentage >= ?",
            (user_id, cat["name"], PASS_PERCENTAGE),
        ).fetchall()
        progress[cat["name"]] = {
            "unlocked": unlocked,
            "completed": sorted(row["level"] for row in completed),
        }
    return progress
