docker run  -d\
  --name foodgram_backend \
  --rm \
  -v static:/backend_static/static \
  -v media:/media \
  --net django-network \
  foodgram_backend:latest
