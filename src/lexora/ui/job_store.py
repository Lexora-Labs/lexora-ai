"""Shared in-memory job store for Translate/Jobs screens."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any, Callable, Dict, List, Optional


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class TranslationJob:
    """One translation job/run. ``id`` is the canonical run identifier (JobId = RunId)."""

    id: str
    book_title: str
    provider: str
    model: str
    target_lang: str
    status: str
    progress: float
    created_at: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None
    total_docs: Optional[int] = None
    docs_translated: Optional[int] = None
    error: Optional[str] = None
    output_path: Optional[str] = None
    log_cursor_start: Optional[int] = None
    log_cursor_end: Optional[int] = None

    @property
    def run_id(self) -> str:
        return self.id


class JobStore:
    """Thread-safe in-memory job state with change subscriptions."""

    def __init__(self) -> None:
        self._jobs: Dict[str, TranslationJob] = {}
        self._listeners: List[Callable[[], None]] = []
        self._lock = Lock()

    def subscribe(self, callback: Callable[[], None]) -> Callable[[], None]:
        with self._lock:
            self._listeners.append(callback)

        def _unsubscribe() -> None:
            with self._lock:
                if callback in self._listeners:
                    self._listeners.remove(callback)

        return _unsubscribe

    def snapshot(self) -> List[TranslationJob]:
        with self._lock:
            return sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)

    def create_job(
        self,
        *,
        job_id: str,
        book_title: str,
        provider: str,
        model: str,
        target_lang: str,
        status: str = "in_progress",
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        with self._lock:
            self._jobs[job_id] = TranslationJob(
                id=job_id,
                book_title=book_title,
                provider=provider,
                model=model,
                target_lang=target_lang,
                status=status,
                progress=0.0,
                created_at=_now_str(),
                parameters=copy.deepcopy(parameters or {}),
            )
        self._notify()

    def mark_run_started(self, job_id: str) -> None:
        """Record wall-clock start when the worker thread actually begins the run."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or job.started_at:
                return
            job.started_at = _now_str()
        self._notify()

    def update_doc_counts(
        self,
        job_id: str,
        *,
        total_docs: Optional[int] = None,
        docs_translated: Optional[int] = None,
    ) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            if total_docs is not None:
                job.total_docs = max(0, int(total_docs))
            if docs_translated is not None:
                job.docs_translated = max(0, int(docs_translated))
        self._notify()

    def set_doc_progress(self, job_id: str, *, docs_completed: int, docs_total: int) -> None:
        """Update in-progress bar; denominator is ``docs_total + 1`` for extract/repack overhead."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or docs_total <= 0:
                return
            real_t = max(1, int(docs_total))
            c = max(0, min(int(docs_completed), real_t))
            job.total_docs = real_t
            job.docs_translated = c
            if job.status == "in_progress":
                effective = real_t + 1
                numerator = 1 + min(c, real_t)
                job.progress = min(0.999, numerator / float(effective))
        self._notify()

    def set_output_path(self, job_id: str, path: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            job.output_path = path
        self._notify()

    def set_log_cursor_start(self, job_id: str, cursor: int) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            job.log_cursor_start = max(0, int(cursor))
        self._notify()

    def set_log_cursor_end(self, job_id: str, cursor: int) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            job.log_cursor_end = max(0, int(cursor))
        self._notify()

    def get_job(self, job_id: str) -> Optional[TranslationJob]:
        with self._lock:
            return self._jobs.get(job_id)

    def prepare_rerun(self, job_id: str, *, parameters: Optional[Dict[str, Any]] = None) -> bool:
        """Reset a finished/cancelled job so it can be rerun in-place."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            if parameters is not None:
                job.parameters = copy.deepcopy(parameters)
            job.status = "queued"
            job.progress = 0.0
            job.started_at = None
            job.completed_at = None
            job.duration_ms = None
            job.docs_translated = 0 if job.total_docs is not None else None
            job.error = None
            job.log_cursor_start = None
            job.log_cursor_end = None
        self._notify()
        return True

    def delete_job(self, job_id: str) -> tuple[bool, str]:
        """Delete a job unless it is actively running."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False, "Job not found."
            if job.status == "in_progress":
                return False, "Stop/cancel a running job before deleting."
            del self._jobs[job_id]
        self._notify()
        return True, "Job deleted."

    def set_status(
        self,
        job_id: str,
        *,
        status: str,
        progress: Optional[float] = None,
        error: Optional[str] = None,
        duration_ms: Optional[int] = None,
        total_docs: Optional[int] = None,
        docs_translated: Optional[int] = None,
    ) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            job.status = status
            if progress is not None:
                job.progress = max(0.0, min(1.0, progress))
            if error is not None:
                job.error = error
            if total_docs is not None:
                job.total_docs = max(0, int(total_docs))
            if docs_translated is not None:
                job.docs_translated = max(0, int(docs_translated))
            if status in {"completed", "failed", "cancelled"}:
                job.completed_at = _now_str()
                if duration_ms is not None:
                    job.duration_ms = max(0, int(duration_ms))
                if status == "completed":
                    job.progress = 1.0
        self._notify()

    def _notify(self) -> None:
        listeners: List[Callable[[], None]]
        with self._lock:
            listeners = list(self._listeners)
        for callback in listeners:
            try:
                callback()
            except Exception:
                continue
