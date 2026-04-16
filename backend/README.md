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

## Current Orchestration Flow

1. Observe: ingest and monitor readings (`/sensors/ingest`, `/goals/*`, worker tick).
2. Assess risk: deterministic risk evaluation and incident decision.
3. Retrieve context (RAG): gather SOP/threshold/similar-case evidence before drafting.
4. Generate AI plan (Vertex Gemini) and validate plan with deterministic policy rules.
5. Classify risk and branch approval gate: high risk waits for human decision, low risk may auto-approve.
6. Execute simulated actions and emit milestone notifications.
7. Evaluate outcome from post-action observations and persist memory case evidence for re-planning.
8. Stream operational updates via dashboard SSE + durable domain event cursor.

Watch state:

- `GET /api/v1/dashboard/summary`
- `GET /api/v1/dashboard/stream`
- `GET /api/v1/risk/latest`
- `GET /api/v1/plans`
- `GET /api/v1/actions/logs`

Manual trigger endpoints for risk evaluation, plan generation, approval, and
action execution are no longer public API. The public API configures goals and
reads state; the worker owns side-effecting decisions.

Approval and feedback boundaries:

- `POST /api/v1/approvals/plans/{plan_id}/decision` is active (records approval/rejection).
- `GET /api/v1/approvals/plans/{plan_id}/history` is active.
- `POST /api/v1/feedback/execution-batches/{batch_id}/evaluate` remains a contract placeholder (501).
- `GET /api/v1/feedback/execution-batches/{batch_id}/latest` remains a contract placeholder (501).

## Operational API Boundaries

| Endpoint group | Owner module | Responsibility | Status |
|---|---|---|---|
| `/health` | `app.services.health_service` | service readiness metadata | stable |
| `/goals` | `app.services.goals_service` | configure monitoring automation scope | stable |
| `/incidents` | `app.services.incident_service` | manual incident lifecycle management | stable |
| `/plans` | `app.repositories.action` (read) | plan visibility for operators and FE | stable |
| `/execution-batches`, `/action-outcomes` | `app.services.agent_execution_service` | simulated execution transaction view | stable |
| `/actions/logs` | `app.services.agent_execution_service` | execution + decision log timeline | stable |
| `/notifications` | `app.services.notification_service` | dashboard/SMS/Zalo/email mock records | stable |
| `/agent/*`, `/audit/*` | `app.services.agent_trace_service`, `app.services.audit_service` | traceability and auditability | stable |
| `/dashboard/*` | `app.services.dashboard_service` | operational summary and timeline stream | stable |
| `/approvals/*` | `app.services.approval_service` | HITL approval workflow and decision history | active |
| `/feedback/*` | `app.services.feedback` (planned) | post-execution evaluation contracts | placeholder |

## Canonical API Boundaries

- Sensor ingestion: `/api/v1/sensors/ingest`
- Reading queries: `/api/v1/readings/*` (canonical read surface)
- Plan queries: `/api/v1/plans/*` (canonical plan read surface)
- Agent observability only: `/api/v1/agent/runs*`
- Operational lifecycle: `/api/v1/incidents`, `/api/v1/approvals`, `/api/v1/execution-batches`, `/api/v1/actions/logs`, `/api/v1/notifications`

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

## Vertex Vector Search RAG (Phase 1)

Planning context retrieval is now Vertex-first when `RAG_USE_VERTEX_VECTOR_SEARCH=true`.
The workflow embeds query text with Vertex, searches your deployed Vertex index,
maps returned datapoint IDs to local chunk records, and injects ranked evidence
into `retrieved_context.knowledge_context` before plan generation.

Grounding contract in `knowledge_context`:

- `evidence_source`
- `score`
- `snippet`
- `citation`
- `metadata_filters` with `region`, `station`, `severity`, `crop`, `time`

Required environment variables:

- `VERTEX_AI_PROJECT`
- `VERTEX_AI_LOCATION`
- `VERTEX_VECTOR_SEARCH_INDEX`
- `VERTEX_VECTOR_SEARCH_INDEX_ENDPOINT`
- `VERTEX_VECTOR_SEARCH_DEPLOYED_INDEX_ID`
- `RAG_EMBEDDING_MODEL` (default `text-embedding-005`)

Optional controls:

- `RAG_USE_VERTEX_VECTOR_SEARCH=true`
- `RAG_ENABLE_LOCAL_FALLBACK=true`
- `RAG_RETRIEVAL_TOP_K=8`
- `RAG_CSV_REINDEX_TTL_DAYS=7`

Ingest document/CSV sources into DB + Vertex index:

```bash
./.venv/Scripts/python.exe scripts/ingest_rag_source.py \
	"./document/salinity_thresholds.csv" \
	--document-type threshold \
	--tags "threshold,salinity,policy"
```

Ingest bundled sample docs (SOP + threshold + casebook + weather guidance):

```bash
./.venv/Scripts/python.exe scripts/ingest_rag_samples.py
```

Sample files are stored under `document/rag_samples/`.

Supported ingestion formats in Phase 1:

- `txt`, `md`, `rst`, `json`, `yaml`, `yml`, `log`
- `csv` (row-aware normalization)
- `docx` (requires `python-docx`)

Governance behavior:

- Document versioning by `source_key` + `effective_date` in `metadata_payload`.
- CSV TTL re-index checks based on `RAG_CSV_REINDEX_TTL_DAYS` and `last_indexed_at`.
- Re-index cleanup removes stale datapoints from Vertex index before upserting new chunks.
- Retrieval traces are logged into planning observation snapshots and plan audit payloads.

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
