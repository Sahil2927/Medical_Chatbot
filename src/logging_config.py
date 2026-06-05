import logging
import os

from src.request_context import RequestIdFilter


def configure_logging() -> None:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    log_format = os.getenv(
        "LOG_FORMAT",
        "%(asctime)s level=%(levelname)s request_id=%(request_id)s %(name)s: %(message)s",
    )

    root = logging.getLogger()
    if root.handlers:
        return

    handler = logging.StreamHandler()
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(logging.Formatter(log_format))
    root.addHandler(handler)
    root.setLevel(level)
