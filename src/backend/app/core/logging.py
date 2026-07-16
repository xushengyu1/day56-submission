from __future__ import annotations

import logging

from app.audit.projection import redact_metadata


class StructuredLogger:
    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def info(self, message: str, **fields: object) -> None:
        self._logger.info(message, extra={"fields": redact_metadata(fields)})

    def warning(self, message: str, **fields: object) -> None:
        self._logger.warning(message, extra={"fields": redact_metadata(fields)})

    def error(self, message: str, **fields: object) -> None:
        self._logger.error(message, extra={"fields": redact_metadata(fields)})


def get_logger(name: str) -> StructuredLogger:
    return StructuredLogger(logging.getLogger(name))
