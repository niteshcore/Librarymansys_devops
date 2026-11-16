from app import create_app

# gunicorn in Docker loads this object ("run:app")
app = create_app()

if __name__ == "__main__":
    app.run(port=5000, debug=True)
