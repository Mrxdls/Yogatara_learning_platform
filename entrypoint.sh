#!/bin/bash

set -e

# Wait for PostgreSQL
while ! python -c "import socket; socket.create_connection(('$DB_HOST', $DB_PORT), timeout=1)" >/dev/null 2>&1; do
  sleep 1
done

# Run migrations
python manage.py migrate --noinput

# Create superuser
DJANGO_SUPERUSER_USERNAME=$SUPERUSER_USERNAME \
DJANGO_SUPERUSER_PASSWORD=$SUPERUSER_PASSWORD \
DJANGO_SUPERUSER_EMAIL=$SUPERUSER_EMAIL \
python manage.py createsuperuser --noinput --skip-checks 2>/dev/null || true

# Collect static files
python manage.py collectstatic --noinput

if [ "$1" = "gunicorn" ]; then
    echo "Starting Gunicorn..."
    gunicorn \
        --bind 0.0.0.0:8000 \
        --workers 4 \
        --worker-class sync \
        --worker-tmp-dir /dev/shm \
        --access-logfile - \
        --error-logfile - \
        --log-level info \
        Learning_hub.wsgi:application
elif [ "$1" = "celery" ]; then
    echo "Starting Celery Worker..."
    celery -A Learning_hub worker -l info --concurrency=4
elif [ "$1" = "celery-beat" ]; then
    echo "Starting Celery Beat..."
    celery -A Learning_hub beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
else
    exec "$@"
fi
