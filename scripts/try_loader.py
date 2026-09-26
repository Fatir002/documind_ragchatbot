"""Try the loader and splitter on a local file: python -m scripts.try_loader <path>"""

import sys
from pathlib import Path

from app.exceptions import DocuMindError
from app.ingestion.loaders import load_document
from app.ingestion.splitter import split_documents


def main() -> None:
    path = Path(sys.argv[1])
    try:
        docs = load_document(path.name, path.read_bytes())
        chunks = split_documents(docs)
    except DocuMindError as exc:
        print(f"❌ The user would see: {exc.user_message}")
        return
    print(f"✅ Loaded {len(docs)} section(s) -> {len(chunks)} chunk(s)")
    for chunk in chunks[:3]:
        print("-" * 40)
        print("metadata:", chunk.metadata)
        print("text    :", chunk.page_content[:120].replace("\n", " "))


if __name__ == "__main__":
    main()
