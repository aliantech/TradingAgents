from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest


_TEST_DB_DIR = Path(tempfile.mkdtemp(prefix="aquantlens-backend-tests-"))
_TEST_DB_PATH = _TEST_DB_DIR / "aquantlens_test.db"

if os.environ.get("AQUANTLENS_ALLOW_RUNTIME_DB_TESTS") != "1":
    os.environ["AQUANTLENS_DATABASE_URL"] = f"sqlite:///{_TEST_DB_PATH}"


@pytest.fixture(autouse=True)
def forbid_runtime_database_in_tests():
    from app.db import session as db_session

    database_url = str(db_session.engine.url)
    assert "aquantlens_us.db" not in database_url, (
        "Tests must not write to the runtime database. "
        "Set AQUANTLENS_ALLOW_RUNTIME_DB_TESTS=1 only for an explicit manual smoke run."
    )
