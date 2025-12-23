#!/bin/bash

cd ~/foodgram

echo "Collect static files..."
# docker compose -f docker-compose.production.yml --verbose exec backend python manage.py collectstatic --no-input
docker compose -f ./infra/docker-compose.yml --verbose exec backend python manage.py collectstatic --no-input

echo "Copy them to volume..."
# docker compose -f docker-compose.production.yml -- verbose exec backend sh -c "cp -r --verbose /app/collected_static/. /backend_static/static/"
docker compose -f ./infra/docker-compose.yml -- verbose exec backend sh -c "cp -r --verbose /app/collected_static/. /backend_static/static/"
