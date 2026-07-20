import logging
import sys

from pythonjsonlogger.json import JsonFormatter

from app.core.config import settings


def configure_logging() -> None:
    """
    Configure application-wide structured logging.
    """

    root_logger = logging.getLogger()

    # Avoid duplicate handlers when the app reloads
    if root_logger.handlers:
        root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    formatter = JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )

    handler.setFormatter(formatter)

    root_logger.addHandler(handler)

    root_logger.setLevel(settings.LOG_LEVEL)


logger = logging.getLogger("agentdesk")