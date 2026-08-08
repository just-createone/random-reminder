FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./requirements.txt

RUN python -m pip install \
    --no-cache-dir \
    -r requirements.txt

RUN groupadd \
        --gid 10001 \
        app \
    && useradd \
        --uid 10001 \
        --gid app \
        --no-create-home \
        --home-dir /app \
        --shell /usr/sbin/nologin \
        app

COPY backend ./backend
COPY frontend ./frontend
COPY scripts ./scripts

RUN mkdir -p \
        /app/data \
        /app/backups \
        /app/secrets/vapid \
    && chown -R \
        app:app \
        /app

USER app:app

EXPOSE 8000

CMD ["python", "-m", "backend.run"]
