docker run -d \
  --name foodgram-proxy \
  --rm \
  -p 80:80 \
  -v static:/usr/share/nginx/html/static \
  -v media:/usr/share/nginx/html/media \
  nginx:1.25.4-alpine
