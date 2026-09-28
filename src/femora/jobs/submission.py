"""Provider-neutral entry point for remote workflow submission."""

from pathlib import Path
import inspect
from tempfile import TemporaryDirectory
from typing import Any, Mapping, Sequence, TypeVar

from .bundle import bundle as create_bundle
from .platforms.base import JobHandle, Platform
from .platforms.resolve import resolve_platform
from .tracking import record_submission

S = TypeVar("S")


def submit(*, platform: Platform[S] | str, settings: S | Mapping[str, Any], source: str | Path | None = None,
           bundle: str | Path | None = None, inputs: Mapping[str, Any] | None = None,
           files: Sequence[str | Path] | Mapping[str, str | Path] = (), entrypoint: str = "build_workflow",
           function=None) -> JobHandle:
    """Package an existing workflow file, or submit a trusted existing bundle.

    The source is not executed locally. Put calls to submit under a __main__
    guard so importing the bundled factory remotely does not submit recursively.
    All model construction, simulation, and postprocessing remain remote tasks.
    Use platform="tacc" with a settings dictionary for interactive login, or
    supply an authenticated Platform and its settings object. Provider adapters
    own validation, staging, and submission. Never store passwords in settings.
    """
    if sum(value is not None for value in (source, bundle, function)) != 1:
        raise ValueError("Supply exactly one of source, bundle, or function")
    if function is not None:
        if not inspect.isfunction(function) or function.__qualname__ != function.__name__ or not function.__name__.isidentifier():
            raise ValueError("function must be a top-level workflow factory, not a closure or lambda")
        if entrypoint != "build_workflow":
            raise ValueError("function determines its own entrypoint")
        source = inspect.getsourcefile(function)
        if source is None or not Path(source).is_file():
            raise ValueError("function must be defined in a Python source file; notebook cells are not supported yet")
        entrypoint = function.__name__
    if bundle is not None:
        if inputs is not None or files or entrypoint != "build_workflow":
            raise ValueError("inputs/files/entrypoint apply only when packaging source")
        if not Path(bundle).is_file():
            raise FileNotFoundError(bundle)
        platform, settings = resolve_platform(platform, settings)
        handle = platform.submit(Path(bundle), settings)
        record_submission(platform, handle, settings, Path(bundle).stem)
        return handle
    with TemporaryDirectory(prefix="femora-submit-") as directory:
        archive = create_bundle(source=source, destination=Path(directory) / "workflow.zip",
                                inputs={} if inputs is None else inputs,
                                files=files, entrypoint=entrypoint)
        platform, settings = resolve_platform(platform, settings)
        handle = platform.submit(archive, settings)
        record_submission(platform, handle, settings, Path(source).stem)
        return handle
