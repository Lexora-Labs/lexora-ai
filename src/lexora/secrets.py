"""Local encrypted secret storage with env-first resolution."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_db_path() -> Path:
    configured = (os.getenv("LEXORA_UI_JOBS_DB") or "").strip()
    if configured:
        return Path(configured)
    return Path(".lexora") / "jobs.sqlite3"


def _resolve_key_path() -> Path:
    configured = (os.getenv("LEXORA_SECRETS_KEY_PATH") or "").strip()
    if configured:
        return Path(configured)
    return Path(".lexora") / "secrets.key"


def _ensure_fernet() -> Fernet:
    key_path = _resolve_key_path()
    key_path.parent.mkdir(parents=True, exist_ok=True)
    if key_path.exists():
        key = key_path.read_bytes()
    else:
        key = Fernet.generate_key()
        key_path.write_bytes(key)
    return Fernet(key)


def _connect() -> sqlite3.Connection:
    db_path = _resolve_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_secrets (
            name TEXT PRIMARY KEY,
            value_encrypted TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_settings (
            name TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    return conn


def set_secret(name: str, value: str) -> None:
    cleaned = value.strip()
    if not cleaned:
        return
    f = _ensure_fernet()
    encrypted = f.encrypt(cleaned.encode("utf-8")).decode("utf-8")
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO app_secrets(name, value_encrypted, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                value_encrypted=excluded.value_encrypted,
                updated_at=excluded.updated_at
            """,
            (name, encrypted, _utc_now()),
        )


def get_secret(name: str) -> Optional[str]:
    env_val = os.getenv(name)
    if env_val:
        return env_val
    with _connect() as conn:
        row = conn.execute(
            "SELECT value_encrypted FROM app_secrets WHERE name = ?",
            (name,),
        ).fetchone()
    if not row:
        return None
    f = _ensure_fernet()
    try:
        return f.decrypt(str(row[0]).encode("utf-8")).decode("utf-8")
    except Exception:
        return None


def get_secret_first(names: Iterable[str]) -> Optional[str]:
    for name in names:
        value = get_secret(name)
        if value:
            return value
    return None


def has_secret(name: str) -> bool:
    return bool(get_secret(name))


def set_setting(name: str, value: str) -> None:
    cleaned = (value or "").strip()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO app_settings(name, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                value=excluded.value,
                updated_at=excluded.updated_at
            """,
            (name, cleaned, _utc_now()),
        )


def get_setting(name: str, default: Optional[str] = None) -> Optional[str]:
    env_val = os.getenv(name)
    if env_val is not None and str(env_val).strip():
        return str(env_val).strip()
    with _connect() as conn:
        row = conn.execute(
            "SELECT value FROM app_settings WHERE name = ?",
            (name,),
        ).fetchone()
    if not row:
        return default
    value = str(row[0]).strip()
    return value if value else default


def get_setting_first(names: Iterable[str], default: Optional[str] = None) -> Optional[str]:
    for name in names:
        value = get_setting(name)
        if value is not None and str(value).strip():
            return str(value).strip()
    return default


def delete_secret(name: str) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM app_secrets WHERE name = ?", (name,))


def delete_setting(name: str) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM app_settings WHERE name = ?", (name,))
