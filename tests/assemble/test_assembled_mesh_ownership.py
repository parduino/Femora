# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

import numpy as np
import pyvista as pv
import pytest

import femora.components.material.nd  # noqa: F401 — register material types
import femora.components.element.std_brick  # noqa: F401 — register element types

from femora.core.assembler import Assembler as CoreAssembler
from femora.core.model import Model


@pytest.fixture
def mesh_maker():
    mk = Model()
    mk.clear_model()
    return mk


def _make_dummy_assembled_mesh() -> pv.UnstructuredGrid:
    points = np.array(
        [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        dtype=float,
    )
    cells = np.array([4, 0, 1, 2, 3], dtype=np.int64)
    return pv.UnstructuredGrid(cells, [pv.CellType.TETRA], points)


def test_mesh_maker_starts_with_no_assembled_mesh(mesh_maker):
    assert mesh_maker.assembled_mesh is None
    assert not hasattr(mesh_maker.assembler, "AssembeledMesh")


def test_mesh_maker_owns_core_assembler_instance(mesh_maker):
    assert isinstance(mesh_maker.assembler, CoreAssembler)
    assert type(mesh_maker.assembler) is CoreAssembler


def test_delete_assembled_mesh_clears_mesh_maker_state(mesh_maker):
    mesh_maker.assembled_mesh = _make_dummy_assembled_mesh()

    mesh_maker.assembler.delete_assembled_mesh()

    assert mesh_maker.assembled_mesh is None


def test_clear_model_clears_mesh_maker_assembled_mesh(mesh_maker):
    mesh_maker.assembled_mesh = _make_dummy_assembled_mesh()

    mesh_maker.clear_model()

    assert mesh_maker.assembled_mesh is None


def test_assembly_populates_mesh_maker_assembled_mesh(mesh_maker):
    mat = mesh_maker.material.nd.elastic_isotropic(user_name="mat", E=1.0, nu=0.3, rho=1.0)
    ele = mesh_maker.element.brick.std(ndof=3, material=mat)
    mesh_maker.meshpart.volume.uniform_rectangular_grid(
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

    mesh_maker.assembler.create_section(meshparts=["block"], num_partitions=1, merge_points=False)
    mesh_maker.assembler.assemble(merge_points=False)

    assert mesh_maker.assembled_mesh is not None
    assert mesh_maker.assembled_mesh.n_cells > 0


def test_mesh_maker_constructs_assembler_with_model_ownership(mesh_maker):
    from pathlib import Path

    assert mesh_maker.assembler._mesh_maker is mesh_maker
    mesh_maker_source = Path("src/femora/core/model.py").read_text(encoding="utf-8")
    assert "bind_mesh_maker" not in mesh_maker_source
    assert "Assembler(mesh_maker=self)" in mesh_maker_source
    assert "from femora.core.assembler import Assembler" in mesh_maker_source
    assert "from femora.components.Assemble.Assembler import Assembler" not in mesh_maker_source


def test_non_gui_production_avoids_legacy_assembler_compatibility_paths():
    from pathlib import Path

    excluded_gui_files = {
        "AssemblerGUI.py",
        "drmAbsorbingGUI.py",
        "drmPatternGUI.py",
        "drmProcessGUI.py",
        "sp_constraint_gui.py",
    }
    forbidden_patterns = (
        "Assembler.get_instance()",
        "assembler.AssembeledMesh",
        "Assembler().AssembeledMesh",
        ".AssembeledActor",
        ".Assemble(",
    )

    violations = []
    for path in Path("src/femora").rglob("*.py"):
        rel = path.relative_to("src/femora").as_posix()
        if rel.startswith("gui/"):
            continue
        if path.name in excluded_gui_files:
            continue
        if path.name == "Assembler.py" and "Assemble" in path.parts:
            continue

        source = path.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            if pattern in source:
                violations.append(f"{rel}: {pattern}")

    assert violations == []


def test_core_assembler_exposes_only_final_runtime_api():
    from pathlib import Path
    import inspect

    from femora.core.assembler import Assembler

    source = Path("src/femora/core/assembler.py").read_text(encoding="utf-8")
    forbidden_defs = (
        "def bind_mesh_maker(",
        "def delete_section(",
        "def get_section(",
        "def get_assembly_section(",
        "def get_sections(",
        "def list_assembly_sections(",
        "def clear_assembly_sections(",
        "def AssembeledMesh",
        "def get_instance",
        "def Assemble(",
    )
    for name in forbidden_defs:
        assert name not in source

    public_methods = {
        name
        for name, member in inspect.getmembers(Assembler, predicate=inspect.isfunction)
        if not name.startswith("_")
    }
    assert public_methods == {
        "assemble",
        "clear",
        "create_section",
        "delete_assembled_mesh",
        "get",
        "get_all",
        "get_mesh",
        "get_num_cells",
        "get_num_points",
        "plot",
        "remove",
        "reset",
    }
    assert "def assemble(" in source
    assert not hasattr(Assembler, "AssembeledActor")


def test_set_material_parameter_uses_model_owned_assembled_mesh(mesh_maker):
    mat = mesh_maker.material.nd.elastic_isotropic(user_name="mat", E=1.0, nu=0.3, rho=1.0)
    ele = mesh_maker.element.brick.std(ndof=3, material=mat)
    mesh_maker.meshpart.volume.uniform_rectangular_grid(
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
    mesh_maker.assembler.create_section(meshparts=["block"], num_partitions=1, merge_points=False)
    mesh_maker.assembler.assemble(merge_points=False)

    action = mesh_maker.actions.set_material_parameter(mat, "E", 2.0)
    assert len(action.element_tags) == mesh_maker.assembled_mesh.n_cells


def test_mask_manager_uses_mesh_maker_owned_service(mesh_maker):
    mat = mesh_maker.material.nd.elastic_isotropic(user_name="mat", E=1.0, nu=0.3, rho=1.0)
    ele = mesh_maker.element.brick.std(ndof=3, material=mat)
    mesh_maker.meshpart.volume.uniform_rectangular_grid(
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
    mesh_maker.assembler.create_section(meshparts=["block"], num_partitions=1, merge_points=False)
    mesh_maker.assembler.assemble(merge_points=False)

    manager = mesh_maker.mask
    assert manager._mesh_maker is mesh_maker
    assert manager.nodes._mesh.node_ids.shape[0] == mesh_maker.assembled_mesh.n_points


def test_mass_manager_reads_model_owned_assembled_mesh(mesh_maker):
    mat = mesh_maker.material.nd.elastic_isotropic(user_name="mat", E=1.0, nu=0.3, rho=1.0)
    ele = mesh_maker.element.brick.std(ndof=3, material=mat)
    mesh_maker.meshpart.volume.uniform_rectangular_grid(
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
    mesh_maker.assembler.create_section(meshparts=["block"], num_partitions=1, merge_points=False)
    mesh_maker.assembler.assemble(merge_points=False)

    mass_array = mesh_maker.mass.get_assembled_mass_array()
    assert mass_array is not None
    assert mass_array.shape[0] == mesh_maker.assembled_mesh.n_points
