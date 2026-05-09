#!/bin/sh
set -e

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting Event Service..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${SERVICE_PORT:-8002}" \
    --workers 1 \
    --timeout-graceful-shutdown 30
