"""Answer a question using retrieved chunks, grounded with citations."""

import logging
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from app.config import get_settings
from app.exceptions import LLMServiceError
from app.retrieval.hybrid_search import hybrid_search
from app.retrieval.vector_search import RetrievedChunk

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful assistant that answers questions using ONLY the \
provided context. Follow these rules strictly:

1. Answer only from the context below. Do not use outside knowledge.
2. If the context doesn't contain enough information to answer, say so plainly. \
Do not guess or make anything up.
3. After each claim, cite the source using the format [Source N], matching the \
numbered context entries below.
4. Keep the answer concise and directly relevant to the question.

Context:
{context}"""


@dataclass
class Answer:
    """An LLM answer plus the chunks it was grounded in, for citation display."""

    text: str
    sources: list[RetrievedChunk]


def _format_context(chunks: list[RetrievedChunk]) -> str:
    """Number each chunk so the model's [Source N] citations map back to one."""
    parts = []
    for number, chunk in enumerate(chunks, start=1):
        page = chunk.metadata.get("page")
        location = f", page {page}" if page is not None else ""
        parts.append(
            f"[Source {number}] ({chunk.metadata.get('source', 'unknown')}{location})\n"
            f"{chunk.content}"
        )
    return "\n\n".join(parts)


def answer_question(question: str) -> Answer:
    """Retrieve relevant chunks and ask the LLM to answer using only them."""
    chunks = hybrid_search(question, limit=5)

    if not chunks:
        return Answer(
            text="I don't have any documents to search yet. Please upload one first.",
            sources=[],
        )

    settings = get_settings()
    llm = ChatGroq(model=settings.groq_model, api_key=settings.groq_api_key, temperature=0)

    prompt = SYSTEM_PROMPT.format(context=_format_context(chunks))
    try:
        response = llm.invoke([SystemMessage(content=prompt), HumanMessage(content=question)])
    except Exception as exc:  # the Groq SDK raises several distinct error types
        logger.error("LLM call failed", extra={"error": str(exc)})
        raise LLMServiceError(str(exc)) from exc

    logger.info(
        "question answered",
        extra={"question_length": len(question), "chunks_used": len(chunks)},
    )
    return Answer(text=response.content, sources=chunks)
