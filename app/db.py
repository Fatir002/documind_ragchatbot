"""PostgreSQL connection pool and a safe connection helper."""

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

import psycopg
from psycopg.conninfo import make_conninfo
from psycopg_pool import ConnectionPool, PoolTimeout

from app.config import get_settings
from app.exceptions import DatabaseError

logger = logging.getLogger(__name__)


@lru_cache
def get_pool() -> ConnectionPool:
    """Create the connection pool once and reuse it."""
    s = get_settings()
    conninfo = make_conninfo(
        host=s.postgres_host,
        port=s.postgres_port,
        user=s.postgres_user,
        password=s.postgres_password.get_secret_value(),
        dbname=s.postgres_db,
    )
    try:
        pool = ConnectionPool(conninfo, min_size=1, max_size=5, open=False)
        pool.open(wait=True, timeout=5)
    except (psycopg.Error, PoolTimeout) as exc:
        logger.error("could not open database pool", extra={"error": str(exc)})
        raise DatabaseError(str(exc)) from exc
    logger.info("database pool ready")
    return pool


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    """Borrow a connection. Commits on success, rolls back on error."""
    pool = get_pool()
    try:
        with pool.connection() as conn:
            yield conn
    except (psycopg.Error, PoolTimeout) as exc:
        logger.error("database operation failed", extra={"error": str(exc)})
        raise DatabaseError(str(exc)) from exc
