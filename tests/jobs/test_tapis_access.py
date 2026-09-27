"""Read-only access checks with fake clients, never live credentials."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace


def helper():
    path = Path(__file__).parents[2] / "deploy/tapis/check_access.py"
    spec = importlib.util.spec_from_file_location("check_access", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_checks_only_expected_systems(capsys):
    calls = []

    def get_system(*, systemId):
        calls.append(systemId)
        return SimpleNamespace(enabled=True, effectiveUserId="${apiUserId}")

    client = SimpleNamespace(systems=SimpleNamespace(getSystem=get_system))
    assert helper().check_systems(client) == 0
    assert calls == ["stampede3", "designsafe.storage.default"]
    assert "does not prove" in capsys.readouterr().out


def test_errors_do_not_print_exception_secrets(capsys):
    def get_system(**kwargs):
        raise RuntimeError("secret-password-and-token")

    client = SimpleNamespace(systems=SimpleNamespace(getSystem=get_system))
    assert helper().check_systems(client) == 1
    assert "secret-password" not in capsys.readouterr().out


def test_http_error_is_summarized():
    error = RuntimeError("secret")
    error.response = SimpleNamespace(status_code=403)
    assert helper().error_summary(error) == "HTTP 403"


def test_file_checks_use_root_relative_paths(capsys):
    calls = []
    client = SimpleNamespace(
        systems=SimpleNamespace(getSystem=lambda **kw: SimpleNamespace(rootDir="/work2")),
        files=SimpleNamespace(listFiles=lambda **kw: calls.append(kw)),
    )
    assert helper().check_files(client, "testuser", "/work2/shared/femora") == 0
    assert calls == [
        dict(systemId="stampede3", path="shared/femora", limit=5),
        dict(systemId="designsafe.storage.default", path="testuser", limit=5),
    ]
    assert "does not prove write" in capsys.readouterr().out


def test_file_failure_is_redacted_and_other_system_still_checked(capsys):
    calls = []

    def listing(**kwargs):
        calls.append(kwargs["systemId"])
        raise RuntimeError("secret-token")

    client = SimpleNamespace(
        systems=SimpleNamespace(getSystem=lambda **kw: SimpleNamespace(rootDir="/")),
        files=SimpleNamespace(listFiles=listing),
    )
    assert helper().check_files(client, "testuser", "/work2/shared") == 1
    assert len(calls) == 2
    assert "secret-token" not in capsys.readouterr().out


def test_native_path_outside_root_not_requested():
    calls = []
    client = SimpleNamespace(
        systems=SimpleNamespace(getSystem=lambda **kw: SimpleNamespace(rootDir="/scratch")),
        files=SimpleNamespace(listFiles=lambda **kw: calls.append(kw)),
    )
    assert helper().check_files(client, "testuser", "/work2/shared") == 1
    assert [call["systemId"] for call in calls] == ["designsafe.storage.default"]
