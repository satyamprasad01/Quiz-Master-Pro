"""Quiz Master Pro - Flask application entry point.

Run with:
    python app.py

Then open http://127.0.0.1:5000
Default admin account (created on first run): admin / admin123
"""

import os
from pathlib import Path

from flask import Flask, render_template

from models.db import init_app as init_db
from routes import register_blueprints
from utils.security import generate_csrf_token

BASE_DIR = Path(__file__).resolve().parent


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-me-in-production"),
        DATABASE=str(BASE_DIR / "database.db"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 7,  # 7 days
    )
    if test_config:
        app.config.update(test_config)

    # Make the CSRF token available to every template.
    @app.context_processor
    def inject_csrf():
        import datetime

        return {"csrf_token": generate_csrf_token(), "now_year": datetime.date.today().year}

    # Template filters used by the dashboard / result pages.
    from models import questions as question_model

    @app.template_filter("category_color")
    def category_color_filter(name):
        cat = question_model.get_category(name)
        return cat["color"] if cat else "#6366f1"

    @app.template_filter("category_icon")
    def category_icon_filter(name):
        cat = question_model.get_category(name)
        return cat["icon"] if cat else "fa-question"

    # Friendly error pages.
    @app.errorhandler(404)
    def not_found(_e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(_e):
        return render_template("500.html"), 500

    init_db(app)
    register_blueprints(app)

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
