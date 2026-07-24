# PDF p.16 Dockerfile, extended only with EXPOSE + a reports volume mount point.
FROM python:3.13-slim

# Build-time dependencies for asyncpg / bcrypt compilation wheels are already
# shipped as binary wheels for cp313, so we keep the image slim.
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Reports written by the Celery worker land here.
RUN mkdir -p /app/reports

EXPOSE 8080

# The compose file overrides command for the celery-worker service.
# Run as a module so relative imports inside the `app` package resolve.
CMD ["python", "-m", "app.app"]
