#!/bin/sh

echo "Starting Foodgram backend..."

python manage.py migrate --no-input

gunicorn -w 4 -t 600 --bind 0:8000 foodgram.wsgi
