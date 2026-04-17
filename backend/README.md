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
- Docker Compose runtime topology for PostgreSQL, Redis, MQTT, backend API, and frontend
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
docker compose up -d
```

The compose topology already includes `postgres`, `redis`, `mqtt`, `backend`,
and `frontend`. For the hackathon demo, keep these defaults in place:

- `IOT_INGEST_MODE=mqtt`
- `MQTT_ENABLED=true`
- `PUBSUB_ENABLED=false`
- `EARTH_ENGINE_ENABLED=false`
- `ACTIVE_MONITORING_ENABLED=true`
- `ACTIVE_MONITORING_MODE=active`

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

Device-first MQTT demo mode (subscriber runs inside API process):

```bash
IOT_INGEST_MODE=mqtt
MQTT_ENABLED=true
MQTT_BROKER_URL=localhost
MQTT_BROKER_PORT=1883
MQTT_TOPIC_SENSOR_READINGS=mekong/sensors/readings
MQTT_TOPIC_DEVICE_STATUS=mekong/sensors/status
MQTT_TOPIC_DEAD_LETTER=mekong/sensors/readings/dlq
IOT_DLQ_ARCHIVE_ENABLED=true
IOT_DLQ_ARCHIVE_PATH=artifacts/ingest_dlq_archive.jsonl

PUBSUB_ENABLED=false
EARTH_ENGINE_ENABLED=false
ACTIVE_MONITORING_ENABLED=true
ACTIVE_MONITORING_MODE=active
```

Run device-first MQTT scenario stream:

```bash
./.venv/Scripts/python.exe scripts/run_demo_simulation.py \
  --scenario fast-approve-execute \
  --transport mqtt \
  --mqtt-broker-url localhost \
  --mqtt-broker-port 1883
```

For hackathon demo, prefer MQTT as the primary device path and keep HTTP only as a fallback for local debugging:

```bash
./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario fast-approve-execute
```

The demo story should be presented as:

device/gateway -> MQTT broker -> backend worker -> shared ingest service -> risk/plan/approval/execution -> dashboard

Demo UI (Gradio control center):

```bash
./.venv/Scripts/python.exe gradio_app/demo_app.py
```

Open `http://127.0.0.1:7860` to run scenarios and monitor plans/runs in one screen.

## Run full stack in Docker Compose

```bash
docker compose up -d
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

Integration rollout plan:

- `document/phase-rollout-pubsub-mqtt-gee-frontend.md`
- `document/demo-runbook-5-phut.md`

Watch state:

- `GET /api/v1/dashboard/summary`
- `GET /api/v1/dashboard/stream`
- `GET /api/v1/dashboard/earth-engine/latest`
- `GET /api/v1/risk/latest`
- `GET /api/v1/plans`
- `GET /api/v1/actions/logs`

Manual trigger endpoints for risk evaluation, plan generation, approval, and
action execution are no longer public API. The public API configures goals and
reads state; the worker owns side-effecting decisions.

Approval and feedback boundaries:

- `POST /api/v1/approvals/plans/{plan_id}/decision` is active (records approval/rejection).
- `GET /api/v1/approvals/plans/{plan_id}/history` is active.
- `POST /api/v1/feedback/execution-batches/{batch_id}/evaluate` is active (persists lifecycle evaluation).
- `GET /api/v1/feedback/execution-batches/{batch_id}/latest` is active.

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
| `/feedback/*` | `app.services.feedback` | post-execution lifecycle evaluation | active |

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
- Goal thresholds now accept either:
	- `warning_threshold_dsm` + `critical_threshold_dsm` (canonical)
	- `warning_threshold_gl` + `critical_threshold_gl` (auto-converted to dS/m)
- `auto_plan_enabled`: lets the worker create a plan automatically in active mode.
- `GET /api/v1/goals` and `GET /api/v1/goals/{goal_id}`: read goals.
- `PATCH /api/v1/goals/{goal_id}`: update thresholds, interval, active flag, objective, target.
- `DELETE /api/v1/goals/{goal_id}`: remove goal.

Data constraints are enforced at both API and database levels:

- `critical_threshold_dsm > warning_threshold_dsm`
- `evaluation_interval_minutes >= 1`
- `is_active` controls whether the worker evaluates the goal.

## Salinity Unit Policy

The backend canonical unit is `dS/m` for storage, rules, and comparisons.
For proposal/business communication, API responses additionally expose equivalent `g/L`.

- Conversion factor: `1 dS/m ~= 0.64 g/L`
- Risk-rule thresholds (canonical):
	- safe: `< 1.00 dS/m` (`~< 0.64 g/L`)
	- warning: `>= 1.00` and `< 2.50 dS/m` (`~0.64-1.59 g/L`)
	- danger: `>= 2.50` and `< 4.00 dS/m` (`~1.60-2.55 g/L`)
	- critical: `>= 4.00 dS/m` (`~>= 2.56 g/L`)

This normalization removes ambiguity between proposal narratives (`g/L`) and backend rules (`dS/m`).

## Active Monitoring Worker

Worker loop:

1. Load active monitoring goals.
2. Skip goals whose `last_run_at + evaluation_interval_minutes` is still in the future.
3. Acquire `mekong-salt:monitoring-goal:{goal_id}:lock` in Redis.
4. Run `observe -> risk -> incident`.
5. In `dry_run`, stop before plan creation.
6. In `active`, create a plan only when `auto_plan_enabled=true` and no active plan exists for the incident.
7. If enabled, auto-approve and execute the plan using the simulated action engine.
8. If feedback outcome is failed/partial, optionally auto-replan for limited attempts.

Approval timeout controls:

- `ACTIVE_MONITORING_APPROVAL_TIMEOUT_MINUTES`: pending approvals older than this window are considered stale.
- `ACTIVE_MONITORING_APPROVAL_TIMEOUT_ACTION=auto_reject|none`: `auto_reject` rejects stale pending plans so the next cycle can generate a fresh plan.
- For demos, set timeout to `1` minute to observe the recovery path quickly.

Feedback replan controls:

- `ACTIVE_MONITORING_FEEDBACK_REPLAN_MAX_ATTEMPTS`: maximum follow-up replans in the same goal cycle after failed feedback outcomes.
- Failed outcomes eligible for auto-replan: `failed_execution`, `failed_plan`, `partial_success`.
- `inconclusive` feedback does not auto-replan to avoid loops when no new reading is available.

Useful commands:

```bash
alembic upgrade head
pytest app/tests/test_active_monitoring_worker.py app/tests/test_agent_run_trace.py
```

## Vertex Vector Search RAG (Phase 1)

Detailed operations guide: `document/rag-operations-guide.md`

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
- `RAG_STATIC_CORPUS_PROVIDER=vector_search|vertex_rag_engine_adapter`
- `RAG_RETRIEVAL_TOP_K=8`
- `RAG_CSV_REINDEX_TTL_DAYS=7`

Note:

- `vertex_rag_engine_adapter` currently runs through a dedicated adapter boundary and still uses
	Vertex Vector Search as the backing data plane (transitional mode), while exposing
	corpus-provider provenance in retrieval output.

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

Sample files are stored under `document/rag_samples/` with categorized subfolders:

- `document/rag_samples/sop/`
- `document/rag_samples/threshold/`
- `document/rag_samples/casebook/`
- `document/rag_samples/guideline/`

Supported ingestion formats in Phase 1:

- `txt`, `md`, `rst`, `json`, `yaml`, `yml`, `log`
- `csv` (row-aware normalization)
- `docx` (requires `python-docx`)
- `pdf` (requires `pypdf`)

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
