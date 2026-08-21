#!/bin/sh
set -e

echo "==> Running database migrations with Alembic..."
alembic upgrade head

echo "==> Starting application server..."
exec "$@"
