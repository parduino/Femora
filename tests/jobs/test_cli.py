"""The installed shortcut and module invocation share the jobs CLI."""

import json
from unittest.mock import Mock

import pytest

from femora.cli import main
from femora.jobs.__main__ import main as jobs_main


def test_dispatch_preserves_arguments(monkeypatch):
    dispatch = Mock()
    monkeypatch.setattr("femora.jobs.__main__.main", dispatch)
    main(["jobs", "track", "--app-id", "custom-app"])
    dispatch.assert_called_once_with(["track", "--app-id", "custom-app"], prog="femora jobs")


@pytest.mark.parametrize("arguments, expected", [
    (["--help"], "usage: femora"),
    (["jobs", "--help"], "usage: femora jobs"),
    (["jobs", "track", "--help"], "usage: femora jobs track"),
])
def test_help(arguments, expected, capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(arguments)
    assert exit_info.value.code == 0
    assert expected in capsys.readouterr().out


def test_shortcut_and_module_use_same_local_registry(capsys):
    main(["jobs", "add", "existing-id", "--name", "study"])
    capsys.readouterr()
    main(["jobs", "list", "--json"])
    shortcut = json.loads(capsys.readouterr().out)
    jobs_main(["list", "--json"])
    original = json.loads(capsys.readouterr().out)
    assert shortcut == original
    assert shortcut[0]["name"] == "study"


def test_unknown_command_is_an_error():
    with pytest.raises(SystemExit) as exit_info:
        main(["unknown"])
    assert exit_info.value.code == 2
