# Mekong-SALT Backend

Phase 1 provides the backend foundation only:

- FastAPI bootstrap with structured `app/` modules
- environment-based config with Pydantic v2 settings
- async SQLAlchemy and Redis placeholders
- shared logging, middleware, exceptions, and response envelope
- Alembic baseline for PostgreSQL + pgvector
- Docker Compose local infrastructure for PostgreSQL and Redis
- basic smoke test and seed script

## Local setup

```bash
py -3.13 -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env
```

Python 3.11+ is required. On this machine, `py -3.13` is the correct interpreter to use.

## Start local infrastructure

```bash
docker compose up -d postgres redis
```

## Run locally

```bash
./.venv/Scripts/python.exe -m uvicorn main:app --reload

```

## Optional: run backend in Docker too

```bash
docker compose --profile app up --build
```

## Apply migrations

```bash
alembic upgrade head
```

## Seed

```bash
python scripts/seed.py
```

## Sample curl

```bash
curl http://localhost:8000/api/v1/health
```
