"""Security helpers: CSRF tokens, sessions and input validation."""

import re
import secrets

from flask import jsonify, request, session

# ---------------------------------------------------------------------------
# CSRF
# ---------------------------------------------------------------------------

# Requests that mutate state must carry a valid CSRF token.
MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def generate_csrf_token() -> str:
    """Return (and lazily create) the per-session CSRF token."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def csrf_protect() -> bool:
    """Return True when the current request is CSRF-safe.

    Compares the ``X-CSRF-Token`` header (AJAX) or the ``csrf_token`` form
    field against the session token using a constant-time comparison.
    """
    expected = session.get("csrf_token")
    if not expected:
        return False

    provided = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
    if not provided:
        return False
    return secrets.compare_digest(expected, provided)


def csrf_required(func):
    """Decorator: reject state-changing requests without a valid CSRF token."""

    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.method in MUTATING_METHODS and not csrf_protect():
            if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify(error="Invalid or missing CSRF token."), 400
            return "Invalid or missing CSRF token.", 400
        return func(*args, **kwargs)

    return wrapper


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,20}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def valid_username(username: str) -> bool:
    return bool(username and USERNAME_RE.match(username))


def valid_email(email: str) -> bool:
    return bool(email and len(email) <= 120 and EMAIL_RE.match(email))


def valid_password(password: str) -> bool:
    return bool(password) and len(password) >= 6


def sanitize_text(value: str, max_len: int = 500) -> str:
    """Trim and cap length. Used before storing user-provided text."""
    value = (value or "").strip()
    return value[:max_len]
