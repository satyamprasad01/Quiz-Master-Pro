"""Authentication blueprint: signup, login, logout, forgot/reset password."""

import secrets

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from models import users
from utils.decorators import public_only
from utils.security import (
    csrf_protect,
    csrf_required,
    sanitize_text,
    valid_email,
    valid_password,
    valid_username,
)

auth = Blueprint("auth", __name__)


@auth.route("/signup", methods=["GET", "POST"])
@public_only
def signup():
    if request.method == "POST":
        if not csrf_protect():
            return "Invalid or missing CSRF token.", 400

        username = sanitize_text(request.form.get("username", ""), 20)
        email = sanitize_text(request.form.get("email", ""), 120).lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        errors = []
        if not valid_username(username):
            errors.append("Username must be 3-20 characters (letters, numbers or underscore).")
        if not valid_email(email):
            errors.append("Please enter a valid email address.")
        if not valid_password(password):
            errors.append("Password must be at least 6 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if users.get_by_username(username):
            errors.append("That username is already taken.")
        if users.get_by_email(email):
            errors.append("That email is already registered.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("signup.html", username=username, email=email)

        user_id = users.create_user(username, email, password)
        session["user_id"] = user_id
        session["username"] = username
        session["role"] = "user"
        flash(f"Welcome aboard, {username}! Your quiz journey begins now.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("signup.html")


@auth.route("/login", methods=["GET", "POST"])
@public_only
def login():
    if request.method == "POST":
        if not csrf_protect():
            return "Invalid or missing CSRF token.", 400

        identifier = sanitize_text(request.form.get("username", ""), 60)
        password = request.form.get("password", "")

        user = users.get_by_username(identifier) or (
            users.get_by_email(identifier.lower()) if valid_email(identifier) else None
        )

        if user and users.verify_password(user, password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            session.permanent = True
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("main.dashboard"))

        flash("Invalid username/email or password.", "danger")
        return render_template("login.html", identifier=identifier)

    return render_template("login.html")


@auth.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))


# ---------------------------------------------------------------------------
# Forgot password (demo flow: reset code is shown on screen in place of an email)
# ---------------------------------------------------------------------------
@auth.route("/forgot", methods=["GET", "POST"])
@public_only
def forgot():
    if request.method == "POST":
        if not csrf_protect():
            return "Invalid or missing CSRF token.", 400
        email = sanitize_text(request.form.get("email", ""), 120).lower()
        user = users.get_by_email(email) if valid_email(email) else None
        if user:
            code = secrets.token_urlsafe(8)
            session["reset_user_id"] = user["id"]
            session["reset_code"] = code
            flash(f"Demo email sent! Use this reset code: {code}", "success")
            return redirect(url_for("auth.reset"))
        flash("No account found with that email address.", "danger")
    return render_template("forgot.html")


@auth.route("/reset", methods=["GET", "POST"])
@public_only
def reset():
    if session.get("reset_user_id") is None:
        return redirect(url_for("auth.forgot"))
    if request.method == "POST":
        if not csrf_protect():
            return "Invalid or missing CSRF token.", 400
        code = sanitize_text(request.form.get("code", ""), 16)
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not secrets.compare_digest(session.get("reset_code", ""), code):
            flash("Invalid reset code.", "danger")
            return render_template("reset.html")
        if not valid_password(password):
            flash("Password must be at least 6 characters.", "danger")
            return render_template("reset.html")
        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("reset.html")

        users.update_password(session["reset_user_id"], password)
        session.pop("reset_user_id", None)
        session.pop("reset_code", None)
        flash("Password updated! You can now log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("reset.html")
