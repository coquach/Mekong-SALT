"""Batch-ingest bundled sample documents into Vertex-backed RAG."""

from __future__ import annotations

import asyncio
from pathlib import Path

from app.db.session import AsyncSessionFactory, close_database_engine
from app.repositories.knowledge import KnowledgeDocumentRepository
from app.services.rag.ingestion_service import ingest_knowledge_file_to_vertex


def _sample_manifest() -> list[dict[str, object]]:
    return [
        {
            "relative_path": "document/rag_samples/sop_salinity_response_playbook.md",
            "title": "SOP Salinity Response Playbook",
            "source_uri": "mekong-salt://samples/sop-salinity-response-playbook-v1",
            "document_type": "sop",
            "tags": ["sop", "salinity", "response", "irrigation"],
            "metadata": {"region_code": "global", "sample": True},
        },
        {
            "relative_path": "document/rag_samples/threshold_policy_matrix.csv",
            "title": "Threshold Policy Matrix",
            "source_uri": "mekong-salt://samples/threshold-policy-matrix-v1",
            "document_type": "threshold",
            "tags": ["threshold", "policy", "salinity", "csv"],
            "metadata": {"region_code": "global", "sample": True},
        },
        {
            "relative_path": "document/rag_samples/past_incident_casebook.csv",
            "title": "Past Incident Casebook",
            "source_uri": "mekong-salt://samples/past-incident-casebook-v1",
            "document_type": "casebook",
            "tags": ["case", "incident", "history", "csv"],
            "metadata": {"region_code": "global", "sample": True},
        },
        {
            "relative_path": "document/rag_samples/weather_tide_operational_notes.md",
            "title": "Weather Tide Operational Notes",
            "source_uri": "mekong-salt://samples/weather-tide-operational-notes-v1",
            "document_type": "guideline",
            "tags": ["weather", "tide", "guidance", "operations"],
            "metadata": {"region_code": "global", "sample": True},
        },
    ]


async def _run() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    manifest = _sample_manifest()

    ingested = 0
    skipped = 0

    async with AsyncSessionFactory() as session:
        repo = KnowledgeDocumentRepository(session)

        for item in manifest:
            source_uri = str(item["source_uri"])
            existing = await repo.get_by_source_uri(source_uri)
            if existing is not None:
                skipped += 1
                print(f"skipped_existing source_uri={source_uri}")
                continue

            absolute_path = backend_root / str(item["relative_path"])
            result = await ingest_knowledge_file_to_vertex(
                session,
                file_path=str(absolute_path),
                title=str(item["title"]),
                source_uri=source_uri,
                document_type=str(item["document_type"]),
                tags=list(item["tags"]),
                metadata_payload=dict(item["metadata"]),
            )
            ingested += 1
            print(
                "ingested_sample "
                f"document_id={result.document_id} "
                f"chunk_count={result.chunk_count} "
                f"source_uri={result.source_uri}"
            )

    print(f"summary ingested={ingested} skipped={skipped} total={len(manifest)}")


def main() -> None:
    try:
        asyncio.run(_run())
    finally:
        asyncio.run(close_database_engine())


if __name__ == "__main__":
    main()
