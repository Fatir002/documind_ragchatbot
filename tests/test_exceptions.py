"""Tests for app/exceptions.py: user-facing messages stay separate from detail."""

from app.exceptions import DatabaseError, DocuMindError, InputValidationError


def test_default_user_message_is_used_when_no_override_given() -> None:
    error = DatabaseError("connection refused on port 5432")
    assert error.user_message == "We couldn't reach the database. Please try again in a moment."
    assert str(error) == "connection refused on port 5432"


def test_custom_user_message_overrides_default() -> None:
    error = InputValidationError("file is 25MB", user_message="File too large (max 10 MB).")
    assert error.user_message == "File too large (max 10 MB)."


def test_empty_detail_falls_back_to_user_message() -> None:
    error = DocuMindError()
    assert str(error) == error.user_message == "Something went wrong. Please try again."


def test_all_custom_exceptions_are_documind_errors() -> None:
    assert isinstance(DatabaseError("x"), DocuMindError)
    assert isinstance(InputValidationError("x"), DocuMindError)