"""Quiz blueprint: start, play, autosave answers, auto-submit, grading."""

import time

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from models import attempts, progress, questions, results
from utils.decorators import login_required
from utils.grading import safe_category
from utils.security import csrf_required

quiz = Blueprint("quiz", __name__)

QUIZ_LENGTH = 10          # questions per quiz
QUIZ_DURATION = 600       # seconds (10 minutes)


def _active_attempt(user_id: int):
    """Find the latest unfinished attempt for this user (any category)."""
    from models.db import get_db

    conn = get_db()
    rows = conn.execute(
        """SELECT * FROM attempts WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1""",
        (user_id,),
    ).fetchall()
    for r in rows:
        if not attempts.load_state(r).get("submitted"):
            return r
    return None


def _public_state(state: dict) -> dict:
    """Client-safe copy of attempt state (correct answers are never revealed)."""
    return {
        "questions": [
            {"id": q["id"], "question": q["question"], "options": q["options"]}
            for q in state["questions"]
        ],
        "answers": state["answers"],
        "remaining": max(0, int(state["duration"] - (time.time() - state["started_at"]))),
        "submitted": state["submitted"],
    }


@quiz.route("/quiz/start", methods=["POST"])
@login_required
@csrf_required
def start():
    data = request.get_json(silent=True) or {}
    category = safe_category(request.form.get("category") or data.get("category"))
    try:
        level = int(request.form.get("level") or data.get("level") or 0)
    except (TypeError, ValueError):
        level = 0

    cat = questions.get_category(category)
    if not cat:
        flash("Category not found.", "danger")
        return redirect(url_for("main.categories"))

    max_level = len(questions.all_levels())
    if not (1 <= level <= max_level):
        flash("Invalid level.", "danger")
        return redirect(url_for("main.levels", category=category))

    unlocked = progress.get_unlocked_level(session["user_id"], category)
    if level > unlocked:
        flash("This level is locked. Complete the previous level to unlock it.", "warning")
        return redirect(url_for("main.levels", category=category))

    pool = questions.get_questions_for_quiz(category, level, limit=QUIZ_LENGTH)
    if len(pool) < QUIZ_LENGTH:
        flash(f"Not enough questions for {category} Level {level} yet.", "warning")
        return redirect(url_for("main.levels", category=category))

    # Build shuffled options per question (keep track of the correct index).
    import random

    quiz_questions = []
    for q in pool:
        options = [q["option1"], q["option2"], q["option3"], q["option4"]]
        correct = options[q["correct_option"] - 1]
        random.shuffle(options)
        quiz_questions.append(
            {"id": q["id"], "question": q["question"], "options": options, "correct": options.index(correct)}
        )

    token = attempts.create_attempt(session["user_id"], category, level, quiz_questions, QUIZ_DURATION)
    session["active_attempt"] = token
    return redirect(url_for("quiz.quiz_page"))


@quiz.route("/quiz", methods=["GET", "POST"])
@login_required
def quiz_page():
    user_id = session["user_id"]
    token = session.get("active_attempt")
    attempt = attempts.get_attempt(token) if token else None
    if not attempt:
        attempt = _active_attempt(user_id)

    if not attempt:
        flash("No active quiz. Pick a level to get started.", "info")
        return redirect(url_for("main.categories"))

    if attempt["user_id"] != user_id:
        return redirect(url_for("main.categories"))

    state = attempts.load_state(attempt)
    if state.get("submitted"):
        return redirect(url_for("main.result", result_id=state["result_id"]))

    # Auto-submit when the timer has already run out (page loaded too late).
    if attempts.remaining_seconds(attempt, state) <= 0:
        return redirect(url_for("quiz.auto_submit", attempt=attempt["id"]))

    session["active_attempt"] = attempt["id"]
    category = attempt["category"]
    return render_template(
        "quiz.html",
        attempt_id=attempt["id"],
        category=category,
        level=attempt["level"],
        question_count=QUIZ_LENGTH,
        duration=state["duration"],
        remaining=attempts.remaining_seconds(attempt, state),
        csrf_token=session.get("csrf_token"),
    )


@quiz.route("/quiz/auto-submit/<attempt>")
@login_required
def auto_submit(attempt):
    """Server-side submit triggered when the timer expires."""
    row = attempts.get_attempt(attempt)
    if not row or row["user_id"] != session["user_id"]:
        return redirect(url_for("main.categories"))
    state = attempts.load_state(row)
    if state.get("submitted"):
        return redirect(url_for("main.result", result_id=state["result_id"]))
    _grade(row, state, timed_out=True)
    return redirect(url_for("main.result", result_id=state["result_id"]))


@quiz.route("/quiz/state")
@login_required
def state():
    """JSON endpoint used by quiz.js to (re)load the current attempt."""
    attempt = attempts.get_attempt(session.get("active_attempt")) if session.get("active_attempt") else None
    if not attempt or attempt["user_id"] != session["user_id"]:
        return jsonify(error="No active quiz."), 404
    state = attempts.load_state(attempt)
    if state.get("submitted"):
        return jsonify(submitted=True, result_id=state["result_id"])
    return jsonify(_public_state(state))


@quiz.route("/quiz/answer", methods=["POST"])
@login_required
@csrf_required
def answer():
    """Autosave a single answer (called on every option click)."""
    attempt = attempts.get_attempt(session.get("active_attempt")) if session.get("active_attempt") else None
    if not attempt or attempt["user_id"] != session["user_id"]:
        return jsonify(error="No active quiz."), 404

    data = request.get_json(silent=True) or {}
    q_index = data.get("q_index")
    selected = data.get("selected")

    if q_index is None or selected is None:
        return jsonify(error="Missing parameters."), 400
    try:
        q_index = int(q_index)
        selected = int(selected)
    except (TypeError, ValueError):
        return jsonify(error="Invalid parameters."), 400

    state = attempts.load_state(attempt)
    if state.get("submitted"):
        return jsonify(error="Quiz already submitted."), 409
    if not (0 <= q_index < len(state["questions"])):
        return jsonify(error="Question index out of range."), 400

    state["answers"][str(q_index)] = selected
    attempts.save_state(attempt["id"], state)
    return jsonify(ok=True, answered=len(state["answers"]))


@quiz.route("/quiz/submit", methods=["POST"])
@login_required
@csrf_required
def submit():
    """Grade the quiz and store the result. Returns JSON for the result page."""
    attempt = attempts.get_attempt(session.get("active_attempt")) if session.get("active_attempt") else None
    if not attempt or attempt["user_id"] != session["user_id"]:
        return jsonify(error="No active quiz."), 404

    state = attempts.load_state(attempt)
    if state.get("submitted"):
        return jsonify(submitted=True, result_id=state["result_id"])

    _grade(attempt, state, timed_out=False)
    return jsonify(ok=True, result_id=state["result_id"])


def _grade(attempt, state: dict, timed_out: bool) -> None:
    """Grade answers, persist the result and unlock the next level."""
    answers = state["answers"]
    total = len(state["questions"])
    score = 0
    for i, q in enumerate(state["questions"]):
        if answers.get(str(i)) == q["correct"]:
            score += 1

    elapsed = int(time.time() - state["started_at"])
    time_taken = min(elapsed, state["duration"])

    result = results.add_result(
        attempt["user_id"],
        attempt["category"],
        attempt["level"],
        score,
        total,
        time_taken,
        attempt_id=attempt["id"],
    )
    attempts.finish_attempt(attempt["id"], state, result["id"])

    max_level = len(questions.all_levels())
    progress.unlock_if_passed(
        attempt["user_id"], attempt["category"], attempt["level"], result["percentage"], max_level
    )
    session.pop("active_attempt", None)
