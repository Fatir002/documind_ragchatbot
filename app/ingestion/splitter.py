"""Split loaded Documents into retrieval-sized chunks."""

import logging

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def split_documents(documents: list[Document]) -> list[Document]:
    """Split Documents into chunks, keeping and extending their metadata."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        add_start_index=True,  # records each chunk's character offset in its source page
    )
    chunks = splitter.split_documents(documents)

    for position, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = position

    logger.info(
        "documents split",
        extra={"input_sections": len(documents), "output_chunks": len(chunks)},
    )
    return chunks
