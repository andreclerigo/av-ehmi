FROM python:3.11-slim AS base

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5003

CMD ["gunicorn", "app:app", "--worker-class", "eventlet", "--workers", "1", "--bind", "0.0.0.0:5003", "--capture-output", "--log-level", "info"]
