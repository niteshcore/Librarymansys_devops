import os

from flask import Flask

from . import models
from .routes import bp

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_app(config=None):
    app = Flask(__name__)

    # Settings come from environment variables, so Docker can change them
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    app.config["DATABASE"] = os.environ.get(
        "DATABASE_PATH", os.path.join(BASE_DIR, "data", "library.db")
    )

    # Tests pass their own settings here, e.g. a temporary database
    if config:
        app.config.update(config)

    os.makedirs(os.path.dirname(os.path.abspath(app.config["DATABASE"])), exist_ok=True)

    app.teardown_appcontext(models.close_db)

    with app.app_context():
        models.init_db()

    app.register_blueprint(bp)

    return app
