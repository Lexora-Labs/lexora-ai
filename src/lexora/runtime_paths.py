"""Resolve Lexora-AI repository (or PyInstaller / ``flet pack`` bundle) root paths."""

from __future__ import annotations

import sys
from pathlib import Path


def lexora_repo_root(*, anchor_file: Path | None = None) -> Path:
    """Return repo root in development or the frozen bundle root when packaged.

    In a ``flet pack`` / PyInstaller build, ship ``assets/`` and ``lexora-ai-icon.ico``
    at the bundle root (``sys._MEIPASS`` for one-file) via ``--add-data``.
    """
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent

    start = anchor_file.resolve() if anchor_file is not None else Path(__file__).resolve()
    for ancestor in [start] + list(start.parents):
        if (ancestor / "README.md").is_file() and (ancestor / "requirements.txt").is_file():
            return ancestor
    # Fallback: lexora/ui/main.py -> repo is parents[3]
    return Path(__file__).resolve().parents[2]
