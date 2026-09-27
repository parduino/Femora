"""Tiny MPI launch test: one two-rank solve, then concurrent two/three-rank solves.

Each rank solves an independent one-element spring. This checks launcher rank
counts, offsets, stage ordering, and output collection, NOT a partitioned solver.
Package with ``python tacc_mpi_smoke.py --bundle tiny_mpi.zip`` and replay inside
a five-slot allocation with ``--backend tacc``. Requires MPI-enabled OpenSees.
"""

import argparse
from pathlib import Path

import femora as fm


CASES = {"single": 2, "pair_a": 2, "pair_b": 3}


def create(ctx):
    models = ctx.workspace / "models"
    models.mkdir(exist_ok=True)
    for name, ranks in CASES.items():
        script = """wipe
set pid [getPID]
set np [getNP]
if {$np != EXPECTED_RANKS} {error "Unexpected MPI size: $np"}
model BasicBuilder -ndm 1 -ndf 1
node 1 0.0
node 2 1.0
fix 1 1
uniaxialMaterial Elastic 1 1000.0
element truss 1 1 2 1.0 1
timeSeries Linear 1
pattern Plain 1 1 {load 2 1.0}
constraints Plain
numberer Plain
system BandGeneral
test NormUnbalance 1.0e-10 10
algorithm Linear
integrator LoadControl 1.0
analysis Static
set ok [analyze 1]
if {$ok != 0} {error "Spring analysis failed on rank $pid"}
set f [open "rank_${pid}.txt" w]
puts $f "$pid $np [nodeDisp 2 1]"
close $f
wipe
"""
        (models / f"{name}.tcl").write_text(
            script.replace("EXPECTED_RANKS", str(ranks)), encoding="ascii"
        )


def compare(ctx):
    summary = []
    for name, ranks in CASES.items():
        stage = "single" if name == "single" else "parallel"
        directory = ctx.result(stage, name).output_dir
        files = list(directory.glob("rank_*.txt"))
        if len(files) != ranks:
            raise RuntimeError(f"{name}: expected {ranks} rank files, found {len(files)}")
        for rank in range(ranks):
            pid, size, displacement = (directory / f"rank_{rank}.txt").read_text().split()
            if int(pid) != rank or int(size) != ranks or abs(float(displacement) - 0.001) > 1e-10:
                raise RuntimeError(f"{name}: invalid result on rank {rank}")
        summary.append(f"{name}: {ranks} ranks, displacement 0.001, passed")
    (ctx.output_dir / "comparison.txt").write_text("\n".join(summary) + "\n", encoding="ascii")


def build_workflow():
    workflow = fm.Workflow("tacc-mpi-smoke")
    workflow.add("create", tasks=[fm.tasks.Python("models", create)])
    workflow.add("single", tasks=[fm.tasks.OpenSees("single", "models/single.tcl", ranks=2)])
    workflow.add("parallel", parallel=True, tasks=[
        fm.tasks.OpenSees(name, f"models/{name}.tcl", ranks=CASES[name])
        for name in ("pair_a", "pair_b")
    ])
    workflow.add("compare", tasks=[fm.tasks.Python("summary", compare)])
    workflow.outputs("**/rank_*.txt", "**/stdout.log", "compare/**/*.txt", "models/*.tcl")
    return workflow


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--bundle", type=Path)
    mode.add_argument("--submit", action="store_true")
    parser.add_argument("--allocation")
    parser.add_argument("--app-id")
    parser.add_argument("--app-version", default="0.1.0")
    parser.add_argument("--queue", default="skx-dev")
    parser.add_argument("--cores-per-node", type=int, default=48)
    args = parser.parse_args()
    if args.bundle:
        print(fm.jobs.bundle(source=__file__, destination=args.bundle, inputs={}))
    else:
        if not args.allocation or not args.app_id:
            parser.error("--submit requires --allocation and --app-id")
        import getpass
        import sys
        import warnings
        from tapipy.tapis import Tapis
        from femora.jobs.platforms import TACCPlatform, TACCSettings, RemoteSubmissionError, SubmissionValidationError

        if not sys.stdin.isatty():
            parser.error("Use an interactive terminal for private login")
        print(f"Submit to Stampede3/{args.queue}, 1 node, {args.cores_per_node} cores, "
              f"20 minutes, allocation {args.allocation}")
        if input("Type yes to submit: ").strip() != "yes":
            raise SystemExit("Cancelled")
        username = input("DesignSafe username: ").strip()
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            password = getpass.getpass("Password (hidden): ")
        client = Tapis(base_url="https://designsafe.tapis.io", username=username, password=password)
        try:
            client.get_tokens()
            password = None
            client.password = None
            target = TACCPlatform(
                client, app_id=args.app_id, app_version=args.app_version,
                storage_system="designsafe.storage.default",
                input_directory=f"{username}/femora-workflows/submissions",
            )
            job = fm.submit(function=build_workflow, platform=target, settings=TACCSettings(
                system="stampede3", queue=args.queue, allocation=args.allocation,
                nodes=1, cores_per_node=args.cores_per_node, minutes=20,
            ))
            print(f"Job UUID: {job.id}")
        except (RemoteSubmissionError, SubmissionValidationError) as error:
            raise SystemExit(str(error)) from None
        except Exception as error:
            raise SystemExit(f"Remote operation failed ({type(error).__name__}); credentials omitted.") from None
        finally:
            password = None
            client.password = client.access_token = client.refresh_token = None
