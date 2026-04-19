"""Batch-ingest bundled sample documents into Vertex-backed RAG."""

from __future__ import annotations

import asyncio
from pathlib import Path
import re

from app.db.session import AsyncSessionFactory, close_database_engine
from app.repositories.knowledge import KnowledgeDocumentRepository
from app.services.rag.source_sync_service import SourceSyncRequest, sync_knowledge_source


_SUPPORTED_EXTENSIONS = {
    ".txt",
    ".md",
    ".rst",
    ".json",
    ".yaml",
    ".yml",
    ".log",
    ".csv",
    ".docx",
    ".pdf",
}


def _discover_sample_manifest(*, backend_root: Path) -> list[dict[str, object]]:
    """Auto-discover all categorized sample files for one-pass ingestion."""
    samples_root = backend_root / "document" / "rag_samples"
    if not samples_root.exists():
        return []

    manifest: list[dict[str, object]] = []
    for file_path in sorted(samples_root.rglob("*")):
        if not file_path.is_file():
            continue

        ext = file_path.suffix.lower()
        if ext not in _SUPPORTED_EXTENSIONS:
            continue

        relative = file_path.relative_to(backend_root)
        relative_posix = relative.as_posix()

        category = _resolve_category(file_path, samples_root)
        title = _build_title(file_path.stem)
        source_uri = _build_source_uri(relative_posix)
        tags = _build_tags(category=category, file_path=file_path)

        manifest.append(
            {
                "relative_path": relative_posix,
                "title": title,
                "source_uri": source_uri,
                "document_type": category,
                "tags": tags,
                "metadata": {
                    "region_code": "global",
                    "sample": True,
                    "category": category,
                },
            }
        )
    return manifest


def _resolve_category(file_path: Path, samples_root: Path) -> str:
    try:
        parent = file_path.relative_to(samples_root).parts[0].strip().lower()
    except Exception:
        parent = "guideline"
    if parent in {"sop", "threshold", "casebook", "guideline"}:
        return parent
    return "guideline"


def _build_title(stem: str) -> str:
    title = stem.replace("_", " ").replace("-", " ").strip()
    title = re.sub(r"\s+", " ", title)
    if not title:
        return "Sample Document"
    return title.title()


def _build_source_uri(relative_path: str) -> str:
    safe = relative_path.lower().replace(" ", "-")
    safe = re.sub(r"[^a-z0-9_./-]", "", safe)
    safe = safe.replace(".", "-")
    return f"mekong-salt://samples/{safe}"


def _build_tags(*, category: str, file_path: Path) -> list[str]:
    tags = [category, "sample"]
    ext = file_path.suffix.lower().lstrip(".")
    if ext:
        tags.append(ext)

    stem = file_path.stem.lower()
    for token in ("salinity", "water", "quality", "irrigation", "policy", "report", "weather", "tide"):
        if token in stem and token not in tags:
            tags.append(token)
    return tags


async def _run() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    manifest = _discover_sample_manifest(backend_root=backend_root)
    if not manifest:
        print("summary ingested=0 skipped=0 total=0")
        print("warning no_sample_files_found_under=document/rag_samples")
        return

    ingested = 0
    skipped = 0
    failed = 0
    failed_items: list[str] = []

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
            try:
                result = await sync_knowledge_source(
                    session,
                    request=SourceSyncRequest(
                        file_path=str(absolute_path),
                        title=str(item["title"]),
                        source_uri=source_uri,
                        document_type=str(item["document_type"]),
                        tags=list(item["tags"]),
                        metadata_payload=dict(item["metadata"]),
                    ),
                )
                ingested += 1
                print(
                    "ingested_sample "
                    f"document_id={result.document_id} "
                    f"chunk_count={result.chunk_count} "
                    f"document_type={item['document_type']} "
                    f"source_uri={result.source_uri}"
                )
            except Exception as exc:
                failed += 1
                failure_key = f"{item['relative_path']}|{type(exc).__name__}|{exc}"
                failed_items.append(failure_key)
                await session.rollback()
                print(
                    "ingest_failed "
                    f"document_type={item['document_type']} "
                    f"source_uri={source_uri} "
                    f"error={type(exc).__name__}:{exc}"
                )

    print(f"summary ingested={ingested} skipped={skipped} failed={failed} total={len(manifest)}")
    if failed_items:
        print("failed_items_start")
        for entry in failed_items:
            print(entry)
        print("failed_items_end")


async def _main_async() -> None:
    try:
        await _run()
    finally:
        await close_database_engine()


def main() -> None:
    asyncio.run(_main_async())


if __name__ == "__main__":
    main()
