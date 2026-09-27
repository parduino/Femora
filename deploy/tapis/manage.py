"""Explicit deployment operations for trusted Femora Tapis app definitions."""

import argparse
from contextlib import contextmanager
import getpass
import json
from pathlib import Path, PurePosixPath
import sys
import warnings
from urllib.parse import quote


def http_status(error):
    return getattr(getattr(error, "response", None), "status_code", None)


@contextmanager
def login():
    from tapipy.tapis import Tapis

    client = None
    password = None
    try:
        print("Login: https://designsafe.tapis.io (credentials are not saved)")
        username = input("DesignSafe username: ").strip()
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            password = getpass.getpass("Password (hidden): ")
        if not username or not password:
            raise ValueError("Username and password are required")
        client = Tapis(base_url="https://designsafe.tapis.io",
                       username=username, password=password)
        client.get_tokens()
        password = None
        client.password = None
        yield client
    finally:
        password = None
        if client is not None:
            client.password = None
            client.access_token = None
            client.refresh_token = None


def remote_path(value):
    path = PurePosixPath(value)
    if not value or "\\" in value or ":" in value or ".." in path.parts or path == PurePosixPath("."):
        raise ValueError("Use a nonempty system-root-relative remote file path")
    if path.is_absolute():
        raise ValueError("Remote upload path must be relative to the Tapis system root")
    return path


def exists(client, system, path):
    try:
        client.files.listFiles(systemId=system, path=str(path), limit=1)
        return True
    except Exception as error:
        if http_status(error) == 404:
            return False
        raise


def upload(client, source, system, path):
    """Create missing parents, but never intentionally replace a remote file."""
    destination = remote_path(path)
    if not source.is_file():
        raise FileNotFoundError("Local upload file is missing")
    if exists(client, system, destination):
        raise FileExistsError("Remote destination already exists; choose a new version/path")
    for parent in reversed(destination.parents):
        if parent == PurePosixPath("."):
            continue
        if not exists(client, system, parent):
            client.files.mkdir(systemId=system, path=str(parent))
    # Tapis has no atomic create-only upload here. Do not upload concurrently
    # to the same destination; recheck immediately before sending the file.
    if exists(client, system, destination):
        raise FileExistsError("Remote destination appeared during preparation")
    with source.open("rb") as stream:
        client.files.insert(systemId=system, path=str(destination), file=stream)
    print(f"Uploaded: tapis://{system}/{destination}")


def download(client, uuid, destination):
    """Stream output ZIP without extracting or overwriting existing files."""
    import requests

    job = client.jobs.getJob(jobUuid=uuid)
    if job.status not in ("FINISHED", "FAILED", "CANCELLED"):
        raise ValueError("Wait for the job to finish before downloading")
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    if destination.exists() or partial.exists():
        raise FileExistsError("Download destination or partial file already exists")
    url = "https://designsafe.tapis.io/v3/jobs/" + quote(uuid, safe="") + "/output/download/"
    # Never forward the authentication header through a redirect.
    with requests.get(url, headers={"X-Tapis-Token": client.access_token.access_token},
                      stream=True, timeout=(30, 120), allow_redirects=False) as response:
        response.raise_for_status()
        if response.status_code != 200:
            raise ValueError("Unexpected download response (redirects are not followed)")
        with partial.open("xb") as stream:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    stream.write(chunk)
    # The response is a ZIP of the job output directory, including results.zip.
    from zipfile import is_zipfile
    if not is_zipfile(partial):
        raise ValueError("Downloaded response is not a ZIP; partial file retained")
    # Exclusive creation prevents a competing process from being overwritten.
    import shutil
    with destination.open("xb") as stream, partial.open("rb") as source:
        shutil.copyfileobj(source, stream)
    partial.unlink()
    print(f"Downloaded: {destination} (not extracted)")


def perform(client, args):
    if args.command == "download":
        return download(client, args.uuid, args.output)
    if args.command == "upload":
        return upload(client, args.source, args.system, args.path)
    if args.command == "status":
        job = client.jobs.getJob(jobUuid=args.uuid)
        for field in ("uuid", "status", "condition", "lastMessage", "remoteJobId",
                      "remoteOutcome", "execSystemExecDir", "execSystemOutputDir",
                      "archiveSystemId", "archiveSystemDir"):
            value = getattr(job, field, None)
            if value is not None:
                print(f"{field}: {value}")
        if getattr(args, "history", False):
            print("Job history:")
            for event in client.jobs.getJobHistory(jobUuid=args.uuid):
                for field in ("created", "event", "eventDetail", "jobStatus", "description"):
                    value = getattr(event, field, None)
                    if value is not None:
                        print(f"  {field}: {value}")
                print()
        return
    data = json.loads(args.definition.read_text(encoding="utf-8"))
    if args.command == "register":
        if data.get("isPublic") or data.get("owner"):
            raise ValueError("Pilot registration must be private and owned by the current user")
        client.apps.createAppVersion(**data)
        print(f"Registered: {data['id']} version {data['version']}")
    else:
        from femora.jobs.platforms import TACCSubmitter

        def show_validation(report):
            for issue in report.issues:
                print(f"{issue.severity}: {issue.field}: {issue.message}")

        job = TACCSubmitter(client).submit_request(data, on_validation=show_validation)
        print(f"Submitted job UUID: {job.uuid}")
        print("Record this UUID. Do not repeat submit to check progress.")


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    up = commands.add_parser("upload", help="Upload one file; refuse existing destinations")
    up.add_argument("source", type=Path)
    up.add_argument("--system", required=True)
    up.add_argument("--path", required=True, help="File path relative to the Tapis system root")
    for name in ("register", "submit"):
        command = commands.add_parser(name)
        command.add_argument("definition", type=Path)
    status = commands.add_parser("status", help="Read job status and archive location")
    status.add_argument("uuid")
    status.add_argument("--history", action="store_true", help="Also show read-only job event history")
    down = commands.add_parser("download", help="Download completed job output as a ZIP")
    down.add_argument("uuid")
    down.add_argument("--output", type=Path, required=True)
    return result


def main():
    args = parser().parse_args()
    if not sys.stdin.isatty():
        print("Run in your own interactive terminal; redirected credentials are not accepted.")
        return 1
    try:
        if args.command == "upload":
            remote_path(args.path)
            if not args.source.is_file():
                raise FileNotFoundError("Local upload file is missing")
            print(f"Upload {args.source} to tapis://{args.system}/{args.path}")
        elif args.command in ("register", "submit"):
            data = json.loads(args.definition.read_text(encoding="utf-8"))
            print(f"{args.command}: {args.definition}")
            # Show only the request being authorized, never authentication data.
            if args.command == "submit":
                print(f"App: {data['appId']} / {data['appVersion']}")
                print(f"Resources: {data.get('nodeCount')} nodes, "
                      f"{data.get('coresPerNode')} cores/node, {data.get('maxMinutes')} minutes")
                for option in data.get("parameterSet", {}).get("schedulerOptions", []):
                    print(f"Scheduler: {option.get('arg')}")
        if args.command not in ("status", "download") and input("Type yes to continue: ").strip() != "yes":
            print("Cancelled; no remote changes.")
            return 1
        with login() as client:
            perform(client, args)
        return 0
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
    except Exception as error:
        # Avoid SDK exception bodies, which may contain request credentials.
        status = http_status(error)
        print(f"Operation failed: {type(error).__name__}" + (f" (HTTP {status})" if status else ""))
        if isinstance(error, FileExistsError):
            print("Destination exists; nothing was overwritten.")
        if args.command in ("submit", "register"):
            print("If a request reached Tapis, it may have succeeded despite a lost response.")
            print("Check your Tapis jobs/apps before retrying; this helper does not retry writes.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
