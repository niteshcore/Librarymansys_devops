# Start from the small official Python 3.11 image
FROM python:3.11-slim

# Don't create .pyc files, and print logs immediately (no buffering)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Every command below runs inside the /app folder in the container
WORKDIR /app

# Copy ONLY requirements.txt first, then install packages.
# Docker caches this layer, so packages are reinstalled only when requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the application code (.dockerignore decides what gets copied)
COPY . .

# Create a normal user (not root) and a data folder it is allowed to write to
RUN useradd --create-home appuser \
    && mkdir -p /app/data \
    && chown appuser:appuser /app/data

# Run the app as that user, so a bug in the app cannot control the whole container
USER appuser

# Document that the app listens on port 5000
EXPOSE 5000

# Start gunicorn (a production web server) with 2 workers, loading "app" from run.py
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "run:app"]
