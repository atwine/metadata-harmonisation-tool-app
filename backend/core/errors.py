import logging

from fastapi import HTTPException

logger = logging.getLogger("uvicorn.error")

GENERIC_500 = "Something went wrong. Check the server log."


def server_error(route: str, exc: Exception) -> HTTPException:
    # Log only the route and the exception class: the message text can contain file paths or participant data.
    logger.error("500 on %s: %s", route, type(exc).__name__)
    return HTTPException(500, GENERIC_500)


CSV_UNREADABLE = (
    "Could not read this file as a CSV. Check that it is a comma-separated text file "
    "with a header row."
)


def log_failure(where: str, exc: Exception) -> None:
    """Log a failure that is not an HTTP error (a pipeline step, a skipped study).
    Same rule as server_error: class name only, never the message text."""
    logger.error("failure in %s: %s", where, type(exc).__name__)


class ConfigError(ValueError):
    """A problem with the AI settings that the app itself detected. Its message is
    written by this app (never taken from a library), so it is safe to show."""


def ai_error_message(exc: Exception) -> str:
    """Plain-language reason for a failed AI connection or call. The exception text can
    carry URLs, key fragments or file paths, so only the exception class is used."""
    if isinstance(exc, ConfigError):
        return str(exc)
    name = type(exc).__name__.lower()
    if "auth" in name or "permission" in name:
        return "The AI service rejected the API key. Check the key and try again."
    if "timeout" in name:
        return "The AI service did not answer in time. Try again, or raise the timeout."
    if "connect" in name or "connection" in name:
        return "Could not reach the AI service. Check that it is running and the address is right."
    if "notfound" in name:
        return "The AI service could not find that model or address. Check the model name."
    if "ratelimit" in name:
        return "The AI service is limiting requests. Wait a moment and try again."
    return "The AI connection test failed. Check the provider, address, model and key."
