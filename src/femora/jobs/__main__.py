"""Replay workflows and discover or track submitted jobs from the terminal."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from .bundle import replay
from .backends import TACC


def main(argv=None, *, prog="python -m femora.jobs") -> None:
    parser = argparse.ArgumentParser(prog=prog)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("replay", help="run a trusted workflow bundle")
    run.add_argument("bundle")
    run.add_argument("--workspace", required=True)
    run.add_argument("--cores", type=int)
    run.add_argument("--backend", choices=("local", "tacc"), default="local")
    listing = commands.add_parser("list", help="list cached local job records (no login)")
    listing.add_argument("--json", action="store_true")
    listing.add_argument("--remote", action="store_true", help="login and discover remote Femora jobs")
    listing.add_argument("--tenant", default="https://designsafe.tapis.io")
    listing.add_argument("--app-id", help="also recognize this exact custom Femora app ID")
    track = commands.add_parser("track", help="interactive terminal job tracker")
    track.add_argument("--poll-interval", type=int, default=30)
    track.add_argument("--tenant", default="https://designsafe.tapis.io")
    track.add_argument("--app-id", help="also recognize this exact custom Femora app ID")
    add = commands.add_parser("add", help="record an existing job without submitting")
    add.add_argument("uuid")
    add.add_argument("--name")
    add.add_argument("--platform", choices=("tacc",), default="tacc")
    add.add_argument("--tenant", default="https://designsafe.tapis.io")
    add.add_argument("--username")
    status = commands.add_parser("status", help="fetch live status for a recorded job")
    status.add_argument("uuid")
    args = parser.parse_args(argv)
    if args.command == "replay":
        result = replay(args.bundle, workspace=args.workspace, cores=args.cores,
                        backend=TACC() if args.backend == "tacc" else None)
        print(result.manifest)
    else:
        from .tracking import add as add_job, connect, list_jobs
        if args.command == "list":
            try:
                if args.remote:
                    from .platforms.tacc_remote import TACCPlatform
                    # Keep prompts outside stdout so --json remains machine-readable.
                    from contextlib import redirect_stdout
                    with redirect_stdout(sys.stderr):
                        target = TACCPlatform.login(app_id=args.app_id or "job-tracking", base_url=args.tenant)
                    records = list_jobs(platform=target)
                else:
                    records = list_jobs()
            except Exception as error:
                parser.exit(1, f"Discovery failed ({type(error).__name__}); cached records retained.\n")
            if args.json:
                print(json.dumps([asdict(r) for r in records], indent=2))
            else:
                print("Remote Femora jobs:" if args.remote else "Cached local jobs (no remote refresh):")
                for r in records:
                    print(f"{r.name:30} {r.platform:8} {r.state:10} {r.id}  checked: {r.checked_at or 'never'}")
                if not records:
                    print("No jobs found. Use list --remote to discover jobs, or --app-id for a custom app.")
        elif args.command == "add":
            connection = {"base_url": args.tenant}
            if args.username:
                connection["username"] = args.username
            print(add_job(args.uuid, platform=args.platform, name=args.name, connection=connection).id)
        elif args.command == "track":
            if not sys.stdin.isatty() or not sys.stdout.isatty():
                parser.error("track requires an interactive terminal; use list or list --json instead")
            if args.poll_interval < 10:
                parser.error("poll-interval must be at least 10 seconds")
            from .tracker_ui import JobTracker
            JobTracker(poll_interval=args.poll_interval, tenant=args.tenant, app_id=args.app_id).run()
        elif args.command == "status":
            try:
                state = connect(args.uuid).status()
                print(f"{state.state} ({state.native_state})")
            except Exception as error:
                parser.exit(1, f"Status check failed ({type(error).__name__}); private details omitted.\n")


if __name__ == "__main__":
    main()
