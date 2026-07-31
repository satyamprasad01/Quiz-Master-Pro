"""Route blueprints for Quiz Master Pro."""

from .admin import admin
from .api import api
from .auth import auth
from .main import main
from .quiz import quiz


def register_blueprints(app) -> None:
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(quiz)
    app.register_blueprint(api)
    app.register_blueprint(admin)
