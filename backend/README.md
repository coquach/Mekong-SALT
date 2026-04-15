# Mekong-SALT Backend

Backend MVP scope includes:

- FastAPI modular monolith with versioned APIs
- environment-based config with Pydantic v2 settings
- async SQLAlchemy + Redis integration
- authentication disabled for MVP demo
- sensor ingestion + risk evaluation + incident creation
- AI planning orchestration (mock + provider abstractions)
- reactive approval + simulated execution orchestration
- goal-driven active monitoring worker with Redis locks enabled by default
- notifications (dashboard + SMS/Zalo/email mock)
- audit logging and outcomes
- dashboard summary + SSE stream
- shared logging, middleware, exceptions, and response envelope
- Alembic migrations for PostgreSQL + pgvector
- Docker Compose local infrastructure for PostgreSQL and Redis
- seed script with demo data

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

The active monitoring worker is the default runtime path. When
`ACTIVE_MONITORING_ENABLED=true` and `ACTIVE_MONITORING_MODE=active`, the API
process continuously runs due monitoring goals and advances valid plans through
reactive approval and simulated execution.

Standalone worker:

```bash
./.venv/Scripts/python.exe -m app.workers.active_monitoring_worker
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

Authentication is disabled for MVP demo.

## Sample curl

```bash
curl http://localhost:8000/api/v1/health
```

## Reactive Flow

1. Ingest a sensor reading: `POST /api/v1/sensors/ingest`
2. Create or update a monitoring goal: `POST /api/v1/goals`, `PATCH /api/v1/goals/{goal_id}`
3. Worker observes due goals and runs `observe -> risk -> incident -> plan`
4. Valid plans are approved by `reactive-monitoring`
5. Approved plans execute through the simulated action engine
6. Watch state: `GET /api/v1/dashboard/summary`, `GET /api/v1/dashboard/stream`, `GET /api/v1/risk/latest`, `GET /api/v1/plans`, `GET /api/v1/actions/logs`

Manual trigger endpoints for risk evaluation, plan generation, approval, and
action execution are no longer public API. The public API configures goals and
reads state; the worker owns side-effecting decisions.

## Folder Layout

- `app/api`: versioned HTTP routes and response presenters.
- `app/orchestration`: cross-domain workflows such as reactive plan advancement.
- `app/services`: domain services for risk, planning, execution, goals, and incidents.
- `app/repositories`: persistence queries around SQLAlchemy models.
- `app/workers`: long-running background loops.
- `app/agents`: provider adapters and policy/graph logic.
- `app/schemas` and `app/models`: API contracts and persistence models.

## Monitoring Goals

- `POST /api/v1/goals`: create goal with `thresholds`, `evaluation_interval_minutes`, and `is_active`.
- `auto_plan_enabled`: lets the worker create a plan automatically in active mode.
- `GET /api/v1/goals` and `GET /api/v1/goals/{goal_id}`: read goals.
- `PATCH /api/v1/goals/{goal_id}`: update thresholds, interval, active flag, objective, target.
- `DELETE /api/v1/goals/{goal_id}`: remove goal.

Data constraints are enforced at both API and database levels:

- `critical_threshold_dsm > warning_threshold_dsm`
- `evaluation_interval_minutes >= 1`
- `is_active` controls whether the worker evaluates the goal.

## Active Monitoring Worker

Worker loop:

1. Load active monitoring goals.
2. Skip goals whose `last_run_at + evaluation_interval_minutes` is still in the future.
3. Acquire `mekong-salt:monitoring-goal:{goal_id}:lock` in Redis.
4. Run `observe -> risk -> incident`.
5. In `dry_run`, stop before plan creation.
6. In `active`, create a plan only when `auto_plan_enabled=true` and no active/simulated plan exists for the incident.
7. If enabled, auto-approve and execute the plan using the simulated action engine.

Useful commands:

```bash
alembic upgrade head
pytest app/tests/test_active_monitoring_worker.py app/tests/test_agent_run_trace.py
```

## Agent Runs + Observation Snapshots (Phase 3)

- `agent_runs`: one record per risk/plan run with `status`, `trigger_source`, `payload`, and decision `trace`.
- `observation_snapshots`: pre-decision observation payload linked 1:1 to `agent_runs`.

Trace APIs:

- `GET /api/v1/agent/runs`: list recent runs.
- `GET /api/v1/agent/runs/{run_id}`: inspect one run with snapshot and decision trace.

Trace fields:

- `monitoring.worker.observe_risk`: risk observation run.
- `monitoring.worker.auto_plan`: plan generation run.
- `reactive-monitoring`: approval/execution actor for automated plan advancement.
