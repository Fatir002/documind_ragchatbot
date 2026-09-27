"""Loads the embedding model once and reuses it everywhere."""

import logging
from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384


@lru_cache
def get_embeddings() -> HuggingFaceEmbeddings:
    """Create the embedding model once. The first call downloads and caches it."""
    logger.info("loading embedding model", extra={"model": EMBEDDING_MODEL_NAME})
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
