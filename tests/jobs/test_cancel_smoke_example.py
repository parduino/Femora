"""Offline checks for the disposable cancellation workflow."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock


def helper():
    path = Path(__file__).parents[2] / "examples/workflows/tacc_cancel_smoke.py"
    spec = importlib.util.spec_from_file_location("cancel_smoke_example", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_wait_script_is_bounded(tmp_path):
    helper().create(SimpleNamespace(workspace=tmp_path))
    script = (tmp_path / "models/wait.tcl").read_text()
    assert "$i < 60" in script
    assert "after 5000" in script
    assert "flush stdout" in script
    assert "analyze" not in script


def test_completion_marker(tmp_path):
    helper().completed(SimpleNamespace(output_dir=tmp_path))
    assert "completed normally" in (tmp_path / "not-cancelled.txt").read_text()


def test_factory_only_defines_stages(monkeypatch):
    fm = Mock()
    monkeypatch.setitem(__import__("sys").modules, "femora", fm)
    workflow = helper().build_workflow()
    assert workflow is fm.Workflow.return_value
    assert [call.args[0] for call in workflow.add.call_args_list] == [
        "create", "wait", "after-wait",
    ]
    fm.tasks.OpenSees.assert_called_once_with("disposable", "models/wait.tcl", ranks=2)
    fm.submit.assert_not_called()
