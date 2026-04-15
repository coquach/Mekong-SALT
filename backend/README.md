# Mekong-SALT Backend

Backend MVP scope includes:

- FastAPI modular monolith with versioned APIs
- environment-based config with Pydantic v2 settings
- async SQLAlchemy + Redis integration
- authentication disabled for MVP demo
- sensor ingestion + risk evaluation + incident creation
- AI planning orchestration (mock + provider abstractions)
- approval workflow and simulated execution
- goal-driven active monitoring worker with Redis locks
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

The active monitoring worker is off by default. To run it inside the API
process, set `ACTIVE_MONITORING_ENABLED=true`. Start with
`ACTIVE_MONITORING_MODE=dry_run`, then switch to `active` only after the worker
has completed stable cycles.

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

## Demo flow (MVP)

1. Ingest a sensor reading: `POST /api/v1/sensors/ingest`
2. Evaluate risk: `GET /api/v1/risk/current`
3. Create a monitoring goal: `POST /api/v1/goals`
4. Run one goal cycle to create plan: `POST /api/v1/goals/{goal_id}/run-once`
5. Update goal config: `PATCH /api/v1/goals/{goal_id}`
6. List current goals: `GET /api/v1/goals`
7. Approve plan: `POST /api/v1/approvals/plans/{plan_id}`
8. Execute (mock): `POST /api/v1/agent/execute-simulated`
9. Watch dashboard: `GET /api/v1/dashboard/summary` or `GET /api/v1/dashboard/stream`

## Monitoring Goals (Phase 2)

- `POST /api/v1/goals`: create goal with `thresholds`, `evaluation_interval_minutes`, and `is_active`.
- `auto_plan_enabled`: lets the worker create a pending-approval plan automatically in active mode.
- `GET /api/v1/goals` and `GET /api/v1/goals/{goal_id}`: read goals.
- `PATCH /api/v1/goals/{goal_id}`: update thresholds, interval, active flag, objective, target.
- `DELETE /api/v1/goals/{goal_id}`: remove goal.
- `POST /api/v1/goals/{goal_id}/run-once`: trigger one immediate cycle using persisted goal configuration.

Data constraints are enforced at both API and database levels:

- `critical_threshold_dsm > warning_threshold_dsm`
- `evaluation_interval_minutes >= 1`
- `is_active` is required and controls whether run-once is allowed.

## Active Monitoring Worker (Phase 4)

Worker loop:

1. Load active monitoring goals.
2. Skip goals whose `last_run_at + evaluation_interval_minutes` is still in the future.
3. Acquire `mekong-salt:monitoring-goal:{goal_id}:lock` in Redis.
4. Run `observe -> risk -> incident`.
5. In `dry_run`, stop before plan creation.
6. In `active`, create a plan only when `auto_plan_enabled=true` and no non-terminal plan exists for the incident.

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

Compatibility and trace fields:

- Legacy `POST /api/v1/agent/plan` is available again for existing clients.
- `GET /api/v1/risk/current` returns `agent_run_id`.
- `POST /api/v1/alerts/evaluate` returns `agent_run_id`.
- Plan generation responses include `agent_run_id` when available.
