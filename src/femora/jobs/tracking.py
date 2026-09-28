"""Local job records and reconnectable handles; credentials stay in memory."""

from dataclasses import dataclass, asdict, replace
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import sqlite3
import time
import warnings
from contextlib import contextmanager
from urllib.parse import urlsplit


def _now():
    return datetime.now(timezone.utc).isoformat()


def _resources(values):
    return {key: value for key, value in (values or {}).items()
            if key in {"system", "queue", "allocation", "nodes", "cores_per_node", "minutes"}}


@dataclass(frozen=True)
class JobRecord:
    key: str
    id: str
    platform: str
    name: str
    submitted_at: str
    connection: dict
    resources: dict
    state: str = "unknown"
    native_state: str = "UNKNOWN"
    checked_at: str | None = None


class JobRegistry:
    """SQLite avoids losing records when separate submitting processes overlap."""

    def __init__(self, path=None):
        from platformdirs import user_data_path
        self.path = Path(path or os.environ.get("FEMORA_JOBS_DB") or
                         user_data_path("femora", appauthor=False) / "jobs.sqlite3")

    @contextmanager
    def _open(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.path, timeout=10)
        db.execute("CREATE TABLE IF NOT EXISTS jobs (key TEXT PRIMARY KEY, record TEXT NOT NULL)")
        try:
            with db:
                yield db
        finally:
            db.close()

    def save(self, record):
        with self._open() as db:
            db.execute("INSERT OR REPLACE INTO jobs VALUES (?, ?)",
                       (record.key, json.dumps(asdict(record))))
        return record

    def list(self):
        with self._open() as db:
            return sorted((JobRecord(**json.loads(row[0])) for row in
                           db.execute("SELECT record FROM jobs")),
                          key=lambda record: record.submitted_at, reverse=True)

    def get(self, job_id):
        matches = [record for record in self.list() if job_id in (record.id, record.key)]
        if len(matches) != 1:
            raise ValueError("Job not found or ambiguous; use its full registry key")
        return matches[0]


def add(job_id, *, platform="tacc", name=None, connection=None, resources=None, registry=None):
    """Register an existing job without submitting or contacting the provider."""
    if platform not in _CONNECTORS:
        raise ValueError(f"Unsupported tracking platform: {platform}")
    connection = dict(connection or {})
    allowed = {"base_url", "username", "app_id", "app_version"}
    if set(connection) - allowed:
        raise ValueError("Connection records allow only tenant, username, app ID and version; no credentials")
    if any(not isinstance(value, str) or not value.strip() for value in connection.values()):
        raise ValueError("Connection fields must be nonempty strings")
    if platform == "tacc":
        connection.setdefault("base_url", "https://designsafe.tapis.io")
        url = urlsplit(connection["base_url"])
        if url.scheme != "https" or not url.netloc or url.username or url.password or url.query or url.fragment:
            raise ValueError("Tenant must be an HTTPS URL without credentials, query, or fragment")
    if not isinstance(job_id, str) or not job_id.strip():
        raise ValueError("A nonempty job ID is required")
    # Only persist resource fields, never arbitrary settings or workflow inputs.
    resources = _resources(resources)
    key = hashlib.sha256(json.dumps([platform, connection.get("base_url"),
                                   connection.get("username"), job_id]).encode()).hexdigest()
    store = registry or JobRegistry()
    existing = next((r for r in store.list() if r.key == key), None)
    return existing or store.save(JobRecord(key, job_id, platform, name or job_id,
                                           _now(), connection, resources))


def sync(platform, *, registry=None):
    """Discover remote jobs through an authenticated adapter and cache them.

    Remote discovery never deletes cached jobs that a provider no longer lists.
    Only normalized summaries and safe connection fields are persisted.
    """
    store = registry or JobRegistry()
    metadata = platform.tracking_metadata()
    records = []
    for summary in platform.list_jobs():
        record = add(summary.id, platform=metadata["platform"], name=summary.name,
                     connection={**metadata["connection"], **summary.connection},
                     resources=summary.resources, registry=store)
        record = replace(record, name=summary.name,
                         submitted_at=summary.submitted_at or record.submitted_at,
                         connection={**record.connection, **summary.connection},
                         resources={**record.resources, **_resources(summary.resources)},
                         state=summary.status.state, native_state=summary.status.native_state,
                         checked_at=_now())
        records.append(store.save(record))
    return records


def list_jobs(*, platform=None, registry=None):
    """List cached jobs, or discover remote jobs when given an authenticated adapter."""
    if platform is not None:
        return sync(platform, registry=registry)
    return (registry or JobRegistry()).list()


def _tacc_connect(record):
    from .platforms.tacc_remote import TACCPlatform
    target = TACCPlatform.login(app_id=record.connection.get("app_id", "job-tracking"),
                                app_version=record.connection.get("app_version", "0.1.0"),
                                base_url=record.connection.get("base_url", "https://designsafe.tapis.io"))
    expected = record.connection.get("username")
    if expected and target._client.username != expected:
        raise ValueError("Authenticated account does not match the job record")
    return target


_CONNECTORS = {"tacc": _tacc_connect}


class TrackedJob:
    def __init__(self, record, handle, registry):
        self.record, self._handle, self._registry = record, handle, registry
        self.id = record.id

    def status(self):
        from dataclasses import replace
        status = self._handle.status()
        self.record = replace(self.record, state=status.state, native_state=status.native_state,
                              checked_at=_now())
        self._registry.save(self.record)
        return status

    def details(self):
        self.status()
        method = getattr(self._handle, "details", None)
        return method() if callable(method) else {}

    def cancel(self):
        # Request only; cancellation is not confirmed until a subsequent status.
        self._handle.cancel()

    def download(self, destination):
        return self._handle.download(Path(destination))

    def wait(self, poll_interval=30, timeout=None):
        if poll_interval < 1 or (timeout is not None and timeout < 0):
            raise ValueError("Polling interval must be >=1 and timeout nonnegative")
        started = time.monotonic()
        while True:
            status = self.status()
            if status.state in {"succeeded", "failed", "cancelled"}:
                return status
            if timeout is not None and time.monotonic() - started >= timeout:
                raise TimeoutError("Job is still active; no remote action was taken")
            time.sleep(poll_interval)


def connect(job_id, *, platform=None, registry=None):
    """Reconnect to a recorded job; optionally reuse an authenticated adapter."""
    store = registry or JobRegistry()
    record = store.get(job_id)
    target = platform if platform is not None else _CONNECTORS[record.platform](record)
    return TrackedJob(record, target.job(record.id), store)


def record_submission(target, handle, settings, name):
    """Tracking failure must never turn a successful submit into a retry."""
    from collections.abc import Mapping
    method = getattr(target, "tracking_metadata", None)
    if not callable(method):
        return
    try:
        metadata = method()
        if not isinstance(metadata, Mapping):
            return
        resources = asdict(settings) if hasattr(settings, "__dataclass_fields__") else settings
        add(handle.id, platform=metadata["platform"], name=name,
            connection=metadata["connection"], resources=resources)
    except Exception:
        warnings.warn(f"Job {handle.id} was submitted but could not be recorded locally. "
                      "Keep its ID; do not resubmit.", UserWarning, stacklevel=2)
