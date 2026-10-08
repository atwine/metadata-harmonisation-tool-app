import logging

from fastapi import HTTPException

logger = logging.getLogger("uvicorn.error")

GENERIC_500 = "Something went wrong. Check the server log."


def server_error(route: str, exc: Exception) -> HTTPException:
    # Log only the route and the exception class: the message text can contain file paths or participant data.
    logger.error("500 on %s: %s", route, type(exc).__name__)
    return HTTPException(500, GENERIC_500)
