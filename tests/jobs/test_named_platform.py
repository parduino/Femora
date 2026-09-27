"""Named submission dispatch, without authentication or remote side effects."""

from unittest.mock import Mock
from zipfile import ZipFile

import pytest
import femora as fm
from femora.jobs.platforms import TACCPlatform, TACCSettings


@pytest.fixture
def settings():
    return dict(app_id="test-app", system="stampede3", queue="skx-dev",
                allocation="PROJECT", nodes=1, cores_per_node=48, minutes=20)


@pytest.fixture
def source(tmp_path):
    path = tmp_path / "workflow.py"
    path.write_text("raise RuntimeError('must not run locally')\n")
    return path


def test_named_submit_packages_and_resolves(monkeypatch, source, settings):
    target = Mock()
    login = Mock(return_value=target)
    monkeypatch.setattr(TACCPlatform, "login", login)
    original = dict(settings)

    def submit(archive, resources):
        with ZipFile(archive) as zipped:
            assert zipped.read("workflow.py") == source.read_bytes()
        assert resources == TACCSettings("stampede3", "skx-dev", "PROJECT", 1, 48, 20)
        return "job"

    target.submit.side_effect = submit
    assert fm.submit(source=source, platform="tacc", settings=settings) == "job"
    login.assert_called_once_with(app_id="test-app")
    assert settings == original


def test_named_existing_bundle_and_connection_options(monkeypatch, source, settings, tmp_path):
    archive = fm.jobs.bundle(source=source, destination=tmp_path / "workflow.zip", inputs={})
    login = Mock()
    monkeypatch.setattr(TACCPlatform, "login", login)
    settings.update(app_version="0.2.0", base_url="https://designsafe.tapis.io",
                    storage_system="storage", input_directory="user/jobs")
    fm.submit(bundle=archive, platform="tacc", settings=settings)
    login.assert_called_once_with(app_id="test-app", app_version="0.2.0",
                                  base_url="https://designsafe.tapis.io",
                                  storage_system="storage", input_directory="user/jobs")
    login.return_value.submit.assert_called_once()


@pytest.mark.parametrize("changes", [
    {"app_id": ""}, {"nodes": 0}, {"cores_per_node": True},
    {"minutes": "20"}, {"queue": None}, {"typo": 1}, {"password": "not-allowed"},
])
def test_invalid_settings_do_not_login(monkeypatch, source, settings, changes):
    login = Mock()
    monkeypatch.setattr(TACCPlatform, "login", login)
    settings.update(changes)
    with pytest.raises(ValueError):
        fm.submit(source=source, platform="tacc", settings=settings)
    login.assert_not_called()


def test_missing_unknown_and_bad_files_do_not_login(monkeypatch, source, settings):
    login = Mock()
    monkeypatch.setattr(TACCPlatform, "login", login)
    for platform, options in [("aws", settings), ("tacc", {}), ("tacc", None)]:
        with pytest.raises((TypeError, ValueError)):
            fm.submit(source=source, platform=platform, settings=options)
    with pytest.raises(ValueError, match="data file was not found"):
        fm.submit(source=source, platform="tacc", settings=settings, files=["missing.txt"])
    login.assert_not_called()
