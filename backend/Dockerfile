FROM python:3.10-slim

WORKDIR /app

RUN python -m pip install --upgrade pip

COPY requirements.txt .

RUN python -m pip install -r requirements.txt

COPY . .

EXPOSE 8000

COPY ./start_backend.sh /app/start_backend.sh
RUN chmod +x /app/start_backend.sh
ENTRYPOINT ["/app/start_backend.sh"]
