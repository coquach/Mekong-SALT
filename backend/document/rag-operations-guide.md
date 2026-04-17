# RAG Operations Guide (Backend)

This guide describes how RAG works in Mekong-SALT backend, how to configure it, and how to operate it safely in demo and production-like environments.

## 1. Runtime Architecture

Planning-time retrieval is built from 3 evidence lanes:

1. Static document lane
- SOP/threshold/guideline documents in `knowledge_documents` + `embedded_chunks`
- Primary path: Vertex Vector Search
- Fallback path: local DB ranking

2. Similar-case lane
- Historical incidents and their latest plans from operational tables
- Pure DB retrieval

3. Memory-case lane
- Episodic cases from `memory_cases`
- Vector-first, then DB fallback

Lane outputs are merged and ranked by broker late-fusion:
- de-duplicate evidence keys
- sort by score
- keep top `max_evidence`

References:
- `app/services/rag/retrieval_service.py`
- `app/services/rag/static_document_lane.py`
- `app/services/rag/similar_case_lane.py`
- `app/services/rag/memory_case_lane.py`
- `app/services/rag/retrieval_broker.py`

## 2. Data Flow

1. Source files are ingested from CLI (`scripts/ingest_rag_source.py` or `scripts/ingest_rag_samples.py`).
2. Content is normalized, chunked, embedded, and upserted to Vertex.
3. Chunk metadata and document governance fields are stored in Postgres.
4. At planning time, objective + risk context produce query terms.
5. Retrieval broker returns ranked evidence with provenance and ranking metadata.
6. Planner prompt receives retrieval context and generates a structured plan.

## 3. Required Configuration

Set these in `backend/.env`:

- `VERTEX_AI_PROJECT`
- `VERTEX_AI_LOCATION`
- `VERTEX_VECTOR_SEARCH_INDEX`
- `VERTEX_VECTOR_SEARCH_INDEX_ENDPOINT`
- `VERTEX_VECTOR_SEARCH_DEPLOYED_INDEX_ID`
- `RAG_EMBEDDING_MODEL` (default `text-embedding-005`)

Recommended toggles:

- `RAG_USE_VERTEX_VECTOR_SEARCH=true`
- `RAG_ENABLE_LOCAL_FALLBACK=true`
- `RAG_STATIC_CORPUS_PROVIDER=vector_search`
- `RAG_RETRIEVAL_TOP_K=8`

Notes:
- `vertex_rag_engine_adapter` is transitional naming, still backed by Vertex Vector Search.
- Runtime planning provider is Gemini-only in current backend settings.

## 4. Ingestion Runbook

### 4.1 Ingest one source

```bash
./.venv/Scripts/python.exe scripts/ingest_rag_source.py \
  "./document/rag_samples/threshold/threshold_policy_matrix.csv" \
  --document-type threshold \
  --tags "threshold,salinity,policy"
```

### 4.2 Ingest bundled samples

```bash
./.venv/Scripts/python.exe scripts/ingest_rag_samples.py
```

Important behavior:

- `scripts/ingest_rag_samples.py` skips sources that already exist by `source_uri`.
- If you edited sample files and need refreshed embeddings/chunks, re-sync those files explicitly with `scripts/ingest_rag_source.py`.
- For sample updates, prefer stable `--source-uri` + `--source-key` so version history stays traceable.

Example re-sync after editing SOP:

```bash
./.venv/Scripts/python.exe scripts/ingest_rag_source.py \
  "./document/rag_samples/sop/sop_salinity_response_playbook.md" \
  --source-uri "mekong-salt://samples/document/rag_samples/sop/sop_salinity_response_playbook-md" \
  --document-type sop \
  --tags "sop,sample,salinity"
```

### 4.3 Supported formats

- `txt`, `md`, `rst`, `json`, `yaml`, `yml`, `log`
- `csv`
- `docx` (requires `python-docx`)
- `pdf` (requires `pypdf`)

### 4.4 Governance behavior

- Re-index if content hash changes
- CSV TTL-based re-index checks (`RAG_CSV_REINDEX_TTL_DAYS`)
- Old datapoints are removed before new upsert
- Document metadata tracks source key, effective date, version, and last indexed time

## 5. Retrieval Contract (What Planner Receives)

`retrieval_context` includes:

- `evidence`: ranked evidence rows (with `rank`, `score`, `citation`)
- `provenance`:
  - vector/local usage flags
  - provider name
  - source counts
  - total candidate count
- `ranking_metadata`:
  - top_k and max_evidence
  - query terms
  - top citations
- `policy_flags`:
  - simulation-only constraints
  - evidence minimum requirement

This payload is available in planning trace and can be audited.

## 6. Observability and Verification

### 6.1 Check plan and traces

- `GET /api/v1/plans?limit=10`
- `GET /api/v1/agent/runs?limit=20`
- `GET /api/v1/agent/runs/{run_id}`

### 6.2 Check audit logs for retrieval trace

- `GET /api/v1/audit/logs?plan_id={plan_id}`

Plan audit payload stores retrieval trace summary and planning transition log.

### 6.3 Dashboard stream

- `GET /api/v1/dashboard/stream`

Useful for confirming plan-created and execution summary events during scenarios.

## 7. Quality Tuning Guidance

If you ingest many books/documents, use this checklist:

1. Keep top-k conservative first
- Demo: `RAG_RETRIEVAL_TOP_K=5..6`
- Larger ops: `6..10` depending on latency budget

2. Keep chunk size moderate
- Start around 600 to 900 chars
- Too large chunks reduce citation precision

3. Enforce metadata discipline
- Region scope, document class, severity relevance
- Stable source keys and effective dates

4. Control duplication
- Avoid ingesting near-identical documents repeatedly
- Prefer version updates over duplicate titles/sources
- Keep one stable `source_uri` per logical document and re-sync in place

5. Validate citation stability
- Run same scenario multiple times
- Compare top citations and source counts
- Large variance indicates ranking noise or poor metadata

## 8. Common Problems and Fixes

1. Problem: retrieval returns weak/irrelevant evidence
- Check source metadata completeness
- Reduce top-k
- Verify vector index and deployed index id

2. Problem: planning prompt becomes noisy
- Reduce top-k and max evidence
- Split very large documents into cleaner sections before ingest

3. Problem: memory lane not contributing
- Ensure migration/table readiness for `memory_cases`
- Verify vector restricts include `entity_type=memory_case`

4. Problem: fallback always used
- Check Vertex credentials and index endpoint
- Confirm `RAG_USE_VERTEX_VECTOR_SEARCH=true`

## 9. Operational Baseline for Demo

Suggested demo profile:

- `RAG_USE_VERTEX_VECTOR_SEARCH=true`
- `RAG_ENABLE_LOCAL_FALLBACK=true`
- `RAG_RETRIEVAL_TOP_K=6`
- `RAG_STATIC_CORPUS_PROVIDER=vector_search`
- Ingest only curated sample pack before demo

Then run:

```bash
./.venv/Scripts/python.exe scripts/run_demo_setup.py
./.venv/Scripts/python.exe scripts/run_demo_simulation.py --scenario rag-provenance-drilldown
```

Inspect run trace and plan audit to verify provenance quality.
