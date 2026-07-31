"""API blueprint: JSON endpoints for charts, leaderboards, achievements & search."""

from collections import Counter
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request, session

from models import questions, results, users
from models.db import get_db
from utils.decorators import login_required
from utils.grading import is_pass

api = Blueprint("api", __name__)


@api.route("/api/leaderboard")
@login_required
def leaderboard():
    entries = results.leaderboard(limit=50)
    return jsonify(
        [
            {
                "rank": i + 1,
                "username": e["username"],
                "category": e["category"],
                "level": e["level"],
                "score": e["score"],
                "percentage": e["percentage"],
                "time_taken": e["time_taken"],
            }
            for i, e in enumerate(entries)
        ]
    )


@api.route("/api/user/stats")
@login_required
def user_stats():
    """Chart data for the dashboard."""
    user_id = session["user_id"]
    user_results = results.results_for_user(user_id)

    # Attempts per day (last 14 days)
    today = datetime.utcnow()
    days = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(13, -1, -1)]
    per_day = Counter((r["date"] or "")[:10] for r in user_results)
    attempts_over_time = [per_day.get(d, 0) for d in days]

    # Score distribution by category
    category_scores = {}
    for r in user_results:
        category_scores.setdefault(r["category"], []).append(r["percentage"])
    category_labels = []
    category_avg = []
    for cat, scores in sorted(category_scores.items()):
        category_labels.append(cat)
        category_avg.append(round(sum(scores) / len(scores), 1))

    # Recent score trend (last 10 results)
    recent = list(reversed(user_results[-10:]))
    trend_labels = [f"#{r['id']}" for r in recent]
    trend_values = [r["percentage"] for r in recent]

    return jsonify(
        {
            "attempts_over_time": {"labels": days, "values": attempts_over_time},
            "category_avg": {"labels": category_labels, "values": category_avg},
            "score_trend": {"labels": trend_labels, "values": trend_values},
            "total_attempts": len(user_results),
        }
    )


@api.route("/api/achievements")
@login_required
def achievements():
    user_id = session["user_id"]
    user_results = results.results_for_user(user_id)
    cats = questions.all_categories()
    max_level = len(questions.all_levels())

    badges = []
    if len(user_results) >= 1:
        badges.append(("First Steps", "Completed your first quiz.", "fa-flag-checkered"))
    if any(r["percentage"] >= 90 for r in user_results):
        badges.append(("Sharpshooter", "Scored 90% or higher.", "fa-bullseye"))
    if any(r["percentage"] == 100 for r in user_results):
        badges.append(("Perfect!", "Scored a perfect 100%.", "fa-crown"))
    if any(r["time_taken"] <= 180 for r in user_results):
        badges.append(("Speed Demon", "Finished a quiz in under 3 minutes.", "fa-bolt"))
    if len([r for r in user_results if r["percentage"] >= 90]) >= 5:
        badges.append(("Quiz Machine", "Five quizzes at 90% or better.", "fa-robot"))

    completed_by_cat = Counter((r["category"], r["level"]) for r in user_results if is_pass(r["percentage"]))
    for cat in cats:
        cat_done = sum(1 for lvl in range(1, max_level + 1) if (cat["name"], lvl) in completed_by_cat)
        if cat_done == max_level:
            badges.append((f"{cat['name']} Champion", "Completed every level in this category.", cat["icon"] or "fa-trophy"))

    total_done = sum(1 for lvl in range(1, max_level + 1) for cat in cats if (cat["name"], lvl) in completed_by_cat)
    if total_done == max_level * len(cats):
        badges.append(("Quiz Master Pro", "Completed every level in every category!", "fa-medal"))

    return jsonify([{"name": n, "desc": d, "icon": i} for n, d, i in badges])


@api.route("/api/search")
@login_required
def search():
    """Search categories and levels (returns suggestions)."""
    q = request.args.get("q", "").strip().lower()
    if len(q) < 2:
        return jsonify([])

    cats = [
        {"type": "category", "name": c["name"], "icon": c["icon"], "color": c["color"]}
        for c in questions.all_categories()
        if q in c["name"].lower() or q in c["description"].lower()
    ]
    lvls = [
        {"type": "level", "name": l["name"], "number": l["level_number"], "color": l["color"]}
        for l in questions.all_levels()
        if q in l["name"].lower() or q in l["description"].lower()
    ]
    return jsonify(cats + lvls)


@api.route("/api/admin/stats")
def admin_stats():
    """Analytics for the admin dashboard."""
    if session.get("role") != "admin":
        return jsonify(error="Forbidden"), 403

    conn = get_db()
    user_count = users.user_count()
    question_count = questions.question_count()
    result_count = results.result_count()

    per_category = [
        {"category": c["name"], "icon": c["icon"], "count": questions.count_questions(c["name"])}
        for c in questions.all_categories()
    ]

    per_level = [
        {"level": l["level_number"], "name": l["name"], "count": questions.count_questions(level=l["level_number"])}
        for l in questions.all_levels()
    ]

    attempts_per_day_rows = conn.execute(
        "SELECT date(date) AS day, COUNT(*) AS c FROM results GROUP BY date(date) ORDER BY day DESC LIMIT 14"
    ).fetchall()
    attempts_per_day = [{"label": r["day"], "count": r["c"]} for r in reversed(attempts_per_day_rows)]

    avg_score = conn.execute("SELECT AVG(percentage) AS a FROM results").fetchone()["a"]

    return jsonify(
        {
            "users": user_count,
            "questions": question_count,
            "results": result_count,
            "avg_score": round(avg_score or 0, 1),
            "per_category": per_category,
            "per_level": per_level,
            "attempts_per_day": attempts_per_day,
        }
    )
