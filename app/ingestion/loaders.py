"""Load uploaded files into LangChain Document objects, with validation."""

import logging
from io import BytesIO
from pathlib import Path

from langchain_core.documents import Document
from pypdf import PdfReader

from app.exceptions import DocumentProcessingError, InputValidationError

logger = logging.getLogger(__name__)

MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}


def load_document(filename: str, data: bytes) -> list[Document]:
    """Validate an uploaded file and return its text as Documents."""
    safe_name = Path(filename).name  # strips any folder parts from the name
    extension = Path(safe_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise InputValidationError(
            f"unsupported extension {extension!r}",
            user_message="Unsupported file type. Please upload a PDF, TXT, or MD file.",
        )
    if not data:
        raise InputValidationError("empty file", user_message="That file is empty.")
    if len(data) > MAX_FILE_BYTES:
        raise InputValidationError(
            f"file too large: {len(data)} bytes",
            user_message="File too large. The maximum size is 10 MB.",
        )

    if extension == ".pdf":
        documents = _load_pdf(safe_name, data)
    else:
        documents = _load_text(safe_name, data)

    logger.info("document loaded", extra={"file_name": safe_name, "sections": len(documents)})
    return documents


def _load_pdf(filename: str, data: bytes) -> list[Document]:
    try:
        reader = PdfReader(BytesIO(data))
        encrypted = reader.is_encrypted
        pages = (
            []
            if encrypted
            else [
                (number, page.extract_text() or "")
                for number, page in enumerate(reader.pages, start=1)
            ]
        )
    except Exception as exc:  # pypdf can raise many error types on damaged files
        logger.warning("pdf unreadable", extra={"file_name": filename, "error": str(exc)})
        raise DocumentProcessingError(f"pdf unreadable: {exc}") from exc

    if encrypted:
        raise DocumentProcessingError(
            "encrypted pdf",
            user_message="This PDF is password-protected. Remove the password and try again.",
        )

    documents = [
        Document(page_content=text.strip(), metadata={"source": filename, "page": number})
        for number, text in pages
        if text.strip()
    ]
    if not documents:
        raise DocumentProcessingError(
            "pdf has no extractable text",
            user_message="We couldn't find any text in this PDF. It may be a scanned image.",
        )
    return documents


def _load_text(filename: str, data: bytes) -> list[Document]:
    try:
        text = data.decode("utf-8-sig")  # also handles the BOM Windows Notepad adds
        text = text.replace("\r\n", "\n").replace("\r", "\n")  # normalize Windows line endings
    except UnicodeDecodeError as exc:
        raise DocumentProcessingError(
            "file is not valid UTF-8",
            user_message="We couldn't read that file. Please save it as UTF-8 text.",
        ) from exc

    if not text.strip():
        raise DocumentProcessingError("no text in file", user_message="That file contains no text.")
    return [Document(page_content=text.strip(), metadata={"source": filename})]
