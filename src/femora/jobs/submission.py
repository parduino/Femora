"""Provider-neutral entry point for remote workflow submission."""

from pathlib import Path
import inspect
from tempfile import TemporaryDirectory
from typing import Any, Mapping, Sequence, TypeVar

from .bundle import bundle as create_bundle
from .platforms.base import JobHandle, Platform

S = TypeVar("S")


def submit(*, platform: Platform[S], settings: S, source: str | Path | None = None,
           bundle: str | Path | None = None, inputs: Mapping[str, Any] | None = None,
           files: Sequence[str | Path] = (), entrypoint: str = "build_workflow",
           function=None) -> JobHandle:
    """Package an existing workflow file, or submit a trusted existing bundle.

    The source is not executed locally. Put calls to submit under a __main__
    guard so importing the bundled factory remotely does not submit recursively.
    All model construction, simulation, and postprocessing remain remote tasks.
    Platform owns validation, staging, and submission; no provider name dispatch
    or credentials are embedded in the workflow.
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
        return platform.submit(Path(bundle), settings)
    with TemporaryDirectory(prefix="femora-submit-") as directory:
        archive = create_bundle(source=source, destination=Path(directory) / "workflow.zip",
                                inputs={} if inputs is None else inputs,
                                files=files, entrypoint=entrypoint)
        return platform.submit(archive, settings)
