"""Entry point. Locally: `python run.py`. In Docker, gunicorn loads `run:app`."""
from app import create_app

# gunicorn looks for this variable named "app"
app = create_app()

if __name__ == "__main__":
    # Development server only (debug=True auto-reloads on code changes)
    app.run(port=5000, debug=True)
