# Mekong-SALT

`backend/` contains the FastAPI modular monolith for the Mekong-SALT decision-support backend. The current runtime model is reactive: monitoring goals drive risk evaluation, incident handling, AI planning, reactive approval, and simulated execution without public API trigger steps.

Canonical API boundaries are documented in [backend/README.md](backend/README.md):

- `/api/v1/readings/*` is the canonical reading query surface
- `/api/v1/plans/*` is the canonical plan read surface
- `/api/v1/agent/runs*` is observability-only

`frontend/` contains the Vite + React client for the UI integration phase.
