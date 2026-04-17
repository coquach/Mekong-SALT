# RAG Sample Source Pack (International Standard Style)

This folder contains normalized source documents for RAG ingestion and retrieval benchmarking.

## Folder Taxonomy
- sop: standard operating playbooks
- threshold: policy matrices and control thresholds
- casebook: historical incident/case records
- guideline: operational interpretation notes

## Conventions
- Language: English (international-readable baseline)
- Date format: ISO 8601 (`YYYY-MM-DD`)
- Units: explicit SI-compatible notation where applicable (`dS/m`, `g/L`, `minutes`)
- IDs: stable and version-aware (`DOC-ID`, `POL-*`, `CASE-*`)
- Metadata keys: consistent snake_case labels

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
