"""Installed command entry point; feature modules own their command logic."""

import argparse
import sys


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "jobs":
        from .jobs.__main__ import main as jobs_main
        return jobs_main(argv[1:], prog="femora jobs")
    parser = argparse.ArgumentParser(prog="femora")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("jobs", help="discover, track, and run workflows")
    parser.parse_args(argv)
