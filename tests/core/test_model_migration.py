import inspect
import re
from pathlib import Path

import femora
from femora.core.model import Model


def _source_has_model_get_instance_call(source: str) -> bool:
    stripped = re.sub(r'(["\']).*?\1', "", source, flags=re.DOTALL)
    return bool(re.search(r"\bModel\.get_instance\s*\(", stripped))


def _strip_string_literals(source: str) -> str:
    return re.sub(r'(["\']).*?\1', "", source, flags=re.DOTALL)


def test_authoritative_runtime_class_is_model():
    assert Model.__module__ == "femora.core.model"
    assert inspect.getfile(Model).endswith("core" + "\\model.py") or inspect.getfile(Model).endswith(
        "core/model.py"
    )


def test_fm_model_constructor():
    model = femora.Model()
    assert isinstance(model, Model)


def test_model_is_primary_public_name():
    assert femora.Model is Model
    assert not hasattr(femora, "material")
    assert not hasattr(femora, "process")
    assert not hasattr(femora, "actions")
    assert not hasattr(femora, "MeshMaker")
    assert not hasattr(Model, "get_instance")


def test_model_does_not_expose_gui():
    assert not hasattr(Model, "gui")
    source = Path("src/femora/core/model.py").read_text(encoding="utf-8")
    assert "def gui(" not in source
    assert "femora.gui" not in source
    assert "MainWindow" not in source


def test_non_gui_tests_and_benchmarks_avoid_legacy_model_accessors():
    allowed = {
        "tests/core/test_model_migration.py",
    }
    repo_root = Path(__file__).resolve().parents[2]
    violations = []
    for root in (repo_root / "tests", repo_root / "benchmarks"):
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            rel = path.relative_to(repo_root).as_posix()
            if rel in allowed:
                continue
            source = path.read_text(encoding="utf-8")
            stripped = _strip_string_literals(source)
            if _source_has_model_get_instance_call(source):
                violations.append(rel)
            if "femora.get_instance()" in stripped:
                violations.append(rel)
            if re.search(r"\bfemora\.(material|element|meshpart|assembler|analysis|pattern|process|actions|interface|mask|mass|region|constraint|load|time_series|ground_motion|transformation|section|recorder|damping)\b", stripped):
                violations.append(rel)
            if "MeshMaker" in stripped:
                violations.append(rel)
    assert violations == []


def test_femora_module_exposes_model_only():
    public_names = set(dir(femora))
    assert "Model" in public_names
    assert "material" not in public_names
    assert "process" not in public_names
    assert "actions" not in public_names
