"""Admin blueprint: analytics, question/category/level CRUD, users & scores."""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from models import questions, results, users
from utils.decorators import admin_required
from utils.security import csrf_required, sanitize_text

admin = Blueprint("admin", __name__, url_prefix="/admin")


@admin.route("/")
@admin_required
def dashboard():
    return render_template("admin.html")


# ---------------------------------------------------------------------------
# Questions
# ---------------------------------------------------------------------------
@admin.route("/questions")
@admin_required
def questions_page():
    categories = questions.all_categories()
    levels = questions.all_levels()
    cat = request.args.get("category") or None
    lvl = request.args.get("level") or None
    level = int(lvl) if lvl and lvl.isdigit() else None
    rows = questions.all_questions(cat, level)
    return render_template(
        "admin_questions.html",
        categories=categories,
        levels=levels,
        rows=rows,
        selected_category=cat,
        selected_level=level,
    )


@admin.route("/questions/add", methods=["POST"])
@admin_required
@csrf_required
def question_add():
    category, level, q, opts, correct = _question_form()
    if not _validate_question(category, level, q, opts, correct):
        flash("Invalid question data. All fields are required.", "danger")
        return redirect(request.referrer or url_for("admin.questions_page"))
    questions.add_question(category, level, q, opts, correct)
    flash("Question added.", "success")
    return redirect(url_for("admin.questions_page", category=category, level=level))


@admin.route("/questions/<int:qid>/edit", methods=["POST"])
@admin_required
@csrf_required
def question_edit(qid):
    row = questions.get_question(qid)
    if not row:
        abort(404)
    category, level, q, opts, correct = _question_form()
    if not _validate_question(category, level, q, opts, correct):
        flash("Invalid question data. All fields are required.", "danger")
        return redirect(url_for("admin.questions_page"))
    questions.update_question(qid, category, level, q, opts, correct)
    flash("Question updated.", "success")
    return redirect(url_for("admin.questions_page", category=category, level=level))


@admin.route("/questions/<int:qid>/delete", methods=["POST"])
@admin_required
@csrf_required
def question_delete(qid):
    questions.delete_question(qid)
    flash("Question deleted.", "info")
    return redirect(request.referrer or url_for("admin.questions_page"))


def _question_form():
    category = sanitize_text(request.form.get("category", ""), 60)
    try:
        level = int(request.form.get("level") or 0)
    except (TypeError, ValueError):
        level = 0
    q = sanitize_text(request.form.get("question", ""), 1000)
    opts = [sanitize_text(request.form.get(f"option{i}", ""), 500) for i in range(1, 5)]
    try:
        correct = int(request.form.get("correct_option") or 0)
    except (TypeError, ValueError):
        correct = 0
    return category, level, q, opts, correct


def _validate_question(category, level, q, opts, correct) -> bool:
    if not category or not level or not q:
        return False
    if not all(opts):
        return False
    if not (1 <= correct <= 4):
        return False
    return True


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------
@admin.route("/categories")
@admin_required
def categories_page():
    return render_template("admin_categories.html", categories=questions.all_categories())


@admin.route("/categories/add", methods=["POST"])
@admin_required
@csrf_required
def category_add():
    name = sanitize_text(request.form.get("name", ""), 60)
    icon = sanitize_text(request.form.get("icon", "fa-folder-open"), 60)
    color = sanitize_text(request.form.get("color", "#6c5ce7"), 20)
    desc = sanitize_text(request.form.get("description", ""), 300)
    if not name:
        flash("Category name is required.", "danger")
        return redirect(url_for("admin.categories_page"))
    if questions.get_category(name):
        flash("That category already exists.", "danger")
        return redirect(url_for("admin.categories_page"))
    questions.add_category(name, icon, desc, color)
    flash("Category added.", "success")
    return redirect(url_for("admin.categories_page"))


@admin.route("/categories/<int:cid>/edit", methods=["POST"])
@admin_required
@csrf_required
def category_edit(cid):
    name = sanitize_text(request.form.get("name", ""), 60)
    icon = sanitize_text(request.form.get("icon", "fa-folder-open"), 60)
    color = sanitize_text(request.form.get("color", "#6c5ce7"), 20)
    desc = sanitize_text(request.form.get("description", ""), 300)
    if not name:
        flash("Category name is required.", "danger")
        return redirect(url_for("admin.categories_page"))
    questions.update_category(cid, name, icon, desc, color)
    flash("Category updated.", "success")
    return redirect(url_for("admin.categories_page"))


@admin.route("/categories/<int:cid>/delete", methods=["POST"])
@admin_required
@csrf_required
def category_delete(cid):
    questions.delete_category(cid)
    flash("Category deleted (its questions and results were removed too).", "info")
    return redirect(url_for("admin.categories_page"))


# ---------------------------------------------------------------------------
# Levels
# ---------------------------------------------------------------------------
@admin.route("/levels")
@admin_required
def levels_page():
    return render_template("admin_levels.html", levels=questions.all_levels())


@admin.route("/levels/add", methods=["POST"])
@admin_required
@csrf_required
def level_add():
    try:
        num = int(request.form.get("level_number") or 0)
    except (TypeError, ValueError):
        num = 0
    name = sanitize_text(request.form.get("name", ""), 60)
    color = sanitize_text(request.form.get("color", "#00b894"), 20)
    desc = sanitize_text(request.form.get("description", ""), 300)
    if not num or not name:
        flash("Level number and name are required.", "danger")
        return redirect(url_for("admin.levels_page"))
    if questions.get_level(num):
        flash("That level number already exists.", "danger")
        return redirect(url_for("admin.levels_page"))
    questions.add_level(num, name, desc, color)
    flash("Level added.", "success")
    return redirect(url_for("admin.levels_page"))


@admin.route("/levels/<int:lid>/edit", methods=["POST"])
@admin_required
@csrf_required
def level_edit(lid):
    try:
        num = int(request.form.get("level_number") or 0)
    except (TypeError, ValueError):
        num = 0
    name = sanitize_text(request.form.get("name", ""), 60)
    color = sanitize_text(request.form.get("color", "#00b894"), 20)
    desc = sanitize_text(request.form.get("description", ""), 300)
    if not num or not name:
        flash("Level number and name are required.", "danger")
        return redirect(url_for("admin.levels_page"))
    questions.update_level(lid, num, name, desc, color)
    flash("Level updated.", "success")
    return redirect(url_for("admin.levels_page"))


@admin.route("/levels/<int:lid>/delete", methods=["POST"])
@admin_required
@csrf_required
def level_delete(lid):
    questions.delete_level(lid)
    flash("Level deleted (its questions were removed too).", "info")
    return redirect(url_for("admin.levels_page"))


# ---------------------------------------------------------------------------
# Users & scores
# ---------------------------------------------------------------------------
@admin.route("/users")
@admin_required
def users_page():
    return render_template("admin_users.html", users=users.all_users())


@admin.route("/users/<int:uid>/reset", methods=["POST"])
@admin_required
@csrf_required
def user_reset(uid):
    users.reset_user_progress(uid)
    flash("Progress reset for that user.", "success")
    return redirect(url_for("admin.users_page"))


@admin.route("/scores")
@admin_required
def scores_page():
    return render_template("admin_scores.html", results=results.all_results())


@admin.route("/scores/<int:rid>/delete", methods=["POST"])
@admin_required
@csrf_required
def score_delete(rid):
    results.delete_result(rid)
    flash("Result deleted.", "info")
    return redirect(url_for("admin.scores_page"))
