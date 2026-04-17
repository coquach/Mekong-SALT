# Phase Rollout: Pub/Sub + MQTT + Earth Engine + Frontend

Updated: April 17, 2026

## Goal

Roll out real IoT ingestion and spatial intelligence on top of the current backend lifecycle (risk -> plan -> approval -> execution -> feedback), while incrementally upgrading the existing Next.js frontend.

## Current Baseline

- Backend already supports canonical HTTP ingest (`/api/v1/sensors/ingest`) and active monitoring worker.
- Agentic lifecycle is operational with approval gate and simulated execution.
- Frontend is currently scaffolded (Next.js starter), not yet wired to dashboard/risk workflows.

## Phase 0: Foundation Hardening (1-2 weeks)

Scope:
- Keep current HTTP ingest as fallback path.
- Add feature flags/config for MQTT, Pub/Sub, Earth Engine.
- Define canonical event schema for sensor reading payloads.

Deliverables:
- Environment keys in `backend/.env.example`.
- Runbook and rollout gates for each integration feature.
- Contract for dedup/idempotency (`station_code + recorded_at + source_event_id`).

Done criteria:
- App boots with all new flags disabled by default.
- No behavior change for existing demo scenarios.

## Phase 1: MQTT Edge Ingest (2 weeks)

Scope:
- Add MQTT subscriber worker for edge gateways/devices.
- Map incoming MQTT payloads to existing sensor ingestion schema.
- Add dead-letter strategy for malformed payloads.

Deliverables:
- MQTT consumer service (background task) with reconnect/backoff.
- Topic conventions:
  - `mekong/sensors/readings`
  - `mekong/sensors/status`
- Basic device observability: ingest success/fail counters.

Done criteria:
- MQTT messages produce persisted readings and appear in `/readings/latest`.
- Duplicate messages do not create duplicate readings.

## Phase 2: Pub/Sub Stream Ingest (2 weeks)

Scope:
- Add GCP Pub/Sub subscriber for cloud streaming channel.
- Support dual ingest mode (`mqtt` + `pubsub`) via feature flags.
- Introduce ingest lag monitoring and retry control.

Deliverables:
- Pub/Sub subscriber worker and parser.
- Dead-letter topic integration.
- Health metrics:
  - queue lag
  - parse failure count
  - commit success count

Done criteria:
- End-to-end stream from Pub/Sub to risk pipeline works in staging.
- Worker remains stable under burst load and message retries.

## Phase 3: Earth Engine Spatial Context (2-3 weeks)

Scope:
- Add Earth Engine adapter for satellite-derived contextual signals.
- Generate region/station-level spatial summaries for planning context.
- Keep current weather API fallback for resilience.

Deliverables:
- Earth Engine service boundary (no direct coupling into core logic).
- Derived context fields injected into planning retrieval payload:
  - vegetation/soil-water proxy
  - surface water mask trend
  - region anomaly summary
- Caching policy for Earth Engine queries.

Done criteria:
- Planning run traces show Earth Engine context when enabled.
- If Earth Engine fails, lifecycle still proceeds with fallback context.

## Phase 4: Frontend Integration on Existing Next App (2 weeks)

Scope:
- Build operational UI on top of current Next.js app (not rewrite).
- Wire backend APIs for dashboard, timeline, approvals, executions.
- Add map layer and event stream panels.

Deliverables:
- Pages/components:
  - Dashboard summary cards
  - Timeline feed (readings/risk/incidents/plans/executions)
  - Pending approvals action panel
  - Execution/feedback detail panel
- Frontend env:
  - `NEXT_PUBLIC_API_BASE_URL`
  - optional map key if map provider is used

Done criteria:
- Operators can complete flow in UI:
  - observe incident
  - approve/reject plan
  - trigger simulate
  - inspect feedback and auto-replan evidence

## Recommended Sequence

1. Phase 0 immediately (safe, no behavior change).
2. Phase 1 (MQTT) first for edge parity.
3. Phase 2 (Pub/Sub) for cloud-scale stream reliability.
4. Phase 3 (Earth Engine) for spatial enrichment.
5. Phase 4 (Frontend) parallel from late Phase 2 onward.

## Risks and Controls

- Message duplication: enforce idempotency keys and unique ingest constraints.
- Ingest outage: keep HTTP ingest fallback active.
- Earth Engine latency/cost: add caching + bounded query area.
- Frontend drift: keep API contracts versioned and typed before UI build.

## Immediate Next Sprint Backlog

Backend:
- Create `iot_ingest_mode` switch and worker bootstrap hooks.
- Add domain metrics for MQTT/PubSub consumers.
- Add DLQ payload archive table or object storage sink.

Frontend:
- Replace starter `app/page.tsx` with dashboard shell.
- Add typed API client for `/dashboard/*`, `/plans`, `/approvals`, `/execution-batches`.
- Add auto-refresh + manual refresh controls for operations view.

## Implementation Status (April 17, 2026)

Started:
- MQTT worker bootstrap in API lifespan (`mqtt_enabled` + `iot_ingest_mode in {mqtt, hybrid}`).
- New worker `app/workers/mqtt_ingest_worker.py`:
  - subscribes `mekong/sensors/readings` + `mekong/sensors/status`
  - validates and ingests readings into existing `/sensors/ingest` domain service
  - reconnect loop with exponential backoff
  - dead-letter publish to `mekong/sensors/readings/dlq` on parse/persist failures
  - runtime ingest counters in logs (success/fail/status/dlq)
- Sensor ingest idempotency guard (`station_id + recorded_at + source`) to reduce duplicate writes.
- Demo simulator upgrade:
  - `scripts/run_demo_simulation.py` now supports `--transport http|mqtt`
  - MQTT publisher CLI flags (`--mqtt-broker-url`, `--mqtt-broker-port`, `--mqtt-topic-readings`, `--mqtt-qos`, auth options)
  - same scenario catalog can now drive agentic flow via MQTT path.

Next:
- Add DLQ archive sink (DB/object storage) instead of topic-only DLQ.
- Add ingest metrics endpoint/dashboard cards.
- Add DB-level unique constraint for hard idempotency under concurrent writes.
