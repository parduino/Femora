"""Offline checks for the deployable Tapis app; no credentials or remote jobs."""

import importlib.util
import json
from pathlib import Path
import stat
from types import SimpleNamespace
from zipfile import ZipFile

import pytest


def load(name):
    path = Path(__file__).parents[2] / "deploy/tapis" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def arguments(builder, tmp_path):
    return builder.parser().parse_args([
        "--output", str(tmp_path / "app"), "--exec-system", "test.stampede3",
        "--archive-system", "test.storage", "--archive-dir", "project/femora",
        "--queue", "skx", "--allocation", "TEST-123",
        "--image", "/shared/femora/0.1.0/app.zip",
        "--bundle-url", "tapis://test.storage/inputs/mpi.zip",
    ])


def test_package_contract(tmp_path):
    builder = load("build_app")
    target = builder.build(arguments(builder, tmp_path))
    app = json.loads((target / "app.json").read_text())
    job = json.loads((target / "job.json").read_text())
    assert app["runtime"] == "ZIP" and app["jobType"] == "BATCH"
    assert app["jobAttributes"]["isMpi"] is False
    assert app["jobAttributes"]["archiveMode"] == "ALWAYS"
    assert "archiveSystemId" not in app["jobAttributes"]
    assert job["archiveSystemDir"] == "project/femora/${JobUUID}"
    assert job["parameterSet"]["schedulerOptions"] == [
        {"name": "allocation", "arg": "-A TEST-123"}
    ]
    assert job["nodeCount"] == 1 and job["coresPerNode"] == 48
    with ZipFile(target / "app.zip") as archive:
        assert set(archive.namelist()) == {"site.sh", "tapisjob_app.sh", "run_workflow.py"}
        assert archive.getinfo("tapisjob_app.sh").external_attr >> 16 & stat.S_IXUSR
        assert b"\r" not in archive.read("tapisjob_app.sh")
        assert b"OpenSeesMP" in archive.read("tapisjob_app.sh")
    with pytest.raises(FileExistsError):
        builder.build(arguments(builder, tmp_path))


def test_reject_invalid_scheduler_argument(tmp_path):
    builder = load("build_app")
    args = arguments(builder, tmp_path)
    args.allocation = "project; unsafe"
    with pytest.raises(ValueError, match="allocation"):
        builder.build(args)


def test_designsafe_defaults(tmp_path):
    builder = load("build_app")
    args = builder.parser().parse_args([
        "--output", str(tmp_path / "app"), "--allocation", "TEST-123",
        "--image", "/shared/app.zip", "--bundle-url", "tapis://designsafe.storage.default/user/mpi.zip",
    ])
    target = builder.build(args)
    app = json.loads((target / "app.json").read_text())
    job = json.loads((target / "job.json").read_text())
    assert app["jobAttributes"]["execSystemId"] == "stampede3"
    assert app["jobAttributes"]["execSystemExecDir"] == "${JobWorkingDir}"
    assert job["archiveSystemId"] == "designsafe.storage.default"
    assert job["archiveSystemDir"] == "${EffectiveUserId}/tapis-jobs-archive/${JobCreateDate}/${JobUUID}"


@pytest.mark.parametrize("exit_code", [0, 7])
def test_replay_and_archive(tmp_path, monkeypatch, exit_code):
    app = load("run_workflow")
    workspace, output = tmp_path / "work", tmp_path / "output"
    bundle = tmp_path / "workflow.zip"
    bundle.write_bytes(b"test bundle")

    def replay(argv, **kwargs):
        assert argv[-2:] == ["--backend", "tacc"]
        workspace.mkdir()
        (workspace / "selected.txt").write_text("selected")
        (workspace / "unselected.txt").write_text("do not archive")
        logs = workspace / "solve" / "model"
        logs.mkdir(parents=True)
        (logs / "stdout.log").write_text("partial diagnostic")
        (workspace / "manifest.json").write_text(json.dumps({"artifacts": ["selected.txt"]}))
        kwargs["stdout"].write("runner diagnostic\n")
        return SimpleNamespace(returncode=exit_code)

    monkeypatch.setattr(app.subprocess, "run", replay)
    assert app.run(bundle, workspace, output) == (0 if exit_code == 0 else 1)
    with ZipFile(output / "results.zip") as archive:
        assert set(archive.namelist()) == {"manifest.json", "selected.txt", "solve/model/stdout.log"}
    status = json.loads((output / "run-status.json").read_text())
    assert status["workflow_exit_code"] == exit_code
    assert status["status"] == ("finished" if exit_code == 0 else "failed")
    assert "runner diagnostic" in (output / "workflow.log").read_text()


@pytest.mark.parametrize("name", ["../secret", "/secret", "C:/secret", "..\\secret"])
def test_reject_escaping_artifacts(tmp_path, name):
    app = load("run_workflow")
    work = tmp_path / "work"
    work.mkdir()
    (work / "manifest.json").write_text(json.dumps({"artifacts": [name]}))
    with pytest.raises(ValueError):
        app.collect(work, tmp_path / "results.zip")


def test_missing_bundle_reports_failure(tmp_path):
    app = load("run_workflow")
    output = tmp_path / "output"
    assert app.run(tmp_path / "missing.zip", tmp_path / "work", output) == 1
    assert json.loads((output / "run-status.json").read_text())["status"] == "failed"


def test_existing_workspace_is_not_overwritten(tmp_path):
    app = load("run_workflow")
    work = tmp_path / "work"
    work.mkdir()
    (work / "keep.txt").write_text("keep")
    with pytest.raises(FileExistsError):
        app.run(tmp_path / "workflow.zip", work, tmp_path / "output")
    assert (work / "keep.txt").read_text() == "keep"


def test_packaging_failure_is_not_success(tmp_path, monkeypatch):
    app = load("run_workflow")
    bundle = tmp_path / "workflow.zip"
    bundle.write_bytes(b"bundle")
    workspace = tmp_path / "work"

    def replay(argv, **kwargs):
        workspace.mkdir()
        (workspace / "manifest.json").write_text(json.dumps({"artifacts": ["missing.txt"]}))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(app.subprocess, "run", replay)
    output = tmp_path / "output"
    assert app.run(bundle, workspace, output) == 1
    assert json.loads((output / "run-status.json").read_text())["status"] == "failed"
