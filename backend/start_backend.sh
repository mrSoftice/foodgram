#!/bin/sh

echo "Starting Foodgram backend..."

python manage.py migrate

# Collect static files
# python manage.py collectstatic --no-input
# cp -r --verbose /app/collected_static/. /backend_static/static/

gunicorn -w 4 -t 600 --bind 0:8000 foodgram.wsgi
