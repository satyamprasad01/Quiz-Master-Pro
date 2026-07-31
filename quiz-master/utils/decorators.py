"""Flask decorators for authentication and authorisation."""

from functools import wraps

from flask import flash, redirect, session, url_for


def login_required(func):
    """Require an authenticated user. Redirects to login otherwise."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        return func(*args, **kwargs)

    return wrapper


def admin_required(func):
    """Require an authenticated admin account."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            flash("You do not have permission to view that page.", "danger")
            return redirect(url_for("main.index"))
        return func(*args, **kwargs)

    return wrapper


def public_only(func):
    """Only allow access when logged out (login/signup pages)."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" in session:
            return redirect(url_for("main.dashboard"))
        return func(*args, **kwargs)

    return wrapper
