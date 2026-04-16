from __future__ import annotations

from pathlib import Path

from lexora.ui.job_store import JobStore


def test_job_store_persists_and_reloads_jobs(tmp_path: Path) -> None:
    db_path = tmp_path / "jobs.sqlite3"
    store = JobStore(db_path=str(db_path))
    store.create_job(
        job_id="run-1",
        book_title="book.epub",
        provider="OpenAI",
        model="gpt-4o-mini",
        target_lang="vi",
        status="queued",
        parameters={"mode": "replace", "input_file": "book.epub"},
    )
    store.set_status("run-1", status="completed", progress=1.0, duration_ms=500)

    reloaded = JobStore(db_path=str(db_path))
    jobs = reloaded.snapshot()
    assert len(jobs) == 1
    assert jobs[0].id == "run-1"
    assert jobs[0].status == "completed"
    assert jobs[0].parameters.get("mode") == "replace"


def test_job_store_marks_interrupted_runs_on_restart(tmp_path: Path) -> None:
    db_path = tmp_path / "jobs.sqlite3"
    store = JobStore(db_path=str(db_path))
    store.create_job(
        job_id="run-2",
        book_title="book2.epub",
        provider="OpenAI",
        model="gpt-4o-mini",
        target_lang="vi",
        status="in_progress",
        parameters={"mode": "bilingual"},
    )

    reloaded = JobStore(db_path=str(db_path))
    job = reloaded.get_job("run-2")
    assert job is not None
    assert job.status == "failed"
    assert job.error == "Interrupted by app restart."
