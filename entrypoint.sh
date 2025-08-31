#!/bin/sh

set -e

#Wait for PostgreSQL
until pg_isready -h "$DB_HOST" -p "$DB_PORT" >/dev/null 2>&1; do
  sleep 1
done

# Migrations
python manage.py migrate --noinput

# Superuser
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
import os

User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        username=os.environ.get("DJANGO_SUPERUSER_USERNAME"),
        email=os.environ.get("DJANGO_SUPERUSER_EMAIL"),
        password=os.environ.get("DJANGO_SUPERUSER_PASSWORD")
    )
EOF

echo "Upload recipes..."
python manage.py load_data

echo "Starting server..."
gunicorn django_recipe_generator.wsgi:application --bind 0.0.0.0:8000 --timeout 120 --access-logfile -
#uv run manage.py runserver 0.0.0.0:8000
