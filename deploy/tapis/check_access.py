"""Interactive, read-only DesignSafe access check. Never persists credentials."""

import argparse
import getpass
from pathlib import PurePosixPath
import sys
import warnings


def error_summary(error):
    # SDK exception strings can contain request details; never print them.
    status = getattr(getattr(error, "response", None), "status_code", None)
    return f"HTTP {status}" if isinstance(status, int) else type(error).__name__


def check_systems(client):
    success = True
    for system_id in ("stampede3", "designsafe.storage.default"):
        try:
            system = client.systems.getSystem(systemId=system_id)
            print(f"{system_id}: system definition accessible")
            for field in ("enabled", "canExec", "effectiveUserId", "defaultAuthnMethod"):
                value = getattr(system, field, None)
                if value is not None:
                    print(f"  {field}: {value}")
        except Exception as error:
            print(f"{system_id}: check failed ({error_summary(error)})")
            success = False
    print("Definition access does not prove remote login, file access, or allocation access.")
    print("No files uploaded, apps registered, or jobs submitted.")
    return 0 if success else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--files", action="store_true", help="Also check directory listing access")
    parser.add_argument("--queues", action="store_true", help="List live Tapis logical queue limits")
    parser.add_argument("--system", default="stampede3", help="Execution system for queue discovery")
    parser.add_argument("--stampede-dir", default="/work2/08189/amnp95/stampede3/femora-tapis",
                        help="Absolute native path to the shared installation")
    args = parser.parse_args()
    if not sys.stdin.isatty():
        print("Run this helper in your own interactive terminal, not through redirected input.")
        return 1
    try:
        from tapipy.tapis import Tapis
    except ImportError:
        print("Cannot import tapipy. Use an environment with a working tapipy installation.")
        return 1

    client = None
    password = None
    try:
        print("Read-only login check: https://designsafe.tapis.io")
        username = input("DesignSafe username: ").strip()
        if not username:
            print("Username is required.")
            return 1
        # Refuse getpass's visible-input fallback if terminal echo cannot be disabled.
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            password = getpass.getpass("Password (hidden): ")
        if not password:
            print("Password is required.")
            return 1
        client = Tapis(base_url="https://designsafe.tapis.io",
                       username=username, password=password)
        client.get_tokens()
        client.password = None
        password = None
        print("Authentication succeeded. Tokens remain in this process only.")
        status = check_systems(client)
        if args.queues:
            from femora.jobs.platforms import TACCValidator
            queues = TACCValidator(client).queues(args.system)
            print(f"Logical queues exposed by {args.system}:")
            for queue in queues:
                print(f"  {queue.name} (Slurm: {queue.hpc_queue}): "
                      f"nodes={queue.min_nodes}..{queue.max_nodes}, "
                      f"cores/node={queue.min_cores_per_node}..{queue.max_cores_per_node}, "
                      f"minutes={queue.min_minutes}..{queue.max_minutes}")
            print("Missing/negative limits are not verified hardware capacities.")
        if args.files:
            status = max(status, check_files(client, username, args.stampede_dir))
        return status
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return 1
    except getpass.GetPassWarning:
        print("Hidden password entry is unavailable. Use a normal terminal.")
        return 1
    except Exception as error:
        print(f"Login check failed ({error_summary(error)}).")
        print("Check credentials, network access, or any required DesignSafe login steps.")
        return 1
    finally:
        password = None
        if client is not None:
            client.password = None
            client.access_token = None
            client.refresh_token = None


def check_files(client, username, stampede_dir):
    success = True
    for system_id in ("stampede3", "designsafe.storage.default"):
        try:
            if system_id == "stampede3":
                system = client.systems.getSystem(systemId=system_id)
                root = PurePosixPath(system.rootDir)
                target = PurePosixPath(stampede_dir)
                if not root.is_absolute() or not target.is_absolute() or ".." in target.parts:
                    raise ValueError("Expected absolute paths")
                # Files API paths are relative to the system's effective root.
                path = target.relative_to(root).as_posix()
            else:
                path = username
            client.files.listFiles(systemId=system_id, path=path, limit=5)
            print(f"{system_id}: directory listing succeeded ({path})")
        except Exception as error:
            print(f"{system_id}: directory check failed ({error_summary(error)})")
            success = False
    print("Read-only checks complete. No directory contents displayed or files changed.")
    print("Listing access does not prove write permissions or scheduler access.")
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
