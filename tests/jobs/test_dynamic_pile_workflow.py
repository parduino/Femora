"""Workflow packaging and partition-aware pile response regression checks."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from zipfile import ZipFile

import numpy as np
import pytest


ROOT = Path(__file__).parents[2] / "examples/soil_structure_interaction"


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("boundary,expected", [
    ("Fixed", (8, 0, 8)), ("Rayleigh", (8, 8, 16)), ("PML", (8, 8, 16)),
])
def test_partition_budgets(boundary, expected):
    import ast
    tree = ast.parse((ROOT / "dynamic_pile_soil_interaction.py").read_text())
    builder = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                   and node.name == "build_model")
    names = ("physical_parts", "absorber_parts", "ranks")
    assignments = [node for node in builder.body if isinstance(node, ast.Assign)
                   and isinstance(node.targets[0], ast.Name) and node.targets[0].id in names]
    scope = {"BOUNDARY_TYPE": boundary}
    exec(compile(ast.Module(body=assignments, type_ignores=[]), "partitions", "exec"), scope)
    assert tuple(scope[name] for name in names) == expected


def test_stage_order_and_rank_budget():
    model = load("dynamic_pile_soil_interaction")
    workflow = model.build_workflow()
    prepare, build, solve, compare = workflow.stages
    assert [stage.name for stage in workflow.stages] == ["input", "build", "solve", "compare"]
    assert prepare.tasks[0].function is model.create_drm
    assert all(task.function is model.build_model for task in build.tasks)
    assert not build.parallel
    assert [task.name for task in build.tasks] == ["fixed", "rayleigh", "pml"]
    assert solve.parallel
    assert [task.ranks for task in solve.tasks] == [8, 16, 16]
    assert sum(task.cores for task in solve.tasks) == 40
    assert not compare.parallel
    assert "build/*/results/**/*" not in workflow.output_patterns
    assert [task.kwargs for task in build.tasks] == [
        {"boundary": "Fixed"}, {"boundary": "Rayleigh"}, {"boundary": "PML"},
    ]
    assert [task.script for task in solve.tasks] == [
        "build/fixed/model.tcl", "build/rayleigh/model.tcl", "build/pml/model.tcl",
    ]


def test_bundle_contains_postprocessor_and_motion_files(tmp_path):
    model = load("dynamic_pile_soil_interaction")
    archive = model.fm.jobs.bundle(
        source=ROOT / "dynamic_pile_soil_interaction.py", destination=tmp_path / "pile.zip",
        inputs={}, files={
            model.POSTPROCESS: ROOT / model.POSTPROCESS,
            "motions/ricker_surface.acc": model.motions_dir() / "ricker_surface.acc",
            "motions/ricker_surface.time": model.motions_dir() / "ricker_surface.time",
        },
    )
    with ZipFile(archive) as zipped:
        metadata = json.loads(zipped.read("bundle.json"))
        assert set(metadata["files"]) == {
            model.POSTPROCESS, "motions/ricker_surface.acc", "motions/ricker_surface.time",
        }
        assert json.loads(zipped.read("inputs.json")) == {}
        assert b"if __name__" in zipped.read("workflow.py")


def test_response_uses_cross_partition_selection(tmp_path, monkeypatch):
    post = load("dynamic_pile_soil_interaction_postprocess")
    directory = tmp_path / "pml/results"
    directory.mkdir(parents=True)
    (directory / "dynamic_pile_response7.vtkhdf").touch()
    results = Mock()
    results.__enter__ = Mock(return_value=results)
    results.__exit__ = Mock(return_value=False)
    results.times = np.array([0.0, 0.005])
    results.point_history.return_value = np.ones((2, 3))
    monkeypatch.setattr(post.fm.results, "open", lambda _: results)
    time, displacement = post.read_head_response("pml", tmp_path)
    results.nearest_point.assert_called_once()
    assert results.nearest_point.call_args.kwargs["tolerance"] == 1e-6
    results.point_history.assert_called_once_with("displacement", results.nearest_point.return_value)
    assert displacement.shape == (2, 3)
    assert time[-1] == 0.005


def test_comparison_requires_all_cases(tmp_path):
    post = load("dynamic_pile_soil_interaction_postprocess")
    with pytest.raises(FileNotFoundError, match="Missing boundary results"):
        post.generate_results(tmp_path, require_all=True)


def test_cases_share_one_drm(tmp_path, monkeypatch):
    model = load("dynamic_pile_soil_interaction")
    # Stop at construction: verify path handoff without rebuilding the mesh.
    constructor = Mock(side_effect=RuntimeError("stop before mesh construction"))
    monkeypatch.setattr(model, "Model", constructor)
    drm_file = tmp_path / "input/drm/drmload.h5drm"
    drm_file.parent.mkdir(parents=True)
    drm_file.touch()
    for name, boundary in (("fixed", "Fixed"), ("rayleigh", "Rayleigh"), ("pml", "PML")):
        context = SimpleNamespace(
            workspace=tmp_path, output_dir=tmp_path / "build" / name,
            result=Mock(return_value=drm_file),
        )
        with pytest.raises(RuntimeError, match="stop before mesh construction"):
            model.build_model(context, boundary)
        context.result.assert_called_once_with("input", "drm")
    assert [Path(call.kwargs["model_path"]) for call in constructor.call_args_list] == [
        tmp_path / "build/fixed", tmp_path / "build/rayleigh", tmp_path / "build/pml",
    ]


def test_drm_is_independent_of_model_construction(tmp_path, monkeypatch):
    model = load("dynamic_pile_soil_interaction")
    constructor = Mock(side_effect=AssertionError("DRM must not build a Femora model"))
    monkeypatch.setattr(model, "Model", constructor)
    transfer = Mock()
    transfer.deconvolve.return_value = (Mock(), None, None)
    monkeypatch.setattr(model, "TransferFunction", Mock(return_value=transfer))
    monkeypatch.setattr(model.TimeHistory, "load", Mock())
    context = SimpleNamespace(workspace=tmp_path, output_dir=tmp_path / "input/drm")
    assert model.create_drm(context) == tmp_path / "input/drm/drmload.h5drm"
    box = transfer.createDRM.call_args.args[0]
    assert box.n_cells == 24 * 10 * 12
    assert box.bounds == model.SOIL_BOUNDS
    assert np.any(np.isclose(box.points[:, 2], -2.0))
    assert all(layer["damping"] == 0.0 for layer in model.TransferFunction.call_args.kwargs["soil_profile"])
    constructor.assert_not_called()


def test_workflow_is_explicit_for_tutorial_readers():
    import ast
    tree = ast.parse((ROOT / "dynamic_pile_soil_interaction.py").read_text())
    factory = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                   and node.name == "build_workflow")
    assert not any(isinstance(node, (ast.For, ast.ListComp, ast.DictComp, ast.GeneratorExp))
                   for node in ast.walk(factory))


def test_comparison_writes_plot_and_histories(tmp_path, monkeypatch):
    import matplotlib
    matplotlib.use("Agg")
    post = load("dynamic_pile_soil_interaction_postprocess")
    monkeypatch.setattr(post, "read_head_response", lambda *args: (
        np.array([0.0, 0.005]), np.zeros((2, 3)),
    ))
    artifacts = post.generate_results(tmp_path, require_all=True)
    assert len(artifacts) == 4
    assert all(path.is_file() for path in artifacts)
    assert artifacts[1].read_text().splitlines()[0] == "time_s,dx_m,dy_m,dz_m"
    renderer = Mock(side_effect=lambda root, output: (
        output / "boundary_comparison.mp4", output / "boundary_comparison_preview.png",
        output / "movie_settings.json",
    ))
    monkeypatch.setattr(post, "render_comparison_movie", renderer)
    artifacts = post.generate_results(tmp_path, require_all=True, movies=True)
    assert len(artifacts) == 7
    renderer.assert_called_once_with(tmp_path, tmp_path / "post_processing")


def test_comparison_plot_pairs_each_absorber_with_fixed(tmp_path, monkeypatch):
    import matplotlib
    matplotlib.use("Agg")
    post = load("dynamic_pile_soil_interaction_postprocess")
    original = post.plt.subplots
    captured = []

    def subplots(*args, **kwargs):
        figure, axes = original(*args, **kwargs)
        captured.extend(axes)
        return figure, axes

    monkeypatch.setattr(post.plt, "subplots", subplots)
    responses = {mode: (np.array([0.0, 1.0]), np.ones((2, 3)) * 0.001)
                 for mode in ("fixed", "pml", "rayleigh")}
    post.plot_head_comparison(responses, tmp_path / "comparison.png")
    assert [axis.get_title() for axis in captured] == ["Fixed vs PML", "Fixed vs Rayleigh"]
    assert [line.get_label() for line in captured[0].lines] == [
        "Fixed boundary", "PML absorbing boundary"]
    assert [line.get_label() for line in captured[1].lines] == [
        "Fixed boundary", "Rayleigh absorbing boundary"]
    assert all(np.allclose(line.get_ydata(), 1.0) for axis in captured for line in axis.lines)
    assert (tmp_path / "comparison.png").is_file()


def test_movie_defaults_use_perspective_and_half_speed():
    import ast
    import inspect
    post = load("dynamic_pile_soil_interaction_postprocess")
    assert inspect.signature(post.render_comparison_movie).parameters["stride"].default == 5
    tree = ast.parse(inspect.getsource(post.render_comparison_movie))
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    assert any(ast.unparse(node.func) == "plotter.disable_parallel_projection" for node in calls)
    assert not any(ast.unparse(node.func) == "plotter.enable_parallel_projection" for node in calls)
    projection = next(node for node in calls if ast.unparse(node.func) == "plotter.disable_parallel_projection")
    camera = next(node for node in ast.walk(tree) if isinstance(node, ast.Assign)
                  and ast.unparse(node.targets[0]) == "plotter.camera_position")
    assert camera.lineno > projection.lineno
    writer = next(node for node in calls if ast.unparse(node.func) == "plotter.open_movie")
    assert next(kw.value.value for kw in writer.keywords if kw.arg == "framerate") == 20


def test_example_uses_native_transient_and_preserves_boundary_layers():
    import ast

    tree = ast.parse((ROOT / "dynamic_pile_soil_interaction.py").read_text())
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    transient = [node for node in calls if ast.unparse(node.func) == "model.analysis.transient"]
    assert len(transient) == 1
    assert {kw.arg for kw in transient[0].keywords} >= {"dt", "final_time", "max_retries"}
    assert not any(ast.unparse(node.func) == "model.actions.tcl" for node in calls)
    absorbers = [node for node in calls if ast.unparse(node.func) == "model.interface.boundary.absorber"]
    assert len(absorbers) == 2
    assert [next(kw.value.value for kw in node.keywords if kw.arg == "num_layers")
            for node in absorbers] == [3, 5]
    assert [next(kw.value.value for kw in node.keywords if kw.arg == "rayleigh_damping")
            for node in absorbers] == [0.10, 0.95]
    assert all(next(kw.value.value for kw in node.keywords if kw.arg == "match_damping") is False
               for node in absorbers)
    assert not any(ast.unparse(node.func) == "model.damping.frequency_rayleigh" for node in calls)
    model = load("dynamic_pile_soil_interaction")
    assert model.FINAL_TIME == 12.0


def test_import_does_not_login_or_submit(monkeypatch):
    import femora as fm
    from femora.jobs.platforms import TACCPlatform

    login, submit = Mock(), Mock()
    monkeypatch.setattr(TACCPlatform, "login", login)
    monkeypatch.setattr(fm, "submit", submit)
    load("dynamic_pile_soil_interaction")
    login.assert_not_called()
    submit.assert_not_called()
