# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

import inspect
import json
from pathlib import Path

import numpy as np
import femora.components.element.std_brick  # noqa: F401 — register element types
import femora.components.material.nd  # noqa: F401 — register material types
import pytest

from femora.core.model import Model


@pytest.fixture
def assembled_model(tmp_path):
    model = Model(model_name="export_test", model_path=str(tmp_path))
    mat = model.material.nd.elastic_isotropic(user_name="mat", E=1.0, nu=0.3, rho=1.0)
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
    return model


def test_export_logic_not_implemented_in_core_model():
    source = Path("src/femora/core/model.py").read_text(encoding="utf-8")
    assert "getFemoraMax" not in source
    assert "FEMORA_REQUIRED_NP" not in source
    assert "mpConstraints" not in source
    assert "def _get_tcl_helper_functions" not in source
    assert "def _get_tcl_file_header" not in source
    assert "def gui(" not in source


def test_model_export_methods_are_thin_wrappers():
    tcl_source = inspect.getsource(Model.export_to_tcl)
    vtk_source = inspect.getsource(Model.export_to_vtk)
    assert "from femora.io.export_tcl import export_to_tcl" in tcl_source
    assert "from femora.io.export_vtk import export_to_vtk" in vtk_source
    assert "getFemoraMax" not in tcl_source
    assert "assembled_mesh.save" not in vtk_source


def test_export_helpers_live_in_io_modules():
    from femora.io.export_tcl import export_to_tcl, _get_tcl_helper_functions
    from femora.io.export_vtk import build_vtk_info_snapshot, export_to_vtk

    assert export_to_tcl.__module__ == "femora.io.export_tcl"
    assert export_to_vtk.__module__ == "femora.io.export_vtk"
    assert build_vtk_info_snapshot.__module__ == "femora.io.export_vtk"
    assert "getFemoraMax" in _get_tcl_helper_functions()


def test_model_export_to_tcl_writes_expected_sections(assembled_model, tmp_path):
    tcl_file = tmp_path / "model.tcl"
    assert assembled_model.export_to_tcl(str(tcl_file)) is True
    content = tcl_file.read_text(encoding="utf-8")
    assert "wipe" in content
    assert "FEMORA_REQUIRED_NP" in content
    assert "# Materials" in content
    assert "# Nodes & Elements" in content
    assert "# Dampings" in content
    assert "# Regions" in content
    assert "# Process" in content
    assert "exit" in content


def test_model_export_to_tcl_writes_recorder_element_groups_without_retagging_mesh(assembled_model, tmp_path):
    group = assembled_model.group.element.from_cells(
        name="recorder_group",
        cell_indices=np.array([0], dtype=np.int64),
    )
    original_regions = assembled_model.assembled_mesh.cell_data["Region"].copy()

    tcl_file = tmp_path / "model.tcl"
    assert assembled_model.export_to_tcl(str(tcl_file)) is True

    content = tcl_file.read_text(encoding="utf-8")
    assert "# Element Groups" in content
    assert f"region {group.tag} -ele 1" in content
    np.testing.assert_array_equal(assembled_model.assembled_mesh.cell_data["Region"], original_regions)


def test_model_export_to_vtk_writes_file(assembled_model, tmp_path):
    vtk_file = tmp_path / "model.vtk"
    assert assembled_model.export_to_vtk(str(vtk_file)) is True
    assert vtk_file.exists()
    assert vtk_file.stat().st_size > 0
    assert "FemoraPartTags" in assembled_model.assembled_mesh.field_data
    assert "FemoraPartNames" in assembled_model.assembled_mesh.field_data


def test_model_export_to_vtk_can_write_info_json(assembled_model, tmp_path):
    vtk_file = tmp_path / "model.vtk"
    info_file = tmp_path / "model_info.json"
    assert assembled_model.export_to_vtk(str(vtk_file), write_info_json=True) is True
    assert vtk_file.exists()
    assert info_file.exists()

    payload = json.loads(info_file.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["format"] == "femora_vtk_info"
    assert payload["vtk_file"] == "model.vtk"
    assert "regions" not in payload
    assert "meshparts" not in payload

    assert payload["femora_part_kinds"]["meshpart"] == 1
    femora_part = next(item for item in payload["femora_parts"] if item["name"] == "block")
    assert femora_part["tag"] == 1
    assert femora_part["kind"] == "meshpart"
    assert femora_part["kind_id"] == 1
    assert femora_part["source_tag"] == 1
    assert set(assembled_model.assembled_mesh.cell_data["FemoraPartTag"]) == {1}
    assert set(assembled_model.assembled_mesh.cell_data["FemoraPartKind"]) == {1}


def test_model_export_to_vtk_without_info_json_preserves_old_behavior(assembled_model, tmp_path):
    vtk_file = tmp_path / "model.vtk"
    info_file = tmp_path / "model_info.json"
    assert assembled_model.export_to_vtk(str(vtk_file), write_info_json=False) is True
    assert vtk_file.exists()
    assert not info_file.exists()


def test_standalone_export_to_tcl_matches_wrapper(assembled_model, tmp_path):
    from femora.io.export_tcl import export_to_tcl

    wrapper_file = tmp_path / "wrapper.tcl"
    direct_file = tmp_path / "direct.tcl"
    assembled_model.export_to_tcl(str(wrapper_file))
    export_to_tcl(assembled_model, filename=str(direct_file))
    assert wrapper_file.read_text(encoding="utf-8") == direct_file.read_text(encoding="utf-8")


def test_non_gui_runtime_avoids_meshmaker_shim_import():
    violations = []
    for path in Path("src/femora").rglob("*.py"):
        rel = path.relative_to("src/femora").as_posix()
        if rel.startswith("gui/"):
            continue
        source = path.read_text(encoding="utf-8")
        if "MeshMaker" in source:
            violations.append(rel)
    assert violations == []
