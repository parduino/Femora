"""Provider-neutral contracts; no scheduler or authentication assumptions."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Literal, Protocol, TypeVar

from ..workflow import Workflow

Settings = TypeVar("Settings", contravariant=True)


@dataclass(frozen=True)
class ValidationIssue:
    severity: Literal["error", "warning", "unverified"]
    field: str
    message: str


@dataclass(frozen=True)
class ValidationReport:
    issues: tuple[ValidationIssue, ...] = ()

    @property
    def errors(self):
        return tuple(issue for issue in self.issues if issue.severity == "error")

    @property
    def valid(self) -> bool:
        """No known errors; unverified checks can still remain."""
        return not self.errors

    def raise_for_errors(self) -> None:
        if self.errors:
            raise ValueError("\n".join(f"{i.field}: {i.message}" for i in self.errors))


@dataclass(frozen=True)
class JobStatus:
    state: Literal["pending", "running", "succeeded", "failed", "cancelled", "unknown"]
    native_state: str
    message: str = ""


class JobHandle(Protocol):
    @property
    def id(self) -> str: ...
    def status(self) -> JobStatus: ...
    def cancel(self) -> None: ...
    def download(self, destination: Path) -> Path: ...


@dataclass(frozen=True)
class JobSummary:
    """Safe provider-neutral discovery data, not a raw SDK response."""

    id: str
    name: str
    submitted_at: str
    status: JobStatus
    connection: dict = field(default_factory=dict)
    resources: dict = field(default_factory=dict)


class JobDiscovery(Protocol):
    """Optional adapter capability; discovery is read-only."""

    def list_jobs(self) -> Iterable[JobSummary]: ...
    def tracking_metadata(self) -> dict: ...


class PlatformValidator(Protocol[Settings]):
    def validate(self, workflow: Workflow, settings: Settings) -> ValidationReport: ...


class Platform(PlatformValidator[Settings], Protocol[Settings]):
    """Future submission implementations must validate before remote writes.

    Bundle is a trusted workflow archive. Credentials belong to the provider
    instance, never settings or the bundle. This is not an execution backend.
    """

    def submit(self, bundle: Path, settings: Settings) -> JobHandle: ...
