#!/bin/bash
set -e

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-6543}"
WORKERS="${WORKERS:-2}"
APP_MODULE="${APP_MODULE:-app.main:app}"

if [ "$ENV" = "development" ]; then
    echo "Running in development mode with reload"
    exec uv run uvicorn "$APP_MODULE" --host "$HOST" --port "$PORT" --reload --timeout-keep-alive 1200
else
    echo "Running in production mode"
    exec uv run uvicorn "$APP_MODULE" --host "$HOST" --port "$PORT" --workers "$WORKERS" --timeout-keep-alive 1200
fi
