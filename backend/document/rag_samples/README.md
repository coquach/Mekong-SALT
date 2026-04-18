# RAG Sample Source Pack (International Standard Style)

This folder contains normalized source documents for RAG ingestion and retrieval benchmarking.

## Folder Taxonomy
- sop: standard operating playbooks
- threshold: policy matrices and control thresholds
- casebook: historical incident/case records
- guideline: operational interpretation notes

## Current Bundle Coverage
- `sop/sop_salinity_response_playbook.md`: end-to-end response SOP for intake salinity incidents.
- `threshold/threshold_policy_matrix.csv`: structured threshold and response policy matrix.
- `casebook/casebook_salinity_incidents.csv`: scenario-based incident/outcome cases for retrieval benchmarking.
- `guideline/weather_tide_operational_notes.md`: hydro-meteorological interpretation guidance.
- `guideline/sensor_confidence_and_calibration_notes.md`: confidence and calibration checklist for sensor readings.
- `sop/recovery_and_closure_checklist.md`: staged recovery and closure checklist after an incident.
- `casebook/casebook_recovery_patterns.csv`: recovery-window and hold-position reference cases.

## Conventions
- Language: English (international-readable baseline)
- Date format: ISO 8601 (`YYYY-MM-DD`)
- Units: explicit SI-compatible notation where applicable (`dS/m`, `g/L`, `minutes`)
- IDs: stable and version-aware (`DOC-ID`, `POL-*`, `CASE-*`)
- Metadata keys: consistent snake_case labels

## Data Authenticity Policy
- This pack is designed for RAG benchmarking and operator training support.
- Casebook rows are normalized reference scenarios unless explicitly marked as validated field incidents.
- Avoid claiming synthetic/reference cases as official government observations.
- New files may summarize operational best practice and reference scenarios; keep them clearly labeled as guidance or benchmark material.

## File-Level Expectations
- Markdown docs: include document control section (ID, version, status, effective date).
- CSV policy matrices: include policy version/effective date/unit/governance fields.
- CSV casebooks: include incident date, normalized response actions, and outcome class.

## Intended Use
- Input for `scripts/ingest_rag_samples.py`.
- Retrieval quality baseline for lane and shadow-mode comparisons.

## Update Workflow (Important)
- `scripts/ingest_rag_samples.py` only ingests new sources; existing `source_uri` entries are skipped.
- After editing any sample file, re-sync that file with `scripts/ingest_rag_source.py` to refresh chunks/vectors.
- Keep a stable `source_uri`/`source_key` per logical document to preserve version traceability.
