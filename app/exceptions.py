"""Custom exceptions: friendly user message separated from technical detail."""


class DocuMindError(Exception):
    """Base class for all expected application errors."""

    default_user_message = "Something went wrong. Please try again."

    def __init__(self, detail: str = "", *, user_message: str | None = None) -> None:
        super().__init__(detail or self.default_user_message)
        self.user_message = user_message or self.default_user_message


class ConfigurationError(DocuMindError):
    default_user_message = (
        "The application is not configured correctly. Please contact the administrator."
    )


class DatabaseError(DocuMindError):
    default_user_message = "We couldn't reach the database. Please try again in a moment."


class InputValidationError(DocuMindError):
    default_user_message = "Some of the information you entered isn't valid."


class AuthenticationError(DocuMindError):
    default_user_message = "Incorrect username or password."


class AuthorizationError(DocuMindError):
    default_user_message = "You don't have permission to do that."


class DocumentProcessingError(DocuMindError):
    default_user_message = "We couldn't process that document. Check the file and try again."


class LLMServiceError(DocuMindError):
    default_user_message = "The AI service is unavailable right now. Please try again shortly."
