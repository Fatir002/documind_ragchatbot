"""Smoke test: verifies Postgres access, pgvector, and the Groq key."""

import psycopg
from langchain_groq import ChatGroq

from app.config import get_settings


def check_database() -> None:
    s = get_settings()
    with psycopg.connect(
        host=s.postgres_host,
        port=s.postgres_port,
        user=s.postgres_user,
        password=s.postgres_password.get_secret_value(),
        dbname=s.postgres_db,
    ) as conn:
        print(f"✅ PostgreSQL connected as {s.postgres_user}")

        row = conn.execute(
            "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
        ).fetchone()
        if row is None:
            raise RuntimeError("pgvector extension is not enabled in this database")
        print(f"✅ pgvector {row[0]} enabled")

        conn.execute("CREATE TABLE _smoke_test (id integer)")
        conn.execute("DROP TABLE _smoke_test")
        print("✅ Can create tables in schema 'public'")


def check_llm() -> None:
    s = get_settings()
    llm = ChatGroq(model=s.groq_model, api_key=s.groq_api_key, temperature=0)
    reply = llm.invoke("Reply with the single word: OK")
    print(f"✅ Groq responded: {reply.content.strip()}")


def main() -> None:
    checks = [("Database", check_database), ("Groq", check_llm)]
    for name, check in checks:
        try:
            check()
        except Exception as exc:  # broad on purpose: this is a diagnostic script
            print(f"❌ {name} check failed: {exc}")


if __name__ == "__main__":
    main()
