"""Read-only TACC preflight via an injected, authenticated Tapis client."""

from dataclasses import dataclass
from copy import deepcopy
import re

from ..backends import TACC
from ..workflow import Workflow
from .base import ValidationIssue, ValidationReport


def _get(obj, field, default=None):
    return obj.get(field, default) if isinstance(obj, dict) else getattr(obj, field, default)


@dataclass(frozen=True)
class TACCSettings:
    system: str
    queue: str
    allocation: str
    nodes: int
    cores_per_node: int
    minutes: int


@dataclass(frozen=True)
class QueueLimits:
    name: str
    hpc_queue: str | None
    min_nodes: int | None
    max_nodes: int | None
    min_cores_per_node: int | None
    max_cores_per_node: int | None
    min_minutes: int | None
    max_minutes: int | None


def _queues(system):
    return tuple(QueueLimits(
        _get(q, "name"), _get(q, "hpcQueueName"),
        *(_get(q, key) for key in (
            "minNodeCount", "maxNodeCount", "minCoresPerNode", "maxCoresPerNode",
            "minMinutes", "maxMinutes")),
    ) for q in (_get(system, "batchLogicalQueues", []) or []))


class TACCValidator:
    """First provider component: discovery and preflight only, never submission.

    The caller owns authentication and selects the Tapis tenant. No tapipy import
    or DesignSafe endpoint is needed here. Limits come from the selected system,
    not a hardcoded hardware table. Missing limits are explicitly unverified.
    """

    def __init__(self, client):
        self._client = client

    def queues(self, system: str) -> tuple[QueueLimits, ...]:
        return _queues(self._client.systems.getSystem(systemId=system))

    def validate(self, workflow: Workflow, settings: TACCSettings) -> ValidationReport:
        return self._validate(settings, workflow)

    def validate_resources(self, settings: TACCSettings) -> ValidationReport:
        """Validate a staged job without importing/executing its Python bundle."""
        return self._validate(settings, None)

    def _validate(self, settings: TACCSettings, workflow: Workflow | None) -> ValidationReport:
        issues = []

        def issue(severity, field, message):
            issues.append(ValidationIssue(severity, field, message))

        for field in ("system", "queue", "allocation"):
            value = getattr(settings, field)
            if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.~-]+", value):
                issue("error", field, "Expected a nonempty identifier without shell syntax.")
        for field in ("nodes", "cores_per_node", "minutes"):
            value = getattr(settings, field)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                issue("error", field, "Must be a positive integer.")
        if issues:
            return ValidationReport(tuple(issues))
        if workflow is None:
            issue("unverified", "workflow", "Staged bundle task capacity is checked by the remote runner, not this resource preflight.")
        elif not workflow.stages:
            issue("error", "workflow", "Workflow has no stages.")
        for stage in (() if workflow is None else workflow.stages):
            required = (sum if stage.parallel else max)(task.cores for task in stage.tasks)
            capacity = settings.nodes * settings.cores_per_node
            if required > capacity:
                issue("error", f"stages.{stage.name}",
                      f"Needs {required} rank slots; requested allocation has {capacity}.")
            try:
                TACC().validate(stage)
            except ValueError as error:
                issue("error", f"stages.{stage.name}", str(error))
        try:
            system = self._client.systems.getSystem(systemId=settings.system)
        except Exception:
            # SDK exceptions may include credentials or request headers.
            issue("error", "system", "Cannot retrieve system configuration; check authentication and access.")
            return ValidationReport(tuple(issues))
        for field in ("enabled", "canExec"):
            if _get(system, field) is not True:
                issue("error", "system", f"System must have {field}=true.")
        queue = next((q for q in _queues(system) if q.name == settings.queue), None)
        if queue is None:
            issue("error", "queue", f"Logical queue '{settings.queue}' is not exposed by this system.")
        else:
            for field, lower, upper in (
                ("nodes", queue.min_nodes, queue.max_nodes),
                ("cores_per_node", queue.min_cores_per_node, queue.max_cores_per_node),
                ("minutes", queue.min_minutes, queue.max_minutes),
            ):
                value = getattr(settings, field)
                for kind, bound in (("minimum", lower), ("maximum", upper)):
                    if isinstance(bound, bool) or not isinstance(bound, int) or bound < 0:
                        issue("unverified", field, f"Queue {kind} not bounded by usable system metadata.")
                    elif (kind == "minimum" and value < bound) or (kind == "maximum" and value > bound):
                        issue("error", field, f"Queue '{queue.name}' {kind} is {bound}; requested {value}.")
        for field, message in (
            ("allocation", "Project eligibility and balance must still be checked by the scheduler."),
            ("environment", "Installed modules, MPI compatibility, and runtime memory use are not checked here."),
            ("storage", "Input readability and output write permissions are not checked here."),
        ):
            issue("unverified", field, message)
        return ValidationReport(tuple(issues))


class SubmissionValidationError(ValueError):
    """Safe-to-display preflight failure, containing no SDK request details."""

    def __init__(self, report):
        self.report = report
        super().__init__("\n".join(f"{i.field}: {i.message}" for i in report.errors))


class TACCSubmitter:
    """Validated submission of an already staged Tapis job request.

    This is the transport adapter for the future full Platform implementation.
    It does not upload bundles, execute user Python locally, or register apps.
    Authentication stays with the injected client. No automatic write retries.
    """

    def __init__(self, client):
        self._client = client
        self.validator = TACCValidator(client)

    def preflight(self, request):
        data = deepcopy(request)
        issues = []

        def error(field, message):
            issues.append(ValidationIssue("error", field, message))

        for field in ("appId", "appVersion"):
            if not isinstance(data.get(field), str) or not data[field].strip():
                error(field, "A registered app ID and version are required.")
        if issues:
            return data, ValidationReport(tuple(issues))
        try:
            app = self._client.apps.getApp(appId=data["appId"], appVersion=data["appVersion"])
        except Exception:
            error("app", "Cannot retrieve the registered app; check version and access.")
            return data, ValidationReport(tuple(issues))
        defaults = _get(app, "jobAttributes", {}) or {}
        # Do not silently relocate an app to a different machine installation.
        app_system = _get(defaults, "execSystemId")
        system = data.get("execSystemId", app_system)
        if app_system and system != app_system:
            error("system", "Selected system differs from the app installation; use a matching app.")
        if data.get("isMpi", _get(defaults, "isMpi")) is not False:
            error("isMpi", "The Femora coordinator requires isMpi=false; tasks launch their own MPI processes.")
        queue = data.get("execSystemLogicalQueue", _get(defaults, "execSystemLogicalQueue"))
        params = data.get("parameterSet", {}) or {}
        if not isinstance(params, dict):
            error("parameterSet", "Expected an object.")
            return data, ValidationReport(tuple(issues))
        options = params.get("schedulerOptions", [])
        if not isinstance(options, list):
            error("schedulerOptions", "Expected a list of allocation options.")
            return data, ValidationReport(tuple(issues))
        allocation = None
        # Narrow pilot contract avoids raw scheduler options overriding validated resources.
        for option in options:
            arg = option.get("arg", "") if isinstance(option, dict) else ""
            match = re.fullmatch(r"-A ([A-Za-z0-9_.~-]+)", arg) if isinstance(arg, str) else None
            if not match or allocation is not None:
                error("schedulerOptions", "Supply exactly one '-A PROJECT' option; use job fields for resources.")
            else:
                allocation = match.group(1)
        for option in _get(_get(defaults, "parameterSet", {}) or {}, "schedulerOptions", []) or []:
            if _get(option, "arg"):
                error("app", "App-level scheduler options are not supported by this pilot preflight.")
        settings = TACCSettings(system, queue, allocation,
                                data.get("nodeCount"), data.get("coresPerNode"), data.get("maxMinutes"))
        report = self.validator.validate_resources(settings)
        issues.extend(report.issues)
        # Explicit job-level values override the app's default queue without updating the app.
        data["execSystemId"] = system
        data["execSystemLogicalQueue"] = queue
        return data, ValidationReport(tuple(issues))

    def submit_request(self, request, *, on_validation=None):
        """Re-read live limits on each submission; callbacks only observe the report."""
        data, report = self.preflight(request)
        if on_validation is not None:
            on_validation(report)
        if not report.valid:
            raise SubmissionValidationError(report)
        return self._client.jobs.submitJob(**data)
