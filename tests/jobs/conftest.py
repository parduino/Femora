"""Job tests must not alter the user's persistent job registry."""

import pytest


@pytest.fixture(autouse=True)
def isolated_job_registry(tmp_path, monkeypatch):
    monkeypatch.setenv("FEMORA_JOBS_DB", str(tmp_path / "test-jobs.sqlite3"))
