"""Reconnect to an existing TACC job. Never creates or submits a workflow."""

import argparse
import getpass
from pathlib import Path
import sys
import warnings


def check_job(job, output=None):
    status = job.status()
    print(f"Job UUID: {job.id}")
    print(f"Status: {status.state} (Tapis: {status.native_state})")
    if output is not None:
        if status.state not in ("succeeded", "failed", "cancelled"):
            print("Job is not finished; no download attempted. Run this check again later.")
            return 1
        destination = job.download(output)
        print(f"Downloaded through job.download(): {destination} (not extracted)")
    return 0


def cancel_job(job, confirm=input):
    status = job.status()
    print(f"Job {job.id}: {status.state} (Tapis: {status.native_state})")
    if status.state in ("succeeded", "failed", "cancelled"):
        print("Job is already terminal; no cancellation sent.")
        return 1
    print("Only cancel a disposable test job. This may stop running work.")
    if confirm("Type the full job UUID to request cancellation: ").strip() != job.id:
        print("Confirmation did not match; no cancellation sent.")
        return 1
    job.cancel()
    print("Cancellation requested, not yet confirmed. Use check to verify CANCELLED.")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="Check status and optionally download completed output")
    check.add_argument("uuid")
    check.add_argument("--output", type=Path)
    cancel = commands.add_parser("cancel", help="Explicitly cancel an existing disposable job")
    cancel.add_argument("uuid")
    args = parser.parse_args()
    if not sys.stdin.isatty():
        parser.error("Use your own interactive terminal for private login")
    if args.command == "check" and args.output is not None:
        if args.output.exists() or args.output.with_name(args.output.name + ".part").exists():
            parser.error("Output or .part file exists; choose a new destination")

    client = None
    password = None
    try:
        from tapipy.tapis import Tapis
        from femora.jobs.platforms import TACCJob

        print("Connect to DesignSafe/Tapis. No jobs will be submitted.")
        username = input("DesignSafe username: ").strip()
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            password = getpass.getpass("Password (hidden): ")
        if not username or not password:
            print("Username and password are required.")
            return 1
        client = Tapis(base_url="https://designsafe.tapis.io", username=username, password=password)
        client.get_tokens()
        password = client.password = None
        # An existing handle needs only its UUID and authenticated client, not
        # app/resource settings used during the original submission.
        job = TACCJob(args.uuid, client)
        if args.command == "cancel":
            return cancel_job(job)
        return check_job(job, args.output)
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled locally. Any existing remote job is unchanged unless cancellation was sent.")
        return 1
    except Exception as error:
        code = getattr(getattr(error, "response", None), "status_code", None)
        print(f"Operation failed ({type(error).__name__}" + (f", HTTP {code}" if code else "") + ").")
        print("Private request details omitted. No automatic retry was made.")
        if args.command == "cancel":
            print("Check the existing job status before retrying cancellation.")
        return 1
    finally:
        password = None
        if client is not None:
            client.password = client.access_token = client.refresh_token = None


if __name__ == "__main__":
    raise SystemExit(main())
