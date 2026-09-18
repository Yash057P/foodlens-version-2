FROM python:3.11-slim

ENV KERAS_BACKEND=tensorflow
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY webapp/requirements-web.txt .
RUN pip install --no-cache-dir -r requirements-web.txt tensorflow-cpu

COPY webapp/ .

EXPOSE 5000
CMD ["python", "app.py"]
