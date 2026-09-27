"""Tapis transport for remote TACC workflow bundles, with injected authentication."""

from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from urllib.parse import quote, urlsplit
from uuid import uuid4
import hashlib
import json
import warnings
from zipfile import ZipFile, is_zipfile

from .base import JobStatus
from .tacc import TACCSettings, TACCSubmitter, TACCValidator, SubmissionValidationError, _get


class RemoteSubmissionError(RuntimeError):
    """Submission may have reached Tapis. Inspect jobs before retrying."""

    def __init__(self, name, bundle_url):
        self.job_name = name
        self.bundle_url = bundle_url
        super().__init__(f"Submission outcome unknown for {name}. Check Tapis before retrying; "
                         f"staged input retained at {bundle_url}.")


def _path(value):
    path = PurePosixPath(value)
    if not value or path.is_absolute() or path == PurePosixPath(".") or ".." in path.parts or "\\" in value or ":" in value:
        raise ValueError("Input directory must be relative to the storage system root")
    return path


def _exists(client, system, path):
    try:
        client.files.listFiles(systemId=system, path=str(path), limit=1)
        return True
    except Exception as error:
        if getattr(getattr(error, "response", None), "status_code", None) == 404:
            return False
        raise


def _check_bundle(path):
    """Verify archive integrity without executing its trusted Python source."""
    with ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate bundle members")
        meta = json.loads(archive.read("bundle.json"))
        if meta.get("format_version") != 1 or not meta.get("entrypoint", "").isidentifier():
            raise ValueError("Unsupported workflow bundle")
        if not isinstance(json.loads(archive.read("inputs.json")), dict):
            raise ValueError("Bundle inputs must be an object")
        expected = {"workflow.py": meta["source_sha256"]}
        for name, digest in meta["files"].items():
            expected["data/" + _path(name).as_posix()] = digest
        if set(names) != {"bundle.json", "inputs.json", *expected}:
            raise ValueError("Unexpected bundle members")
        for name, digest in expected.items():
            actual = hashlib.sha256()
            with archive.open(name) as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    actual.update(chunk)
            if actual.hexdigest() != digest:
                raise ValueError(f"Bundle checksum mismatch: {name}")


@dataclass(frozen=True)
class TACCJob:
    id: str
    _client: object = field(repr=False, compare=False)

    def status(self) -> JobStatus:
        job = self._client.jobs.getJob(jobUuid=self.id)
        native = _get(job, "status", "UNKNOWN")
        states = {"FINISHED": "succeeded", "FAILED": "failed", "CANCELLED": "cancelled",
                  "RUNNING": "running", "ARCHIVING": "running"}
        pending = {"PENDING", "PROCESSING_INPUTS", "STAGING_INPUTS", "STAGING_JOB", "SUBMITTING_JOB", "QUEUED", "BLOCKED", "PAUSED"}
        state = states.get(native, "pending" if native in pending else "unknown")
        return JobStatus(state, native, _get(job, "lastMessage", "") or "")

    def cancel(self) -> None:
        self._client.jobs.cancelJob(jobUuid=self.id)

    def download(self, destination: Path) -> Path:
        import requests

        if self.status().state not in ("succeeded", "failed", "cancelled"):
            raise ValueError("Wait for the job to terminate before downloading")
        destination = Path(destination)
        partial = destination.with_name(destination.name + ".part")
        if destination.exists() or partial.exists():
            raise FileExistsError("Download destination or partial file already exists")
        base = self._client.base_url.rstrip("/")
        url = urlsplit(base)
        if url.scheme != "https" or not url.netloc or url.username or url.password or url.query or url.fragment:
            raise ValueError("Authenticated client must use an HTTPS tenant URL")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with requests.get(base + "/v3/jobs/" + quote(self.id, safe="") + "/output/download/",
                          headers={"X-Tapis-Token": self._client.access_token.access_token},
                          stream=True, timeout=(30, 120), allow_redirects=False) as response:
            response.raise_for_status()
            if response.status_code != 200:
                raise ValueError("Unexpected download response; redirects not followed")
            with partial.open("xb") as stream:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        stream.write(chunk)
        if not is_zipfile(partial):
            raise ValueError("Invalid output ZIP; partial file retained")
        import shutil
        with destination.open("xb") as stream, partial.open("rb") as source:
            shutil.copyfileobj(source, stream)
        partial.unlink()
        return destination


class TACCPlatform:
    """Complete Platform implementation using an existing registered Femora app.

    input_directory is storage-root-relative. Each submission gets a UUID child.
    Caller supplies an authenticated client; this class never prompts or saves
    credentials. Resources remain in TACCSettings, not in the workflow.
    """

    def __init__(self, client, *, app_id, app_version, storage_system, input_directory,
                 archive_directory="${EffectiveUserId}/tapis-jobs-archive/${JobCreateDate}",
                 on_validation=None):
        self._client = client
        self.app_id, self.app_version = app_id, app_version
        self.storage_system = storage_system
        self.input_directory = _path(input_directory)
        if not archive_directory:
            raise ValueError("archive_directory must not be empty")
        self.archive_directory = archive_directory
        self.on_validation = on_validation

    def validate(self, workflow, settings):
        return TACCValidator(self._client).validate(workflow, settings)

    def job(self, job_id):
        """Reconnect to an existing job without submitting again."""
        return TACCJob(job_id, self._client)

    def submit(self, bundle: Path, settings: TACCSettings) -> TACCJob:
        bundle = Path(bundle)
        _check_bundle(bundle)
        unique = uuid4().hex
        folder = self.input_directory / unique
        remote = folder / "workflow.zip"
        url = f"tapis://{self.storage_system}/{remote}"
        request = dict(
            name=f"femora-{unique}", appId=self.app_id, appVersion=self.app_version,
            execSystemId=settings.system, execSystemLogicalQueue=settings.queue,
            nodeCount=settings.nodes, coresPerNode=settings.cores_per_node, maxMinutes=settings.minutes,
            archiveSystemId=self.storage_system,
            archiveSystemDir=self.archive_directory.rstrip("/") + "/${JobUUID}",
            fileInputs=[dict(name="workflow", sourceUrl=url, targetPath="workflow.zip")],
            parameterSet={"schedulerOptions": [dict(name="allocation", arg=f"-A {settings.allocation}")]},
        )
        adapter = TACCSubmitter(self._client)
        _, report = adapter.preflight(request)
        if self.on_validation:
            self.on_validation(report)
        if not report.valid:
            raise SubmissionValidationError(report)
        if report.issues and self.on_validation is None:
            warnings.warn("; ".join(f"{i.severity}: {i.field}: {i.message}" for i in report.issues),
                          UserWarning, stacklevel=2)
        for parent in reversed(folder.parents):
            if parent != PurePosixPath(".") and not _exists(self._client, self.storage_system, parent):
                self._client.files.mkdir(systemId=self.storage_system, path=str(parent))
        if _exists(self._client, self.storage_system, folder):
            raise FileExistsError("Submission input directory already exists")
        self._client.files.mkdir(systemId=self.storage_system, path=str(folder))
        with bundle.open("rb") as stream:
            self._client.files.insert(systemId=self.storage_system, path=str(remote), file=stream)
        try:
            result = adapter.submit_request(request)
        except SubmissionValidationError:
            raise
        except Exception:
            raise RemoteSubmissionError(request["name"], url) from None
        identifier = _get(result, "uuid")
        if not isinstance(identifier, str) or not identifier:
            raise RemoteSubmissionError(request["name"], url)
        return self.job(identifier)
