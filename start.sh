#!/bin/bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1

echo "🚀 启动应用"

if ! command -v uv >/dev/null 2>&1; then
    python -m pip install -U uv
fi

uv sync
uv run python manage.py makemigrations

uv run python manage.py migrate
uv run python manage.py collectstatic --noinput
uv run python manage.py buildwatson

uv run celery -A Rosetta worker -l info &
celery_pid=$!
trap "kill ${celery_pid} 2>/dev/null || true" TERM INT EXIT

uv run uvicorn Rosetta.asgi:application \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --proxy-headers \
    --log-level info
