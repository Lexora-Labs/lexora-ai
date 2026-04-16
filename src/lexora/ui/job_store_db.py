"""SQLite persistence for UI translation jobs."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List


class JobStoreDB:
    """Lightweight SQLite repository for ``TranslationJob`` rows."""

    def __init__(self, db_path: str) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS translation_jobs (
                    id TEXT PRIMARY KEY,
                    book_title TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    target_lang TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    parameters_json TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    duration_ms INTEGER,
                    total_docs INTEGER,
                    docs_translated INTEGER,
                    error TEXT,
                    output_path TEXT,
                    log_cursor_start INTEGER,
                    log_cursor_end INTEGER
                )
                """
            )

    def load_jobs(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM translation_jobs ORDER BY created_at DESC"
            ).fetchall()
        jobs: List[Dict[str, Any]] = []
        for row in rows:
            jobs.append(
                {
                    "id": str(row["id"]),
                    "book_title": str(row["book_title"]),
                    "provider": str(row["provider"]),
                    "model": str(row["model"]),
                    "target_lang": str(row["target_lang"]),
                    "status": str(row["status"]),
                    "progress": float(row["progress"]),
                    "created_at": str(row["created_at"]),
                    "parameters": self._decode_parameters(str(row["parameters_json"])),
                    "started_at": row["started_at"],
                    "completed_at": row["completed_at"],
                    "duration_ms": row["duration_ms"],
                    "total_docs": row["total_docs"],
                    "docs_translated": row["docs_translated"],
                    "error": row["error"],
                    "output_path": row["output_path"],
                    "log_cursor_start": row["log_cursor_start"],
                    "log_cursor_end": row["log_cursor_end"],
                }
            )
        return jobs

    def upsert_job(self, job: Any) -> None:
        payload: Dict[str, Any] = {
            "id": getattr(job, "id"),
            "book_title": getattr(job, "book_title"),
            "provider": getattr(job, "provider"),
            "model": getattr(job, "model"),
            "target_lang": getattr(job, "target_lang"),
            "status": getattr(job, "status"),
            "progress": float(getattr(job, "progress")),
            "created_at": getattr(job, "created_at"),
            "started_at": getattr(job, "started_at"),
            "completed_at": getattr(job, "completed_at"),
            "duration_ms": getattr(job, "duration_ms"),
            "total_docs": getattr(job, "total_docs"),
            "docs_translated": getattr(job, "docs_translated"),
            "error": getattr(job, "error"),
            "output_path": getattr(job, "output_path"),
            "log_cursor_start": getattr(job, "log_cursor_start"),
            "log_cursor_end": getattr(job, "log_cursor_end"),
        }
        payload["parameters_json"] = json.dumps(
            getattr(job, "parameters", {}) or {},
            ensure_ascii=True,
            sort_keys=True,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO translation_jobs (
                    id, book_title, provider, model, target_lang, status, progress,
                    created_at, parameters_json, started_at, completed_at, duration_ms,
                    total_docs, docs_translated, error, output_path, log_cursor_start, log_cursor_end
                ) VALUES (
                    :id, :book_title, :provider, :model, :target_lang, :status, :progress,
                    :created_at, :parameters_json, :started_at, :completed_at, :duration_ms,
                    :total_docs, :docs_translated, :error, :output_path, :log_cursor_start, :log_cursor_end
                )
                ON CONFLICT(id) DO UPDATE SET
                    book_title=excluded.book_title,
                    provider=excluded.provider,
                    model=excluded.model,
                    target_lang=excluded.target_lang,
                    status=excluded.status,
                    progress=excluded.progress,
                    created_at=excluded.created_at,
                    parameters_json=excluded.parameters_json,
                    started_at=excluded.started_at,
                    completed_at=excluded.completed_at,
                    duration_ms=excluded.duration_ms,
                    total_docs=excluded.total_docs,
                    docs_translated=excluded.docs_translated,
                    error=excluded.error,
                    output_path=excluded.output_path,
                    log_cursor_start=excluded.log_cursor_start,
                    log_cursor_end=excluded.log_cursor_end
                """,
                payload,
            )

    def delete_job(self, job_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM translation_jobs WHERE id = ?", (job_id,))

    @staticmethod
    def _decode_parameters(raw: str) -> Dict[str, object]:
        try:
            value = json.loads(raw)
        except Exception:
            return {}
        return value if isinstance(value, dict) else {}
