# 📄 DocuMind — RAG Chatbot with Hybrid Search

A production-style Retrieval-Augmented Generation (RAG) chatbot that answers questions from your own documents, with hybrid search, conversation memory, citations, authentication, and a Streamlit UI.

Built as a portfolio project demonstrating the core skills expected of a junior Generative AI / AI Automation engineer.

---

## Features

- **Document ingestion** — upload PDF, TXT, or MD files (up to 10 MB), validated and chunked
- **Hybrid retrieval** — combines pgvector semantic search with PostgreSQL full-text keyword search, merged using Reciprocal Rank Fusion (RRF)
- **Grounded Q&A** — answers are generated only from retrieved context, with inline `[Source N]` citations; the model says "I don't know" rather than hallucinating
- **Conversation memory** — follow-up questions (e.g. "what are its limitations?") are automatically rewritten into standalone queries using chat history
- **Authentication** — bcrypt-hashed passwords, session-based login, role-based access (`admin` can upload, `user` can only chat)
- **Structured JSON logging** — every operation logs a machine-readable event with severity levels
- **Custom exceptions** — every user-facing error shows a friendly message; technical detail goes to the logs, never the UI
- **Input validation** — file type/size limits, question length limits, per-session rate limiting
- **Database migrations** — a lightweight versioned SQL migration runner, applied automatically
- **Automated tests + CI** — pytest unit tests run automatically via GitHub Actions on every push
- **Dockerized** — runs anywhere via a single `Dockerfile`

---

## Architecture

Streamlit UI (login · chat · admin upload)
        │
Service layer (auth · ingestion · retrieval · Q&A chain)
        │
LangChain (splitting · embeddings · retrieval · prompting)
   │                              │
PostgreSQL + pgvector           Groq (LLM)
(users, documents, chunks)

**Retrieval flow:** a question is optionally rewritten using conversation history → embedded and searched by both vector similarity (pgvector, HNSW index) and keyword full-text search (PostgreSQL `tsvector`) → both ranked lists are merged with Reciprocal Rank Fusion → top chunks are passed to the LLM with a strict "answer only from context" system prompt.

---

## Tech Stack

| Layer | Choice |
|---|---|
| LLM | Groq (`openai/gpt-oss-120b`) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (local, free, 384-dim) |
| Vector store | PostgreSQL + pgvector (HNSW index) |
| Keyword search | PostgreSQL full-text search (`tsvector` / `ts_rank`) |
| Framework | LangChain |
| Frontend | Streamlit |
| Auth | bcrypt password hashing |
| Testing | pytest |
| Linting/formatting | Ruff |
| CI | GitHub Actions |
| Containerization | Docker |

---

## Design Decisions

- **Groq for chat, local model for embeddings** — Groq doesn't serve embedding models, so a free local model (`all-MiniLM-L6-v2`) is used instead of a paid API, keeping the whole pipeline free to run.
- **Custom `chunks` table instead of LangChain's default `PGVector`** — needed a `tsvector` column for hybrid search, which LangChain's built-in vector store schema doesn't provide.
- **`ts_rank` instead of BM25** — PostgreSQL's built-in full-text search was chosen over true BM25 (e.g. via the `pg_search`/ParadeDB extension) for portability: `pg_search` isn't available on most managed Postgres hosts. `pg_search` is a documented upgrade path if stronger keyword ranking is needed later.
- **Reciprocal Rank Fusion (RRF)** merges vector and keyword results using rank position rather than raw scores, since cosine similarity and `ts_rank` live on incomparable scales.
- **Query rewriting for follow-ups** — before retrieval, a follow-up question is rewritten into a standalone question using recent chat history, so vague references like "its" or "that" still retrieve relevant chunks.
- **Errors carry two messages** — every custom exception separates a technical `detail` (for logs) from a `user_message` (for the UI), so users never see stack traces or raw database errors.
- **Own migration runner instead of Alembic** — a small, transparent SQL migration system for this project's scale; documented here as an intentional simplification, with Alembic noted as the natural upgrade path for larger projects.

---

## Project Structure

\`\`\`
documind/
├── app/
│   ├── config.py            # environment-based settings (pydantic-settings)
│   ├── logging_config.py    # structured JSON logging
│   ├── exceptions.py        # custom exceptions with user-facing messages
│   ├── db.py                # PostgreSQL connection pool
│   ├── migrate.py           # SQL migration runner
│   ├── auth.py               # registration & login (bcrypt)
│   ├── embeddings.py         # embedding model loader
│   ├── ingestion/            # loaders, splitter, storage
│   ├── retrieval/            # vector search, keyword search, hybrid (RRF)
│   └── qa/                   # Q&A chain, conversation history
├── migrations/                # numbered SQL migration files
├── scripts/                   # manual test/debug scripts
├── tests/                     # pytest unit tests
├── .github/workflows/ci.yml   # lint + test on every push
├── app_ui.py                  # Streamlit entry point
├── Dockerfile
└── requirements.txt
\`\`\`

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ with the [pgvector](https://github.com/pgvector/pgvector) extension enabled
- A free [Groq API key](https://console.groq.com)
- Docker (optional, for containerized deployment)

### 1. Clone and set up a virtual environment

git clone https://github.com/Fatir002/documind_ragchatbot.git
cd documind_ragchatbot
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

### 2. Install dependencies

pip install -r requirements-dev.txt

### 3. Set up the database

Create a database and a limited application role (adjust names/password as you like):

CREATE DATABASE rag_db;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE ROLE documind_app WITH LOGIN PASSWORD 'your-password';
GRANT CONNECT ON DATABASE rag_db TO documind_app;
GRANT USAGE, CREATE ON SCHEMA public TO documind_app;

### 4. Configure environment variables

cp .env.example .env

Edit `.env` with your real values:

POSTGRES_USER=documind_app
POSTGRES_PASSWORD=your-password
POSTGRES_DB=rag_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

GROQ_API_KEY=your-groq-key
GROQ_MODEL=openai/gpt-oss-120b
LOG_LEVEL=INFO

### 5. Run database migrations

python -m app.migrate

### 6. Launch the app

streamlit run app_ui.py

Open `http://localhost:8501`, register an account, and start chatting. Register a second account and promote it to `admin` manually in the database to enable document uploads:

UPDATE users SET role = 'admin' WHERE username = 'your-username';

---

## Running with Docker

docker build -t documind .
docker run -p 8501:8501 --env-file .env -e POSTGRES_HOST=host.docker.internal documind

> **Note:** `POSTGRES_HOST=host.docker.internal` lets the container reach a PostgreSQL instance running on your host machine. If your database is hosted elsewhere (e.g. a managed cloud Postgres), set `POSTGRES_HOST` to that instead.
>
> First build times can take several minutes due to PyTorch and other ML dependencies — this is expected and only happens once; subsequent builds are cached.

---

## Testing

pytest -v

Unit tests cover exception handling, conversation history, and input validation logic — components that don't require a live database or API connection. Linting and formatting are enforced via Ruff and checked automatically in CI on every push.

ruff check .
ruff format --check .

---

## Known Limitations & Future Improvements

- Conversation memory is per-session and in-memory only (not persisted across app restarts)
- No OCR — scanned PDFs with no text layer aren't supported
- Keyword search uses PostgreSQL's `ts_rank`, not true BM25 (see Design Decisions)
- No password reset flow
- Single embedding model; swapping models requires updating the `vector(384)` column dimension in the `chunks` table migration

---

## Author

Developed by **Fatir Faraz**
