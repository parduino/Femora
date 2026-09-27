"""Disposable two-rank cancellation test. No numerical analysis is performed."""

import argparse
from pathlib import Path


def create(context):
    models = context.workspace / "models"
    models.mkdir(exist_ok=True)
    (models / "wait.tcl").write_text(
        'puts "Cancellation test started on rank [getPID] of [getNP]"\n'
        'flush stdout\n'
        'for {set i 0} {$i < 60} {incr i} {\n'
        '    after 5000\n'
        '    puts "Cancellation test heartbeat: rank [getPID], interval $i"\n'
        '    flush stdout\n'
        '}\n', encoding="ascii",
    )


def completed(context):
    (context.output_dir / "not-cancelled.txt").write_text(
        "The wait completed normally; cancellation did not stop this workflow.\n",
        encoding="ascii",
    )


def build_workflow():
    import femora as fm

    workflow = fm.Workflow("tacc-cancel-smoke")
    workflow.add("create", tasks=[fm.tasks.Python("model", create)])
    workflow.add("wait", tasks=[fm.tasks.OpenSees("disposable", "models/wait.tcl", ranks=2)])
    workflow.add("after-wait", tasks=[fm.tasks.Python("marker", completed)])
    workflow.outputs("**/stdout.log", "**/not-cancelled.txt", "models/*.tcl")
    return workflow


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--bundle", type=Path)
    mode.add_argument("--submit", action="store_true")
    parser.add_argument("--app-id")
    parser.add_argument("--app-version", default="0.1.0")
    parser.add_argument("--allocation")
    args = parser.parse_args()
    import femora as fm

    if args.bundle:
        print(fm.jobs.bundle(source=__file__, destination=args.bundle, inputs={}))
        return 0
    if not args.app_id or not args.allocation:
        parser.error("--submit requires --app-id and --allocation")

    import getpass
    import sys
    import warnings
    from tapipy.tapis import Tapis
    from femora.jobs.platforms import TACCPlatform, TACCSettings

    if not sys.stdin.isatty():
        parser.error("Use your interactive terminal for private login")
    print("Disposable test: Stampede3/skx-dev, 1 node, 48 cores/node, 10 minutes.")
    print(f"Allocation: {args.allocation}. Two MPI ranks wait for five minutes.")
    print("This reserves a node even though the test does little computation.")
    if input("Type yes to submit: ").strip() != "yes":
        return 0
    client = None
    password = None
    try:
        username = input("DesignSafe username: ").strip()
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            password = getpass.getpass("Password (hidden): ")
        if not username or not password:
            raise ValueError("Credentials required")
        client = Tapis(base_url="https://designsafe.tapis.io", username=username, password=password)
        client.get_tokens()
        password = client.password = None
        platform = TACCPlatform(
            client, app_id=args.app_id, app_version=args.app_version,
            storage_system="designsafe.storage.default",
            input_directory=f"{username}/femora-workflows/submissions",
        )
        job = fm.submit(function=build_workflow, platform=platform, settings=TACCSettings(
            system="stampede3", queue="skx-dev", allocation=args.allocation,
            nodes=1, cores_per_node=48, minutes=10,
        ))
        print(f"Disposable job UUID: {job.id}")
        print(f"python examples/workflows/tacc_job_handle.py check {job.id}")
        print(f"python examples/workflows/tacc_job_handle.py cancel {job.id}")
        print("Check again after cancelling until Tapis reports CANCELLED.")
    except Exception as error:
        print(f"Remote operation failed ({type(error).__name__}); private details omitted.")
        print("If submission was attempted, inspect your jobs before retrying: it may have succeeded.")
        return 1
    finally:
        password = None
        if client is not None:
            client.password = client.access_token = client.refresh_token = None
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
