"""Build a Tapis v3 ZIP app and JSON requests; never contacts Tapis."""

import argparse
import json
from pathlib import Path
import shlex
import stat
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED


def build(args):
    for field in ("app_id", "version", "exec_system", "archive_system", "queue", "allocation"):
        value = getattr(args, field)
        if not value or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-~" for c in value):
            raise ValueError(f"invalid {field}: {value!r}")
    for value in (args.nodes, args.cores_per_node, args.minutes):
        if value < 1:
            raise ValueError("nodes, cores-per-node, and minutes must be positive")
    if not (args.image.startswith("/") or args.image.startswith(("tapis://", "https://"))):
        raise ValueError("image must be a remote absolute archive path or tapis/https URL")
    if not args.bundle_url.startswith(("tapis://", "https://")):
        raise ValueError("bundle-url must be a tapis/https URL")
    if not args.archive_dir:
        raise ValueError("archive-dir must be supplied for this user's project")
    target = args.output.resolve()
    target.mkdir(parents=True, exist_ok=True)
    if any(target.iterdir()):
        raise FileExistsError("build output directory must be empty")
    site = {
        "FEMORA_MODULE_PATH": args.module_path,
        "FEMORA_PYTHON_MODULE": args.python_module,
        "FEMORA_MODULE": args.femora_module,
        "FEMORA_OPENSEES_MODULE": args.opensees_module,
    }
    shell = "\n".join(f"{key}={shlex.quote(value)}" for key, value in site.items()) + "\n"
    sources = {"site.sh": shell}
    for name in ("tapisjob_app.sh", "run_workflow.py"):
        sources[name] = Path(__file__).with_name(name).read_text(encoding="utf-8")
    with ZipFile(target / "app.zip", "x", compression=ZIP_DEFLATED) as archive:
        for name, text in sources.items():
            info = ZipInfo(name)
            info.create_system = 3
            mode = 0o755 if name == "tapisjob_app.sh" else 0o644
            info.external_attr = (stat.S_IFREG | mode) << 16
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, text.replace("\r\n", "\n").encode("utf-8"))
    app = {
        "id": args.app_id, "version": args.version,
        "description": "Run trusted Femora workflow bundles inside a TACC allocation.",
        "runtime": "ZIP", "containerImage": args.image, "jobType": "BATCH",
        "strictFileInputs": True,
        "jobAttributes": {
            "execSystemId": args.exec_system, "execSystemLogicalQueue": args.queue,
            "isMpi": False, "archiveMode": "ALWAYS",
            "execSystemExecDir": "${JobWorkingDir}",
            "execSystemInputDir": "${JobWorkingDir}/inputs",
            "execSystemOutputDir": "${JobWorkingDir}/output",
            "fileInputs": [{"name": "workflow", "inputMode": "REQUIRED", "targetPath": "workflow.zip"}],
            "parameterSet": {
                "archiveFilter": {"includes": [], "excludes": [], "includeLaunchFiles": False},
                "logConfig": {"stdoutFilename": "app.log", "stderrFilename": "app.err"},
            },
        },
    }
    job = {
        "name": "femora-mpi-smoke", "appId": args.app_id, "appVersion": args.version,
        "nodeCount": args.nodes, "coresPerNode": args.cores_per_node, "maxMinutes": args.minutes,
        "archiveSystemId": args.archive_system,
        "archiveSystemDir": args.archive_dir.rstrip("/") + "/${JobUUID}",
        "fileInputs": [{"name": "workflow", "sourceUrl": args.bundle_url, "targetPath": "workflow.zip"}],
        "parameterSet": {"schedulerOptions": [
            {"name": "allocation", "arg": f"-A {args.allocation}"},
        ]},
    }
    for name, data in (("app.json", app), ("job.json", job)):
        (target / name).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return target


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--app-id", default="femora-workflow-stampede3")
    result.add_argument("--version", default="0.1.0")
    result.add_argument("--exec-system", default="stampede3")
    result.add_argument("--archive-system", default="designsafe.storage.default")
    result.add_argument("--archive-dir", default="${EffectiveUserId}/tapis-jobs-archive/${JobCreateDate}")
    result.add_argument("--queue", default="skx")
    for name in ("image", "bundle-url", "allocation"):
        result.add_argument(f"--{name}", required=True)
    result.add_argument("--nodes", type=int, default=1)
    result.add_argument("--cores-per-node", type=int, default=48)
    result.add_argument("--minutes", type=int, default=20)
    result.add_argument("--module-path", default="/work2/08189/amnp95/modules")
    result.add_argument("--python-module", default="python/3.12.11")
    result.add_argument("--femora-module", default="femora")
    result.add_argument("--opensees-module", default="opensees/3.8.0")
    return result


if __name__ == "__main__":
    print(build(parser().parse_args()))
