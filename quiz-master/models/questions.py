"""Data access helpers for categories, levels and questions."""


from .db import get_db


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------
def all_categories():
    return get_db().execute("SELECT * FROM categories ORDER BY name").fetchall()


def get_category(name: str):
    return get_db().execute("SELECT * FROM categories WHERE name = ?", (name,)).fetchone()


def add_category(name: str, icon: str, description: str, color: str) -> None:
    conn = get_db()
    conn.execute(
        "INSERT INTO categories (name, icon, description, color) VALUES (?, ?, ?, ?)",
        (name, icon, description, color),
    )
    conn.commit()


def update_category(category_id: int, name: str, icon: str, description: str, color: str) -> None:
    conn = get_db()
    old = conn.execute("SELECT * FROM categories WHERE id = ?", (category_id,)).fetchone()
    conn.execute(
        "UPDATE categories SET name = ?, icon = ?, description = ?, color = ? WHERE id = ?",
        (name, icon, description, color, category_id),
    )
    if old and old["name"] != name:
        conn.execute("UPDATE questions SET category = ? WHERE category = ?", (name, old["name"]))
        conn.execute("UPDATE results SET category = ? WHERE category = ?", (name, old["name"]))
        conn.execute("UPDATE progress SET category = ? WHERE category = ?", (name, old["name"]))
    conn.commit()


def delete_category(category_id: int) -> None:
    conn = get_db()
    cat = conn.execute("SELECT * FROM categories WHERE id = ?", (category_id,)).fetchone()
    if cat:
        conn.execute("DELETE FROM questions WHERE category = ?", (cat["name"],))
        conn.execute("DELETE FROM results WHERE category = ?", (cat["name"],))
        conn.execute("DELETE FROM progress WHERE category = ?", (cat["name"],))
        conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        conn.commit()


# ---------------------------------------------------------------------------
# Levels
# ---------------------------------------------------------------------------
def all_levels():
    return get_db().execute("SELECT * FROM levels ORDER BY level_number").fetchall()


def get_level(level_number: int):
    return get_db().execute("SELECT * FROM levels WHERE level_number = ?", (level_number,)).fetchone()


def add_level(level_number: int, name: str, description: str, color: str) -> None:
    conn = get_db()
    conn.execute(
        "INSERT INTO levels (level_number, name, description, color) VALUES (?, ?, ?, ?)",
        (level_number, name, description, color),
    )
    conn.commit()


def update_level(level_id: int, level_number: int, name: str, description: str, color: str) -> None:
    conn = get_db()
    conn.execute(
        "UPDATE levels SET level_number = ?, name = ?, description = ?, color = ? WHERE id = ?",
        (level_number, name, description, color, level_id),
    )
    conn.commit()


def delete_level(level_id: int) -> None:
    conn = get_db()
    level = conn.execute("SELECT * FROM levels WHERE id = ?", (level_id,)).fetchone()
    if level:
        conn.execute("DELETE FROM questions WHERE level = ?", (level["level_number"],))
        conn.execute("DELETE FROM levels WHERE id = ?", (level_id,))
        conn.commit()


# ---------------------------------------------------------------------------
# Questions
# ---------------------------------------------------------------------------
def question_count() -> int:
    return get_db().execute("SELECT COUNT(*) AS c FROM questions").fetchone()["c"]


def count_questions(category: str | None = None, level: int | None = None) -> int:
    sql = "SELECT COUNT(*) AS c FROM questions WHERE 1=1"
    args: list = []
    if category:
        sql += " AND category = ?"
        args.append(category)
    if level:
        sql += " AND level = ?"
        args.append(level)
    return get_db().execute(sql, args).fetchone()["c"]


def get_questions_for_quiz(category: str, level: int, limit: int = 10):
    """Return up to ``limit`` questions for a quiz.

    Uses ``ORDER BY RANDOM()`` so every attempt gets a fresh shuffle.
    """
    rows = get_db().execute(
        "SELECT * FROM questions WHERE category = ? AND level = ? ORDER BY RANDOM() LIMIT ?",
        (category, level, limit),
    ).fetchall()
    return [dict(row) for row in rows]


def all_questions(category: str | None = None, level: int | None = None):
    sql = "SELECT q.*, c.icon AS category_icon FROM questions q LEFT JOIN categories c ON c.name = q.category WHERE 1=1"
    args: list = []
    if category:
        sql += " AND q.category = ?"
        args.append(category)
    if level:
        sql += " AND q.level = ?"
        args.append(level)
    sql += " ORDER BY q.category, q.level, q.id"
    return get_db().execute(sql, args).fetchall()


def get_question(question_id: int):
    return get_db().execute("SELECT * FROM questions WHERE id = ?", (question_id,)).fetchone()


def add_question(category: str, level: int, question: str, options: list, correct: int) -> None:
    conn = get_db()
    conn.execute(
        """INSERT INTO questions
           (category, level, question, option1, option2, option3, option4, correct_option)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (category, level, question, options[0], options[1], options[2], options[3], correct),
    )
    conn.commit()


def update_question(
    question_id: int, category: str, level: int, question: str, options: list, correct: int
) -> None:
    conn = get_db()
    conn.execute(
        """UPDATE questions SET
           category = ?, level = ?, question = ?, option1 = ?, option2 = ?,
           option3 = ?, option4 = ?, correct_option = ?
           WHERE id = ?""",
        (category, level, question, options[0], options[1], options[2], options[3], correct, question_id),
    )
    conn.commit()


def delete_question(question_id: int) -> None:
    conn = get_db()
    conn.execute("DELETE FROM questions WHERE id = ?", (question_id,))
    conn.commit()
