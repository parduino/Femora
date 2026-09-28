"""The workflow guide's runnable example must work without a solver."""

from pathlib import Path

import femora as fm
import pytest


SOURCE = Path(__file__).parents[2] / "examples/workflows/workflow_basics.py"


@pytest.mark.parametrize("number", [4, 7])
def test_tutorial_bundle_replays_and_preserves_return_values(tmp_path, number):
    archive = fm.jobs.bundle(
        source=SOURCE,
        destination=tmp_path / "tutorial.zip",
        inputs={"number": number},
    )
    workspace = tmp_path / "run"
    run = fm.jobs.replay(archive, workspace=workspace, cores=1)

    assert run.result("input", "number") == workspace / "input/number/number.txt"
    assert run.result("calculate", "double") == number * 2
    assert run.result("calculate", "triple") == number * 3
    report = workspace / "report/summary/summary.txt"
    assert run.result("report", "summary") == report
    assert report.read_text() == f"double: {number * 2:.1f}\ntriple: {number * 3:.1f}\n"
    assert set(run.artifacts) == {
        report,
        workspace / "calculate/double/value.txt",
        workspace / "calculate/triple/value.txt",
    }
    assert run.manifest.is_file()
