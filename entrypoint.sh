#!/bin/sh

echo "Running migrations..."
python manage.py migrate

echo "Upload recipes..."
python manage.py loaddata datadump.json

echo "Starting server..."
gunicorn django_recipe_generator.wsgi:application --bind 0.0.0.0:8000 --timeout 120