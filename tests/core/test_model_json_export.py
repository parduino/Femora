import inspect
import json
from pathlib import Path

import femora.components.element.std_brick  # noqa: F401
import femora.components.material.nd  # noqa: F401
import pytest

from femora.core.model import Model


@pytest.fixture
def assembled_model(tmp_path):
    model = Model(model_name="json_export_test", model_path=str(tmp_path))
    mat = model.material.nd.elastic_isotropic(user_name="soil", E=1.0e4, nu=0.3, rho=1800.0)
    ele = model.element.brick.std(ndof=3, material=mat)
    model.meshpart.volume.uniform_rectangular_grid(
        user_name="block",
        element=ele,
        x_min=0.0,
        x_max=1.0,
        y_min=0.0,
        y_max=1.0,
        z_min=0.0,
        z_max=1.0,
        nx=1,
        ny=1,
        nz=1,
    )
    model.assembler.create_section(meshparts=["block"], num_partitions=1, merge_points=False)
    model.assembler.assemble(merge_points=False)
    model.process.add_step(model.actions.reset(), description="Reset model")
    return model


def test_export_json_helpers_live_in_io_module():
    from femora.io.export_json import build_model_snapshot, export_to_json

    assert export_to_json.__module__ == "femora.io.export_json"
    assert build_model_snapshot.__module__ == "femora.io.export_json"


def test_model_export_to_json_is_thin_wrapper():
    source = inspect.getsource(Model.export_to_json)
    assert "from femora.io.export_json import export_to_json" in source
    assert "build_model_snapshot" not in source
    assert "json.dump" not in source


def test_export_to_json_requires_filename_or_model_metadata():
    model = Model()
    with pytest.raises(ValueError, match="Either provide a filename or set model_name and model_path"):
        model.export_to_json()


def test_export_to_json_writes_valid_snapshot(assembled_model, tmp_path):
    json_file = tmp_path / "snapshot.json"
    assert assembled_model.export_to_json(str(json_file)) is True
    assert json_file.exists()

    payload = json.loads(json_file.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["format"] == "femora_model_snapshot"
    assert payload["model"]["model_name"] == "json_export_test"
    assert payload["model"]["class"] == "Model"
    assert payload["tag_starts"] == {"node": 1, "element": 1, "core": 0}

    managers = payload["managers"]
    assert isinstance(managers["materials"], list)
    assert isinstance(managers["elements"], list)
    assert isinstance(managers["regions"], list)
    assert isinstance(managers["constraints"]["sp"], list)
    assert isinstance(managers["analyses"]["analysis"], list)

    material = next(item for item in managers["materials"] if item["user_name"] == "soil")
    assert material["tag"] == 1
    assert material["type"] == "ElasticIsotropicMaterial"
    assert "opensees_class" in material

    meshpart = next(item for item in payload["meshparts"] if item["user_name"] == "block")
    assert meshpart["tag"] == 1
    assert meshpart["element_tag"] == 1
    assert meshpart["n_points"] > 0
    assert meshpart["n_cells"] > 0
    assert len(meshpart["bounds"]) == 6
    assert "points" not in meshpart
    assert "connectivity" not in meshpart

    assert payload["assembled_mesh"]["exists"] is True
    assert payload["assembled_mesh"]["n_points"] > 0
    assert payload["assembled_mesh"]["n_cells"] > 0
    assert "points" not in payload["assembled_mesh"]

    assert payload["assembly_sections"]
    section = payload["assembly_sections"][0]
    assert section["meshpart_names"] == ["block"]
    assert section["meshpart_tags"] == [1]
    assert "mesh_summary" in section

    assert payload["process"]["num_steps"] == 1
    assert payload["process"]["steps"][0]["type"] == "ResetAction"
    assert payload["process"]["steps"][0]["description"] == "Reset model"


def test_standalone_export_to_json_matches_wrapper(assembled_model, tmp_path):
    from femora.io.export_json import export_to_json

    wrapper_file = tmp_path / "wrapper.json"
    direct_file = tmp_path / "direct.json"
    assembled_model.export_to_json(str(wrapper_file))
    export_to_json(assembled_model, filename=str(direct_file))
    assert wrapper_file.read_text(encoding="utf-8") == direct_file.read_text(encoding="utf-8")


def test_export_json_default_filename_uses_model_metadata(assembled_model, tmp_path):
    default_file = tmp_path / "json_export_test.json"
    assembled_model.export_to_json()
    assert default_file.exists()
    payload = json.loads(default_file.read_text(encoding="utf-8"))
    assert payload["model"]["model_path"] == str(tmp_path)


def test_core_model_does_not_contain_json_export_logic():
    source = Path("src/femora/core/model.py").read_text(encoding="utf-8")
    assert "build_model_snapshot" not in source
    assert "json.dump" not in source
