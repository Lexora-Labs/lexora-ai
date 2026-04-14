"""Centralized logging bootstrap for Lexora AI."""

from __future__ import annotations

import logging
import os
from collections import deque
from logging.handlers import RotatingFileHandler
from pathlib import Path
from threading import Lock
from typing import Deque, Dict, List
from uuid import uuid4

DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"
DEFAULT_UI_BUFFER_SIZE = 500
DEFAULT_UI_MIN_LEVEL = "INFO"


_ui_buffer: Deque[Dict[str, object]] = deque()
_ui_lock = Lock()
_ui_next_event_id = 0


class ContextFilter(logging.Filter):
    """Attach shared run context fields to records."""

    def __init__(self, run_id: str, provider: str):
        super().__init__()
        self.run_id = run_id
        self.provider = provider

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "run_id"):
            record.run_id = self.run_id
        if not hasattr(record, "provider"):
            record.provider = self.provider
        return True


class UILogBufferHandler(logging.Handler):
    """In-memory bounded buffer handler for UI log rendering."""

    def __init__(self, max_events: int, min_level: int):
        super().__init__(level=min_level)
        self.max_events = max(1, max_events)

    def emit(self, record: logging.LogRecord) -> None:
        global _ui_next_event_id
        try:
            with _ui_lock:
                _ui_next_event_id += 1
                event_id = _ui_next_event_id
            payload = {
                "id": event_id,
                "timestamp": self.formatter.formatTime(record, self.formatter.datefmt)
                if self.formatter
                else None,
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "event": getattr(record, "event", None),
                "fields": getattr(record, "fields", {}),
                "run_id": getattr(record, "run_id", None),
                "provider": getattr(record, "provider", None),
            }
            with _ui_lock:
                _ui_buffer.append(payload)
                while len(_ui_buffer) > self.max_events:
                    _ui_buffer.popleft()
        except Exception:
            self.handleError(record)


def get_ui_log_events() -> List[Dict[str, object]]:
    """Return a snapshot copy of buffered UI log events."""
    with _ui_lock:
        return list(_ui_buffer)


def clear_ui_log_events() -> None:
    """Clear in-memory UI log event buffer."""
    global _ui_next_event_id
    with _ui_lock:
        _ui_buffer.clear()
        _ui_next_event_id = 0


def get_ui_log_events_since(last_event_id: int) -> List[Dict[str, object]]:
    """Return buffered UI log events newer than the provided event id."""
    with _ui_lock:
        return [event for event in _ui_buffer if int(event.get("id", 0)) > last_event_id]


def parse_log_targets(raw_targets: str | None) -> List[str]:
    """Parse comma-separated target list into normalized sink names."""
    if not raw_targets:
        return ["console"]

    targets = [token.strip().lower() for token in raw_targets.split(",") if token.strip()]
    return targets or ["console"]


def _parse_level(raw_level: str | None) -> int:
    normalized = (raw_level or "INFO").strip().upper()
    return getattr(logging, normalized, logging.INFO)


def build_logging_config(
    level: str | None = None,
    targets: str | None = None,
    log_file_path: str | None = None,
    file_max_bytes: int | None = None,
    file_backup_count: int | None = None,
    provider: str | None = None,
    run_id: str | None = None,
) -> dict:
    """Build resolved logging config from args + env defaults."""
    resolved_level = level or os.getenv("LEXORA_LOG_LEVEL", "INFO")
    resolved_targets = targets or os.getenv("LEXORA_LOG_TARGETS", "console")
    resolved_log_file_path = log_file_path or os.getenv("LEXORA_LOG_FILE_PATH", "logs/lexora-%DATE%.log")
    resolved_file_max_bytes = file_max_bytes or int(os.getenv("LEXORA_LOG_FILE_MAX_BYTES", "5242880"))
    resolved_file_backup_count = file_backup_count or int(os.getenv("LEXORA_LOG_FILE_BACKUP_COUNT", "3"))
    resolved_provider = provider or os.getenv("LEXORA_LOG_PROVIDER", "auto")
    resolved_run_id = run_id or os.getenv("LEXORA_LOG_RUN_ID", uuid4().hex[:8])

    return {
        "level": resolved_level,
        "targets": parse_log_targets(resolved_targets),
        "log_file_path": resolved_log_file_path,
        "file_max_bytes": resolved_file_max_bytes,
        "file_backup_count": resolved_file_backup_count,
        "provider": resolved_provider,
        "run_id": resolved_run_id,
        "azure_connection_string": os.getenv("LEXORA_AZURE_MONITOR_CONNECTION_STRING", ""),
        "aws_log_group": os.getenv("LEXORA_AWS_LOG_GROUP", ""),
        "aws_log_stream": os.getenv("LEXORA_AWS_LOG_STREAM", ""),
        "aws_region": os.getenv("LEXORA_AWS_REGION", ""),
        "ui_buffer_size": int(os.getenv("LEXORA_LOG_UI_BUFFER_SIZE", str(DEFAULT_UI_BUFFER_SIZE))),
        "ui_min_level": os.getenv("LEXORA_LOG_UI_MIN_LEVEL", DEFAULT_UI_MIN_LEVEL),
    }


def _sanitize_filename_token(value: str) -> str:
    """Keep token values filesystem-safe across platforms."""
    safe = []
    for ch in value:
        if ch.isalnum() or ch in ("-", "_", "."):
            safe.append(ch)
        else:
            safe.append("-")
    return "".join(safe) or "unknown"


def _resolve_log_path(path_pattern: str, config: dict | None = None) -> Path:
    """Resolve log path tokens and return concrete path.

    Supported tokens:
    - `%DATE%`: `YYYY-MM-DD`
    - `%TIME%`: `HH-mm-ss`
    - `%DATETIME%`: `YYYY-MM-DD_HH-mm-ss`
    - `%LEVEL%`: normalized log level
    - `%RUN_ID%`: run identifier
    - `%PROVIDER%`: provider name
    - `%PID%`: current process id
    """
    from datetime import datetime

    now = datetime.now()
    resolved_level = (config or {}).get("level", "INFO")
    resolved_provider = (config or {}).get("provider", "auto")
    resolved_run_id = (config or {}).get("run_id", "run")
    replacements = {
        "%DATE%": now.strftime("%Y-%m-%d"),
        "%TIME%": now.strftime("%H-%M-%S"),
        "%DATETIME%": now.strftime("%Y-%m-%d_%H-%M-%S"),
        "%LEVEL%": _sanitize_filename_token(str(resolved_level).upper()),
        "%RUN_ID%": _sanitize_filename_token(str(resolved_run_id)),
        "%PROVIDER%": _sanitize_filename_token(str(resolved_provider)),
        "%PID%": str(os.getpid()),
    }

    resolved = path_pattern
    for token, value in replacements.items():
        resolved = resolved.replace(token, value)

    path = Path(resolved)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _create_console_handler(formatter: logging.Formatter) -> logging.Handler:
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    return handler


def _create_file_handler(config: dict, formatter: logging.Formatter) -> logging.Handler:
    log_path = _resolve_log_path(config["log_file_path"], config)
    handler = RotatingFileHandler(
        log_path,
        maxBytes=config["file_max_bytes"],
        backupCount=config["file_backup_count"],
        encoding="utf-8",
    )
    handler.setFormatter(formatter)
    return handler


def _create_ui_handler(config: dict, formatter: logging.Formatter) -> logging.Handler:
    handler = UILogBufferHandler(
        max_events=int(config.get("ui_buffer_size") or DEFAULT_UI_BUFFER_SIZE),
        min_level=_parse_level(str(config.get("ui_min_level") or DEFAULT_UI_MIN_LEVEL)),
    )
    handler.setFormatter(formatter)
    return handler


def _try_create_azure_handler(config: dict, formatter: logging.Formatter) -> logging.Handler | None:
    connection_string = config.get("azure_connection_string") or ""
    if not connection_string:
        logging.getLogger("lexora.logging").warning(
            "Azure sink selected but LEXORA_AZURE_MONITOR_CONNECTION_STRING is not set"
        )
        return None

    try:
        from opencensus.ext.azure.log_exporter import AzureLogHandler
    except Exception:
        logging.getLogger("lexora.logging").warning(
            "Azure sink requires opencensus-ext-azure package; sink skipped"
        )
        return None

    handler = AzureLogHandler(connection_string=connection_string)
    handler.setFormatter(formatter)
    return handler


def _try_create_aws_handler(config: dict, formatter: logging.Formatter) -> logging.Handler | None:
    log_group = config.get("aws_log_group") or ""
    if not log_group:
        logging.getLogger("lexora.logging").warning(
            "AWS sink selected but LEXORA_AWS_LOG_GROUP is not set"
        )
        return None

    try:
        import watchtower
    except Exception:
        logging.getLogger("lexora.logging").warning(
            "AWS sink requires watchtower package; sink skipped"
        )
        return None

    handler = watchtower.CloudWatchLogHandler(
        log_group_name=log_group,
        stream_name=config.get("aws_log_stream") or "lexora-ai",
        create_log_group=True,
    )
    handler.setFormatter(formatter)
    return handler


def configure_logging(config: dict | None = None) -> logging.Logger:
    """Configure root logger handlers based on resolved config."""
    resolved = config or build_logging_config()

    root = logging.getLogger()
    root.handlers.clear()
    root.filters.clear()
    root.setLevel(_parse_level(resolved.get("level")))
    context_filter = ContextFilter(
        run_id=str(resolved.get("run_id", "run")),
        provider=str(resolved.get("provider", "auto")),
    )

    formatter = logging.Formatter(DEFAULT_LOG_FORMAT, datefmt=DEFAULT_DATE_FORMAT)

    valid_targets = {"console", "file", "azure", "aws", "ui"}
    for target in resolved.get("targets", ["console"]):
        if target == "console":
            handler = _create_console_handler(formatter)
            handler.addFilter(context_filter)
            root.addHandler(handler)
        elif target == "file":
            handler = _create_file_handler(resolved, formatter)
            handler.addFilter(context_filter)
            root.addHandler(handler)
        elif target == "azure":
            handler = _try_create_azure_handler(resolved, formatter)
            if handler:
                handler.addFilter(context_filter)
                root.addHandler(handler)
        elif target == "aws":
            handler = _try_create_aws_handler(resolved, formatter)
            if handler:
                handler.addFilter(context_filter)
                root.addHandler(handler)
        elif target == "ui":
            handler = _create_ui_handler(resolved, formatter)
            handler.addFilter(context_filter)
            root.addHandler(handler)
        elif target not in valid_targets:
            logging.getLogger("lexora.logging").warning(
                "Unknown log sink target '%s' ignored", target
            )

    if not root.handlers:
        fallback_handler = _create_console_handler(formatter)
        fallback_handler.addFilter(context_filter)
        root.addHandler(fallback_handler)
        root.warning("No active log handlers found; defaulted to console")

    logger = logging.getLogger("lexora")
    logger.debug("Logging initialized with targets=%s", resolved.get("targets"))
    return logger
