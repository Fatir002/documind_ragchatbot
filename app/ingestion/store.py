"""Embed chunks and store them, alongside their parent document, in Postgres."""

import hashlib
import json
import logging

from langchain_core.documents import Document
from psycopg.types.json import Json

from app.db import get_connection
from app.embeddings import get_embeddings
from app.exceptions import DocumentProcessingError

logger = logging.getLogger(__name__)


def store_document(
    filename: str, raw_bytes: bytes, chunks: list[Document], uploaded_by: int
) -> int:
    """Store a document and its embedded chunks. Returns the new document id."""
    content_hash = hashlib.sha256(raw_bytes).hexdigest()
    vectors = get_embeddings().embed_documents([c.page_content for c in chunks])

    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM documents WHERE content_hash = %s", (content_hash,)
        ).fetchone()
        if existing:
            raise DocumentProcessingError(
                f"duplicate content_hash for {filename}",
                user_message="This document has already been uploaded.",
            )

        document_id = conn.execute(
            """
            INSERT INTO documents (filename, content_hash, uploaded_by)
            VALUES (%s, %s, %s) RETURNING id
            """,
            (filename, content_hash, uploaded_by),
        ).fetchone()[0]

        rows = [
            (
                document_id,
                chunk.metadata.get("chunk_index", position),
                chunk.page_content,
                Json(chunk.metadata),
                vector_literal(vector),
            )
            for position, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True))
        ]
        conn.cursor().executemany(
            """
            INSERT INTO chunks (document_id, chunk_index, content, metadata, embedding)
            VALUES (%s, %s, %s, %s, %s)
            """,
            rows,
        )

    logger.info(
        "document stored",
        extra={"document_id": document_id, "file_name": filename, "chunk_count": len(chunks)},
    )
    return document_id


def vector_literal(vector: list[float]) -> str:
    """Format a Python list as the text pgvector expects, e.g. '[0.1,0.2,0.3]'."""
    return json.dumps(vector)
