"""Tests for app/ingestion/loaders.py: validation without needing real files."""

import pytest

from app.exceptions import InputValidationError
from app.ingestion.loaders import load_document


def test_rejects_unsupported_extension() -> None:
    with pytest.raises(InputValidationError):
        load_document("notes.docx", b"some content")


def test_rejects_empty_file() -> None:
    with pytest.raises(InputValidationError):
        load_document("empty.txt", b"")


def test_rejects_file_over_size_limit() -> None:
    oversized = b"a" * (11 * 1024 * 1024)  # 11 MB, over the 10 MB limit
    with pytest.raises(InputValidationError):
        load_document("big.txt", oversized)


def test_accepts_and_loads_valid_text_file() -> None:
    docs = load_document("notes.txt", b"Hello, this is a test document.")
    assert len(docs) == 1
    assert "Hello" in docs[0].page_content
    assert docs[0].metadata["source"] == "notes.txt"


def test_strips_windows_line_endings() -> None:
    docs = load_document("notes.txt", b"line one\r\nline two\r\n")
    assert "\r" not in docs[0].page_content