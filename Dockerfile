FROM python:3.11-slim

ENV KERAS_BACKEND=tensorflow \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

WORKDIR /app
COPY webapp/requirements-web.txt .
RUN pip install --no-cache-dir -r requirements-web.txt

COPY webapp/ .

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
  CMD python -c "import json, urllib.request; data=json.load(urllib.request.urlopen('http://127.0.0.1:5000/api/health', timeout=3)); raise SystemExit(0 if data.get('model_ready') else 1)"

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "2", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
