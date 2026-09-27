"""Answer a question using retrieved chunks, grounded with citations."""

import logging
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from app.config import get_settings
from app.exceptions import LLMServiceError
from app.qa.history import ConversationHistory
from app.retrieval.hybrid_search import hybrid_search
from app.retrieval.vector_search import RetrievedChunk

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful assistant named DocuMind that answers questions using \
ONLY the provided context. Follow these rules strictly:

1. If the user's message is a greeting, thanks, general chit-chat, or a question about \
you (the assistant) — such as your name or what you can do — respond naturally and \
briefly using this identity. Do not apply the context rules below to these messages, \
and do not mention sources for them.
2. For any question seeking information from the documents, answer only from the \
context below. Do not use outside knowledge.
3. If the context doesn't contain enough information to answer an information-seeking \
question, say so plainly. Do not guess or make anything up.
4. After each factual claim, cite the source using the format [Source N], matching the \
numbered context entries below.
5. Keep answers concise and directly relevant to the question.

Context:
{context}"""

REWRITE_PROMPT = """Given the conversation history and a follow-up question, rewrite the \
follow-up into a standalone question that makes sense without the history. If the \
follow-up question is already standalone, return it unchanged. Reply with ONLY the \
rewritten question, nothing else.

Conversation history:
{history}

Follow-up question: {question}

Standalone question:"""


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


def _standalone_question(question: str, history: ConversationHistory, llm: ChatGroq) -> str:
    """Rewrite a follow-up question so it can be searched on its own."""
    if not history.turns:
        return question
    prompt = REWRITE_PROMPT.format(history=history.as_text(), question=question)
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
    except Exception as exc:
        logger.warning("query rewrite failed, using original question", extra={"error": str(exc)})
        return question
    return response.content.strip()


def answer_question(question: str, history: ConversationHistory | None = None) -> Answer:
    """Retrieve relevant chunks and ask the LLM to answer using only them."""
    history = history or ConversationHistory()
    settings = get_settings()
    llm = ChatGroq(model=settings.groq_model, api_key=settings.groq_api_key, temperature=0)

    search_query = _standalone_question(question, history, llm)
    chunks = hybrid_search(search_query, limit=5)

    if not chunks:
        return Answer(
            text="I don't have any documents to search yet. Please upload one first.",
            sources=[],
        )

    prompt = SYSTEM_PROMPT.format(context=_format_context(chunks))
    try:
        response = llm.invoke([SystemMessage(content=prompt), HumanMessage(content=question)])
    except Exception as exc:  # the Groq SDK raises several distinct error types
        logger.error("LLM call failed", extra={"error": str(exc)})
        raise LLMServiceError(str(exc)) from exc

    logger.info(
        "question answered",
        extra={
            "question_length": len(question),
            "search_query": search_query,
            "chunks_used": len(chunks),
        },
    )
    return Answer(text=response.content, sources=chunks)
