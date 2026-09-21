"""A tiny SQL migration runner: applies numbered .sql files once, in order."""

import logging
from pathlib import Path

from app.db import get_connection
from app.exceptions import DatabaseError
from app.logging_config import setup_logging

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def run_migrations() -> list[str]:
    """Apply any migrations not yet applied. Returns the names applied now."""
    applied_now: list[str] = []
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename   TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        done = {row[0] for row in conn.execute("SELECT filename FROM schema_migrations")}

        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if path.name in done:
                continue
            conn.execute(path.read_text(encoding="utf-8"))
            conn.execute("INSERT INTO schema_migrations (filename) VALUES (%s)", (path.name,))
            applied_now.append(path.name)
            logger.info("migration applied", extra={"migration": path.name})
    return applied_now


def main() -> None:
    setup_logging("INFO")
    try:
        applied = run_migrations()
    except DatabaseError as exc:
        print(f"❌ Migration failed: {exc.user_message}")
        return
    if applied:
        print(f"✅ Applied: {', '.join(applied)}")
    else:
        print("✅ Database is already up to date")


if __name__ == "__main__":
    main()
