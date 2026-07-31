"""Data access helpers for quiz results."""

from .db import get_db


def add_result(
    user_id: int,
    category: str,
    level: int,
    score: int,
    total: int,
    time_taken: int,
    attempt_id: str | None = None,
) -> dict:
    """Store a result and return it as a dict with percentage."""
    percentage = round((score / total) * 100, 2)
    conn = get_db()
    cur = conn.execute(
        """INSERT INTO results (user_id, category, level, score, total, percentage, time_taken, attempt_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, category, level, score, total, percentage, time_taken, attempt_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM results WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


def get_result(result_id: int):
    return get_db().execute("SELECT * FROM results WHERE id = ?", (result_id,)).fetchone()


def results_for_user(user_id: int, limit: int | None = None):
    sql = "SELECT * FROM results WHERE user_id = ? ORDER BY date DESC, id DESC"
    args: list = [user_id]
    if limit:
        sql += " LIMIT ?"
        args.append(limit)
    return get_db().execute(sql, args).fetchall()


def all_results():
    return get_db().execute(
        """SELECT r.*, u.username FROM results r
           JOIN users u ON u.id = r.user_id
           ORDER BY r.date DESC""",
    ).fetchall()


def best_score_for_user(user_id: int):
    row = get_db().execute(
        "SELECT MAX(percentage) AS best FROM results WHERE user_id = ?", (user_id,)
    ).fetchone()
    return row["best"] or 0


def average_score_for_user(user_id: int):
    row = get_db().execute(
        "SELECT AVG(percentage) AS avg FROM results WHERE user_id = ?", (user_id,)
    ).fetchone()
    return round(row["avg"], 1) if row["avg"] is not None else 0


def completed_levels_for_user(user_id: int):
    """Distinct category/level pairs completed (attempted and passed)."""
    rows = get_db().execute(
        "SELECT DISTINCT category, level FROM results WHERE user_id = ? AND percentage >= 60",
        (user_id,),
    ).fetchall()
    return [(row["category"], row["level"]) for row in rows]


def leaderboard(limit: int = 10):
    """Top ranked attempts: by score, then percentage, then faster time."""
    return get_db().execute(
        """SELECT r.*, u.username FROM results r
           JOIN users u ON u.id = r.user_id
           ORDER BY r.score DESC, r.percentage DESC, r.time_taken ASC
           LIMIT ?""",
        (limit,),
    ).fetchall()


def rank_of(result) -> int:
    """Position of a result in the global leaderboard (1-based)."""
    row = get_db().execute(
        """SELECT COUNT(*) AS better FROM results
           WHERE score > ? OR (score = ? AND percentage > ?)
              OR (score = ? AND percentage = ? AND time_taken < ?)""",
        (
            result["score"],
            result["score"],
            result["percentage"],
            result["score"],
            result["percentage"],
            result["time_taken"],
        ),
    ).fetchone()
    return row["better"] + 1


def result_count() -> int:
    return get_db().execute("SELECT COUNT(*) AS c FROM results").fetchone()["c"]


def delete_result(result_id: int) -> None:
    conn = get_db()
    conn.execute("DELETE FROM results WHERE id = ?", (result_id,))
    conn.commit()
