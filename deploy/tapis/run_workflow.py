"""App-owned coordinator: replay in a subprocess, preserve diagnostics, archive outputs."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import subprocess
import sys
import traceback
from zipfile import ZIP_DEFLATED, ZipFile


def collect(workspace: Path, destination: Path) -> None:
    """Package declared artifacts plus the manifest and per-task diagnostics."""
    root = workspace.resolve()
    candidates = set()
    manifest = root / "manifest.json"
    if manifest.is_file():
        candidates.add("manifest.json")
        for name in json.loads(manifest.read_text(encoding="utf-8")).get("artifacts", []):
            if not isinstance(name, str):
                raise ValueError("artifact paths must be strings")
            name = name.replace("\\", "/")
            if (PurePosixPath(name).is_absolute() or PureWindowsPath(name).drive
                    or ".." in PurePosixPath(name).parts):
                raise ValueError(f"artifact escapes workspace: {name}")
            candidates.add(name)
    for pattern in ("**/stdout.log", "**/.femora-driver.tcl"):
        candidates.update(path.relative_to(root).as_posix() for path in root.glob(pattern))
    files = []
    for name in sorted(candidates):
        path = root / name
        if not path.resolve().is_relative_to(root) or not path.is_file():
            raise ValueError(f"artifact is missing or outside workspace: {name}")
        files.append((name, path))
    with ZipFile(destination, "x", compression=ZIP_DEFLATED, allowZip64=True) as archive:
        for name, path in files:
            archive.write(path, name)


def run(bundle: Path, workspace: Path, output: Path) -> int:
    bundle, workspace, output = bundle.resolve(), workspace.resolve(), output.resolve()
    if output == workspace or output.is_relative_to(workspace) or workspace.is_relative_to(output):
        raise ValueError("output and workspace must be separate, non-nested directories")
    output.mkdir(parents=True, exist_ok=True)
    # Tapis may already have created its stdout file here. Never replace our outputs.
    for name in ("results.zip", "run-status.json", "workflow.log"):
        if (output / name).exists():
            raise FileExistsError(f"output already exists: {output / name}")
    if workspace.exists() and any(workspace.iterdir()):
        raise FileExistsError("workflow workspace must be fresh")
    status = {"started": datetime.now(timezone.utc).isoformat(), "status": "failed"}
    code = 1
    try:
        digest = hashlib.sha256()
        with bundle.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        status["bundle_sha256"] = digest.hexdigest()
        status["python"] = sys.version
        status["opensees"] = os.environ.get("FEMORA_OPENSEES")
        status["slurm_job_id"] = os.environ.get("SLURM_JOB_ID", os.environ.get("SLURM_JOBID"))
        status["rank_slots"] = os.environ.get("SLURM_NTASKS")
        with (output / "workflow.log").open("x", encoding="utf-8") as log:
            completed = subprocess.run(
                [sys.executable, "-m", "femora.jobs", "replay", str(bundle),
                 "--workspace", str(workspace), "--backend", "tacc"],
                stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, check=False,
            )
        status["workflow_exit_code"] = completed.returncode
        code = 0 if completed.returncode == 0 else 1
        if workspace.exists():
            collect(workspace, output / "results.zip")
        status["status"] = "finished" if code == 0 else "failed"
    except Exception as exc:
        code = 1
        status["error"] = str(exc)
        traceback.print_exc()
    finally:
        status["finished"] = datetime.now(timezone.utc).isoformat()
        (output / "run-status.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    print(f"Femora workflow {status['status']}; outputs: {output}", flush=True)
    return code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.bundle, args.workspace, args.output))
