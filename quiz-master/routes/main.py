"""Main blueprint: home, categories, levels, leaderboard, dashboard, result."""

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from models import attempts, progress, questions, results, users
from utils.decorators import login_required
from utils.grading import get_grade, get_message, is_pass

main = Blueprint("main", __name__)


@main.route("/")
def index():
    stats = {
        "questions": questions.question_count(),
        "categories": len(questions.all_categories()),
        "users": users.user_count(),
        "attempts": results.result_count(),
    }
    top = results.leaderboard(limit=5)
    return render_template("index.html", stats=stats, top=top)


@main.route("/categories")
@login_required
def categories():
    cats = questions.all_categories()
    level_count = len(questions.all_levels())
    prog = progress.category_progress_for_user(session["user_id"])
    return render_template("categories.html", categories=cats, level_count=level_count, progress=prog)


@main.route("/levels/<category>")
@login_required
def levels(category):
    cat = questions.get_category(category)
    if not cat:
        abort(404)
    level_rows = questions.all_levels()
    unlocked = progress.get_unlocked_level(session["user_id"], category)
    completed = {
        row["level"]
        for row in results.results_for_user(session["user_id"])
        if row["category"] == category and is_pass(row["percentage"])
    }

    level_cards = []
    for lvl in level_rows:
        q_count = questions.count_questions(category, lvl["level_number"])
        level_cards.append(
            {
                "level": lvl,
                "question_count": q_count,
                "unlocked": lvl["level_number"] <= unlocked,
                "completed": lvl["level_number"] in completed,
            }
        )
    return render_template(
        "levels.html",
        category=cat,
        levels=level_cards,
        unlocked=unlocked,
        max_level=level_rows[-1]["level_number"] if level_rows else 5,
    )


@main.route("/leaderboard")
@login_required
def leaderboard():
    entries = results.leaderboard(limit=50)
    user_id = session["user_id"]
    return render_template("leaderboard.html", entries=entries, user_id=user_id)


@main.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    categories = questions.all_categories()
    level_count = len(questions.all_levels())

    recent = results.results_for_user(user_id, limit=8)
    prog = progress.category_progress_for_user(user_id)
    all_levels_total = level_count * len(categories)
    completed = len({(c, l) for c in prog for l in prog[c]["completed"]})

    stats = {
        "completed_levels": completed,
        "locked_levels": max(all_levels_total - completed, 0),
        "total_levels": all_levels_total,
        "highest_score": results.best_score_for_user(user_id),
        "average_score": results.average_score_for_user(user_id),
    }
    leader = results.leaderboard(limit=5)
    continue_quiz = None
    for cat in categories:
        for lvl in range(1, level_count + 1):
            att = attempts.get_active_attempt_for(user_id, cat["name"], lvl)
            if att:
                continue_quiz = {"attempt": att, "category": cat["name"], "level": lvl}
                break
        if continue_quiz:
            break

    return render_template(
        "dashboard.html",
        stats=stats,
        recent=recent,
        progress=prog,
        categories=categories,
        leaderboard=leader,
        continue_quiz=continue_quiz,
    )


@main.route("/result/<int:result_id>")
@login_required
def result(result_id):
    res = results.get_result(result_id)
    if not res or res["user_id"] != session["user_id"]:
        abort(404)

    grade = get_grade(res["percentage"])
    message = get_message(res["percentage"], grade)
    passed = is_pass(res["percentage"])
    rank = results.rank_of(res)

    # Answer review: reconstruct the exact questions/options the user saw.
    review = None
    att = attempts.get_attempt_by_result(result_id, session["user_id"])
    if att:
        state = attempts.load_state(att)
        review = []
        for idx, q in enumerate(state["questions"]):
            chosen = state["answers"].get(str(idx))
            review.append(
                {
                    "question": q["question"],
                    "options": q["options"],
                    "correct": q["correct"],
                    "chosen": chosen,
                    "is_correct": chosen == q["correct"],
                }
            )

    # Next level suggestion (if passed)
    max_level = len(questions.all_levels())
    unlocked = progress.get_unlocked_level(session["user_id"], res["category"])
    next_level = res["level"] + 1 if (passed and res["level"] < max_level and next_level_unlocked(unlocked, res["level"])) else None

    return render_template(
        "result.html",
        result=res,
        grade=grade,
        message=message,
        passed=passed,
        rank=rank,
        review=review,
        next_level=next_level,
        max_level=max_level,
    )


def next_level_unlocked(unlocked: int, current_level: int) -> bool:
    return unlocked >= current_level + 1


@main.route("/search")
@login_required
def search():
    """Client-side search landing page (categories/levels)."""
    q = request.args.get("q", "").strip().lower()
    cats = [c for c in questions.all_categories() if q in c["name"].lower() or q in c["description"].lower()]
    lvls = [l for l in questions.all_levels() if q in l["name"].lower() or q in l["description"].lower()]
    return render_template(
        "search.html",
        q=request.args.get("q", ""),
        categories=cats,
        levels=lvls,
    )
