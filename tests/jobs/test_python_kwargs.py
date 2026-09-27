"""Python task arguments survive process execution and bundle replay."""

import pytest
import femora as fm


def calculate(context, *, value, increment=1):
    return context.inputs["base"] + value + increment


def test_kwargs_are_independent_and_positional_cores_preserved():
    arguments = {"value": 2}
    task = fm.tasks.Python("a", calculate, 1, kwargs=arguments)
    arguments["value"] = 100
    assert task.kwargs == {"value": 2}
    assert task.cores == 1
    assert fm.tasks.Python("b", calculate).kwargs == {}
    with pytest.raises(TypeError, match="mapping"):
        fm.tasks.Python("bad", calculate, kwargs=[])
    with pytest.raises(TypeError, match="strings"):
        fm.tasks.Python("bad", calculate, kwargs={1: 2})


def test_kwargs_across_parallel_processes(tmp_path):
    workflow = fm.Workflow("kwargs")
    workflow.add("compute", parallel=True, tasks=[
        fm.tasks.Python("a", calculate, kwargs={"value": 2}),
        fm.tasks.Python("b", calculate, kwargs={"value": 4, "increment": 3}),
    ])
    result = fm.execute(workflow, workspace=tmp_path, inputs={"base": 10}, cores=2)
    assert result.result("compute", "a") == 13
    assert result.result("compute", "b") == 17


def test_kwargs_survive_bundle_replay(tmp_path):
    source = tmp_path / "workflow.py"
    source.write_text('''import femora as fm
def task(context, *, value):
    return value + context.inputs["base"]
def build_workflow():
    workflow = fm.Workflow("bundled-kwargs")
    workflow.add("compute", tasks=[fm.tasks.Python("value", task, kwargs={"value": 7})])
    return workflow
''', encoding="utf-8")
    archive = fm.jobs.bundle(source=source, destination=tmp_path / "workflow.zip", inputs={"base": 3})
    result = fm.jobs.replay(archive, workspace=tmp_path / "run", cores=1)
    assert result.result("compute", "value") == 10
