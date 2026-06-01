# Shared image for all three services + the worker. The compose file overrides
# the command per service. Runs as a non-root user.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install the shared package, then the service code.
COPY common ./common
RUN pip install --no-cache-dir ./common
COPY gateway ./gateway
COPY backend ./backend
COPY worker ./worker

# Non-root user.
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

# Default command is overridden per service in docker-compose.yml.
CMD ["python", "gateway/app.py"]
