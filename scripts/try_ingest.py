"""Full pipeline test: load, split, embed, and store a document.
Usage: python -m scripts.try_ingest <path>
"""

import sys
from pathlib import Path

from app.exceptions import DocuMindError
from app.ingestion.loaders import load_document
from app.ingestion.splitter import split_documents
from app.ingestion.store import store_document
from app.logging_config import setup_logging


def main() -> None:
    setup_logging("INFO")
    path = Path(sys.argv[1])
    raw_bytes = path.read_bytes()
    try:
        docs = load_document(path.name, raw_bytes)
        chunks = split_documents(docs)
        document_id = store_document(path.name, raw_bytes, chunks, uploaded_by=1)
    except DocuMindError as exc:
        print(f"❌ The user would see: {exc.user_message}")
        return
    print(f"✅ Stored document id={document_id} with {len(chunks)} chunks")


if __name__ == "__main__":
    main()
