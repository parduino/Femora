"""Simple submission file mapping and private interactive connection tests."""

import sys
from types import SimpleNamespace
from unittest.mock import Mock
from zipfile import ZipFile

import pytest
import femora as fm
from femora.jobs.platforms import TACCPlatform


def test_submit_maps_external_files_without_executing_source(tmp_path):
    source = tmp_path / "model" / "study.py"
    source.parent.mkdir()
    source.write_text("raise RuntimeError('do not run locally')\n")
    motion = tmp_path / "motion.txt"
    motion.write_text("motion")
    target = Mock()

    def inspect_bundle(archive, settings):
        with ZipFile(archive) as zipped:
            assert zipped.read("data/input/motion.txt") == b"motion"
        return "job"

    target.submit.side_effect = inspect_bundle
    assert fm.submit(source=source, platform=target, settings={},
                     files={"input/motion.txt": motion}) == "job"
    with pytest.raises(ValueError):
        fm.submit(source=source, platform=target, settings={}, files={"../escape": motion})
    assert target.submit.call_count == 1


def test_login_clears_password_and_retains_tokens(monkeypatch):
    import getpass
    client = Mock()
    factory = Mock(return_value=client)
    monkeypatch.setitem(sys.modules, "tapipy.tapis", SimpleNamespace(Tapis=factory))
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _: "user")
    monkeypatch.setattr(getpass, "getpass", lambda _: "secret")
    target = TACCPlatform.login(app_id="app")
    assert client.password is None
    assert client.access_token is not None
    assert str(target.input_directory) == "user/femora-workflows/submissions"
    client.jobs.submitJob.assert_not_called()


def test_login_failure_redacts_details(monkeypatch):
    import getpass
    client = Mock()
    client.get_tokens.side_effect = RuntimeError("secret")
    monkeypatch.setitem(sys.modules, "tapipy.tapis", SimpleNamespace(Tapis=Mock(return_value=client)))
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _: "user")
    monkeypatch.setattr(getpass, "getpass", lambda _: "secret")
    with pytest.raises(RuntimeError, match="private details omitted") as error:
        TACCPlatform.login(app_id="app")
    assert "secret" not in str(error.value)
    assert client.password is client.access_token is client.refresh_token is None


def test_login_requires_terminal(monkeypatch):
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    with pytest.raises(ValueError, match="terminal"):
        TACCPlatform.login(app_id="app")
