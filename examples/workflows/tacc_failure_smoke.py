"""Deliberately fail a remote task to verify error propagation and archiving."""

import argparse
from pathlib import Path
import femora as fm


def fail(ctx):
    (ctx.output_dir / "failure-marker.txt").write_text(
        "FEMORA_EXPECTED_FAILURE: task started\n", encoding="utf-8")
    raise RuntimeError("FEMORA_EXPECTED_FAILURE: intentional acceptance test")


def must_not_run(ctx):
    (ctx.output_dir / "unexpected.txt").write_text("ERROR: later stage ran", encoding="utf-8")


def build_workflow():
    workflow = fm.Workflow("tacc-failure-smoke")
    workflow.add("intentional-failure", tasks=[fm.tasks.Python("fail", fail)])
    workflow.add("blocked-stage", tasks=[fm.tasks.Python("must-not-run", must_not_run)])
    workflow.outputs("**/failure-marker.txt", "**/unexpected.txt", "**/stdout.log")
    return workflow


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    args = parser.parse_args()
    print(fm.jobs.bundle(source=__file__, destination=args.bundle, inputs={}))
