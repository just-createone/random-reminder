FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./requirements.txt

RUN python -m pip install \
    --no-cache-dir \
    -r requirements.txt

COPY backend ./backend
COPY frontend ./frontend

EXPOSE 8000

CMD ["python", "-m", "backend.run"]