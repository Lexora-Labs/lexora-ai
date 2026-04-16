from __future__ import annotations

import os
from pathlib import Path

from lexora.secrets import get_secret, set_secret


def test_secret_store_env_precedence_then_sqlite_fallback(tmp_path: Path) -> None:
    db_path = tmp_path / "jobs.sqlite3"
    key_path = tmp_path / "secrets.key"
    os.environ["LEXORA_UI_JOBS_DB"] = str(db_path)
    os.environ["LEXORA_SECRETS_KEY_PATH"] = str(key_path)

    try:
        set_secret("OPENAI_API_KEY", "sqlite-secret")
        assert get_secret("OPENAI_API_KEY") == "sqlite-secret"

        os.environ["OPENAI_API_KEY"] = "env-secret"
        assert get_secret("OPENAI_API_KEY") == "env-secret"
    finally:
        os.environ.pop("LEXORA_UI_JOBS_DB", None)
        os.environ.pop("LEXORA_SECRETS_KEY_PATH", None)
        os.environ.pop("OPENAI_API_KEY", None)
