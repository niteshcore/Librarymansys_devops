"""App factory: builds and configures the Library Management System."""
import os

from flask import Flask

from . import models
from .routes import bp

# Project root folder (one level above this "app" package)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_app(config=None):
    # Create the Flask application object
    app = Flask(__name__)

    # Settings can be changed with environment variables (useful in Docker)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    app.config["DATABASE"] = os.environ.get(
        "DATABASE_PATH", os.path.join(BASE_DIR, "data", "library.db")
    )

    # Tests pass their own settings here (for example a temporary database)
    if config:
        app.config.update(config)

    # Make sure the folder that holds the SQLite file exists
    os.makedirs(os.path.dirname(os.path.abspath(app.config["DATABASE"])), exist_ok=True)

    # Close the database connection automatically after every request
    app.teardown_appcontext(models.close_db)

    # Create the books table on startup if it does not exist yet
    with app.app_context():
        models.init_db()

    # Attach all our URL routes (defined in routes.py)
    app.register_blueprint(bp)

    return app
