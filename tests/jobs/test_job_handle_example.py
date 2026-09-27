"""Offline acceptance-helper checks, with no network or credentials."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock


def helper():
    path = Path(__file__).parents[2] / "examples/workflows/tacc_job_handle.py"
    spec = importlib.util.spec_from_file_location("job_handle_example", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def job(state):
    handle = Mock()
    handle.id = "test-uuid"
    handle.status.return_value = SimpleNamespace(state=state, native_state=state.upper())
    return handle


def test_check_downloads_completed_job(tmp_path):
    handle = job("succeeded")
    output = tmp_path / "output.zip"
    assert helper().check_job(handle, output) == 0
    handle.download.assert_called_once_with(output)
    handle.cancel.assert_not_called()


def test_running_job_not_downloaded(tmp_path):
    handle = job("running")
    assert helper().check_job(handle, tmp_path / "output.zip") == 1
    handle.download.assert_not_called()
    handle.cancel.assert_not_called()


def test_status_only():
    handle = job("pending")
    assert helper().check_job(handle) == 0
    handle.download.assert_not_called()
    handle.cancel.assert_not_called()


def test_cancel_requires_matching_uuid():
    handle = job("pending")
    assert helper().cancel_job(handle, confirm=lambda _: "yes") == 1
    handle.cancel.assert_not_called()
    assert helper().cancel_job(handle, confirm=lambda _: "test-uuid") == 0
    handle.cancel.assert_called_once_with()


def test_terminal_job_not_cancelled():
    handle = job("succeeded")
    confirm = Mock()
    assert helper().cancel_job(handle, confirm=confirm) == 1
    confirm.assert_not_called()
    handle.cancel.assert_not_called()
