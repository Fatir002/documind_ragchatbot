"""Checks the pool works and shows how errors reach the user."""

from app.db import get_connection
from app.exceptions import DatabaseError
from app.logging_config import setup_logging


def main() -> None:
    setup_logging("INFO")
    try:
        with get_connection() as conn:
            row = conn.execute("SELECT current_user, current_database()").fetchone()
        print(f"✅ Connected as {row[0]} to {row[1]}")
    except DatabaseError as exc:
        print(f"❌ The user would see: {exc.user_message}")


if __name__ == "__main__":
    main()
