"""
Shared structured JSON logging configuration for all agents.
Usage:
    from app.core.logging_config import setup_logging
    logger = setup_logging("agent_name")
"""
import logging
import json
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Formats log records as JSON for structured logging (ELK/Grafana/CloudWatch)."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields (e.g., session_id, request_id)
        for key in ("session_id", "request_id", "agent", "intent", "duration_ms"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(service_name: str, level: str = "INFO") -> logging.Logger:
    """
    Configure structured JSON logging for a service.

    Args:
        service_name: Name of the service (e.g., "host_agent")
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Avoid duplicate handlers on reload
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

    # Prevent propagation to root logger (avoids duplicate logs)
    logger.propagate = False

    return logger
