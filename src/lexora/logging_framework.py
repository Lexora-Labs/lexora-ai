"""Centralized logging bootstrap for Lexora AI."""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import List
from uuid import uuid4

DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


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
    root.setLevel(_parse_level(resolved.get("level")))

    formatter = logging.Formatter(DEFAULT_LOG_FORMAT, datefmt=DEFAULT_DATE_FORMAT)

    valid_targets = {"console", "file", "azure", "aws", "ui"}
    for target in resolved.get("targets", ["console"]):
        if target == "console":
            root.addHandler(_create_console_handler(formatter))
        elif target == "file":
            root.addHandler(_create_file_handler(resolved, formatter))
        elif target == "azure":
            handler = _try_create_azure_handler(resolved, formatter)
            if handler:
                root.addHandler(handler)
        elif target == "aws":
            handler = _try_create_aws_handler(resolved, formatter)
            if handler:
                root.addHandler(handler)
        elif target == "ui":
            # UI sink is handled by UI runtime adapter in later task.
            continue
        elif target not in valid_targets:
            logging.getLogger("lexora.logging").warning(
                "Unknown log sink target '%s' ignored", target
            )

    if not root.handlers:
        root.addHandler(_create_console_handler(formatter))
        root.warning("No active log handlers found; defaulted to console")

    logger = logging.getLogger("lexora")
    logger.debug("Logging initialized with targets=%s", resolved.get("targets"))
    return logger
