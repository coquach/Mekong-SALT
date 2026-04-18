FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --upgrade pip

COPY backend/pyproject.toml backend/README.md backend/alembic.ini backend/main.py ./backend/
COPY backend/app ./backend/app
COPY backend/alembic ./backend/alembic
COPY backend/scripts ./backend/scripts

WORKDIR /app/backend

RUN pip install .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]