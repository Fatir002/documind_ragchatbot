"""User registration and password verification."""

import logging
from dataclasses import dataclass

import bcrypt

from app.db import get_connection
from app.exceptions import AuthenticationError, InputValidationError

logger = logging.getLogger(__name__)

MIN_PASSWORD_LENGTH = 8


@dataclass
class User:
    """An authenticated user, safe to keep in session state (no password data)."""

    id: int
    username: str
    role: str


def _validate_credentials(username: str, password: str) -> None:
    if not username or not username.strip():
        raise InputValidationError("empty username", user_message="Username is required.")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise InputValidationError(
            "password too short",
            user_message=f"Password must be at least {MIN_PASSWORD_LENGTH} characters.",
        )


def register_user(username: str, password: str, role: str = "user") -> User:
    """Create a new user account with a securely hashed password."""
    _validate_credentials(username, password)
    username = username.strip()
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM users WHERE lower(username) = lower(%s)", (username,)
        ).fetchone()
        if existing:
            raise InputValidationError(
                f"username already taken: {username}",
                user_message="That username is already taken.",
            )
        user_id = conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s) RETURNING id",
            (username, password_hash, role),
        ).fetchone()[0]

    logger.info("user registered", extra={"user_id": user_id, "role": role})
    return User(id=user_id, username=username, role=role)


def authenticate(username: str, password: str) -> User:
    """Verify credentials and return the User, or raise AuthenticationError."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, role FROM users WHERE lower(username) = lower(%s)",
            (username.strip(),),
        ).fetchone()

    # Same error for "no such user" and "wrong password" — never reveal which one
    if row is None or not bcrypt.checkpw(password.encode("utf-8"), row[2].encode("utf-8")):
        logger.warning("failed login attempt", extra={"username": username.strip()})
        raise AuthenticationError("invalid username or password")

    logger.info("user authenticated", extra={"user_id": row[0]})
    return User(id=row[0], username=row[1], role=row[3])
