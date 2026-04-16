"""CLI to ingest document/csv sources into Vertex-backed RAG index."""

from __future__ import annotations

import argparse
import asyncio

from app.db.session import AsyncSessionFactory, close_database_engine
from app.services.rag.ingestion_service import ingest_knowledge_file_to_vertex


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest a document/csv source into DB chunks + Vertex Vector Search.",
    )
    parser.add_argument("file_path", help="Path to source file (txt/md/csv/docx).")
    parser.add_argument("--title", default=None, help="Optional document title override.")
    parser.add_argument("--source-uri", default=None, help="Optional stable source URI.")
    parser.add_argument(
        "--document-type",
        default="guideline",
        help="Document type label (guideline|threshold|policy|sop|...).",
    )
    parser.add_argument(
        "--tags",
        default="",
        help="Comma-separated tags, e.g. 'sop,irrigation,salinity'.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=900,
        help="Chunk size in characters.",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=120,
        help="Chunk overlap in characters.",
    )
    return parser


async def _run(args: argparse.Namespace) -> None:
    tags = [item.strip() for item in args.tags.split(",") if item.strip()]

    async with AsyncSessionFactory() as session:
        result = await ingest_knowledge_file_to_vertex(
            session,
            file_path=args.file_path,
            title=args.title,
            source_uri=args.source_uri,
            document_type=args.document_type,
            tags=tags or None,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )

    print("ingestion_succeeded")
    print(f"document_id={result.document_id}")
    print(f"chunk_count={result.chunk_count}")
    print(f"source_uri={result.source_uri}")


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    try:
        asyncio.run(_run(args))
    finally:
        asyncio.run(close_database_engine())


if __name__ == "__main__":
    main()
