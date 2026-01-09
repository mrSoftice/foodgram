#!/bin/bash

cd ~/foodgram

echo "Collect static files..."
docker compose -f docker-compose.production.yml --verbose exec backend python manage.py collectstatic --no-input
# docker compose -f ./docker-compose.yml --verbose exec backend python manage.py collectstatic --no-input
