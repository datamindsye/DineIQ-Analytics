"""Structured logging foundation for DineIQ Analytics."""

import logging
import sys


class StructuredFormatter(logging.Formatter):
    """Simple structured log formatter emitting readable standard or JSON formats."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record, self.datefmt)
        message = record.getMessage()
        log_entry = f"[{timestamp}] [{record.levelname:<8}] [{record.name}] {message}"
        if record.exc_info:
            log_entry += f"\n{self.formatException(record.exc_info)}"
        return log_entry


def setup_logging(log_level: str = "INFO") -> None:
    """Configure system wide logging with unified format."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Avoid duplicate handlers on reinitialization
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(numeric_level)
        formatter = StructuredFormatter(datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Obtain a named logger configured for the application."""
    return logging.getLogger(name)
