docker run  -d\
  --name softice01/foodgram-backend \
  --rm \
  -v static:/backend_static/static \
  -v media:/media \
  --net django-network \
  softice01/foodgram-backend:latest
