"""Database connection management.

A single SQLite connection is stored on the Flask ``g`` object per request
and closed automatically when the request finishes.
"""

import sqlite3

from flask import current_app, g


def get_db() -> sqlite3.Connection:
    """Return a per-request SQLite connection."""
    if "db" not in g:
        db_path = current_app.config["DATABASE"]
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


def close_db(_exc=None) -> None:
    """Close the per-request connection."""
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_app(app) -> None:
    """Initialise the database and register teardown."""
    from database.seed import init_db

    with app.app_context():
        conn = get_db()
        try:
            init_db(conn)
        finally:
            close_db()
    app.teardown_appcontext(close_db)
