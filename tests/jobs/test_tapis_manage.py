"""Deployment control tests with no network or credentials."""

import importlib.util
import json
import io
import sys
from zipfile import ZipFile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest


def helper():
    spec = importlib.util.spec_from_file_location(
        "tapis_manage", Path(__file__).parents[2] / "deploy/tapis/manage.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def missing():
    error = RuntimeError("private request")
    error.response = SimpleNamespace(status_code=404)
    return error


def test_upload_creates_parents_and_sends_bytes(tmp_path):
    source = tmp_path / "app.zip"
    source.write_bytes(b"archive")
    files = Mock()
    files.listFiles.side_effect = missing()
    files.insert.side_effect = lambda **kw: kw["file"].read() == b"archive" or pytest.fail()
    helper().upload(SimpleNamespace(files=files), source, "stampede3", "a/b/app.zip")
    assert [c.kwargs["path"] for c in files.mkdir.call_args_list] == ["a", "a/b"]
    assert files.insert.call_args.kwargs["path"] == "a/b/app.zip"


def test_existing_destination_not_overwritten(tmp_path):
    source = tmp_path / "a"
    source.write_bytes(b"a")
    files = Mock()
    with pytest.raises(FileExistsError):
        helper().upload(SimpleNamespace(files=files), source, "system", "a")
    files.insert.assert_not_called()
    files.mkdir.assert_not_called()


def test_permissions_failure_does_not_trigger_upload(tmp_path):
    source = tmp_path / "a"
    source.write_bytes(b"a")
    files = Mock()
    error = missing()
    error.response.status_code = 403
    files.listFiles.side_effect = error
    with pytest.raises(RuntimeError):
        helper().upload(SimpleNamespace(files=files), source, "system", "a")
    files.insert.assert_not_called()


@pytest.mark.parametrize("path", ["../a", "/work/a", "a/../b", "C:\\a", ""])
def test_bad_remote_paths(path):
    with pytest.raises(ValueError):
        helper().remote_path(path)


def test_register_and_submit_separate(tmp_path, monkeypatch):
    path = tmp_path / "app.json"
    path.write_text(json.dumps(dict(id="pilot", version="0.1")))
    client = Mock()
    helper().perform(client, SimpleNamespace(command="register", definition=path))
    client.apps.createAppVersion.assert_called_once_with(id="pilot", version="0.1")
    client.jobs.submitJob.assert_not_called()
    path.write_text(json.dumps(dict(appId="pilot", appVersion="0.1")))
    submitter = Mock()
    submitter.submit_request.return_value = SimpleNamespace(uuid="job")
    monkeypatch.setattr("femora.jobs.platforms.TACCSubmitter", lambda c: submitter)
    helper().perform(client, SimpleNamespace(command="submit", definition=path))
    assert submitter.submit_request.call_args.args[0] == dict(appId="pilot", appVersion="0.1")
    client.jobs.submitJob.assert_not_called()


def test_status_only_reads():
    client = Mock()
    helper().perform(client, SimpleNamespace(command="status", uuid="test-uuid"))
    client.jobs.getJob.assert_called_once_with(jobUuid="test-uuid")
    client.jobs.submitJob.assert_not_called()


def test_status_history_shows_failure_without_write(capsys):
    client = Mock()
    client.jobs.getJob.return_value = SimpleNamespace(
        uuid="failed-job", status="FAILED", lastMessage="Scheduler rejected request")
    client.jobs.getJobHistory.return_value = [SimpleNamespace(
        created="now", event="JOB_NEW_STATUS", jobStatus="FAILED",
        description="Invalid allocation")]
    helper().perform(client, SimpleNamespace(command="status", uuid="failed-job", history=True))
    output = capsys.readouterr().out
    assert "Scheduler rejected request" in output
    assert "Invalid allocation" in output
    client.jobs.getJobHistory.assert_called_once_with(jobUuid="failed-job")
    client.jobs.submitJob.assert_not_called()
    client.apps.createAppVersion.assert_not_called()


def test_download_streams_zip_without_extraction(tmp_path, monkeypatch):
    buffer = io.BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr("results.zip", b"nested")
    response = Mock(status_code=200)
    response.iter_content.return_value = [buffer.getvalue()]
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    get = Mock(return_value=response)
    monkeypatch.setitem(sys.modules, "requests", SimpleNamespace(get=get))
    client = Mock()
    client.jobs.getJob.return_value = SimpleNamespace(status="FINISHED")
    client.access_token.access_token = "test-token"
    output = tmp_path / "output.zip"
    helper().download(client, "uuid", output)
    assert output.read_bytes() == buffer.getvalue()
    assert not (tmp_path / "results.zip").exists()
    assert get.call_args.kwargs["allow_redirects"] is False
    with pytest.raises(FileExistsError):
        helper().download(client, "uuid", output)
    assert get.call_count == 1


def test_download_rejects_active_job(tmp_path, monkeypatch):
    get = Mock()
    monkeypatch.setitem(sys.modules, "requests", SimpleNamespace(get=get))
    client = Mock()
    client.jobs.getJob.return_value = SimpleNamespace(status="RUNNING")
    with pytest.raises(ValueError):
        helper().download(client, "uuid", tmp_path / "output.zip")
    get.assert_not_called()
