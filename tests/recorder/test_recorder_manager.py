import pytest
import numpy as np
import pyvista as pv

from femora.core.model import Model
from femora.components.recorder.recorders import (
    DriftRecorder,
    MPCORecorder,
    NodeRecorder,
    VTKHDFRecorder,
)
from femora.core.recorder_base import Recorder
from femora.core.recorder_manager import RecorderManager


@pytest.fixture
def mesh_maker():
    mk = Model()
    mk.clear_model()
    return mk


def test_recorder_manager_model_owned(mesh_maker):
    assert isinstance(mesh_maker.recorder, RecorderManager)
    assert mesh_maker.recorder._mesh_maker is mesh_maker


def test_duplicate_recorder_manager_rejected(mesh_maker):
    with pytest.raises(ValueError, match="already owns a recorder manager"):
        RecorderManager(mesh_maker)


def test_runtime_surface_has_no_editor_helpers():
    from femora.components.recorder import recorders

    assert not hasattr(recorders, "RecorderRegistry")
    for name in ("get_values", "get_parameters", "validate"):
        assert not hasattr(Recorder, name)
    for cls in (NodeRecorder, DriftRecorder, VTKHDFRecorder, MPCORecorder):
        for name in ("get_values", "get_parameters", "validate"):
            assert not hasattr(cls, name)


def test_unmanaged_recorder_has_no_tag(mesh_maker):
    recorder = NodeRecorder(
        file_name="disp.out",
        nodes=[1],
        dofs=[1],
        resp_type="disp",
    )
    assert recorder.tag is None
    assert recorder._owner is None


def test_constructor_validation(mesh_maker):
    with pytest.raises(ValueError, match="DOFs must be specified"):
        NodeRecorder(file_name="bad.out", nodes=[1], resp_type="disp")
    with pytest.raises(ValueError, match="File base name must be specified"):
        mesh_maker.recorder.vtkhdf(resp_types=["disp"])


def test_region_name_requires_manager(mesh_maker):
    with pytest.raises(ValueError, match="manager-owned recorder"):
        MPCORecorder(file_name="out.mpco", regions=["missing_region"])


def test_results_path_requires_manager():
    recorder = DriftRecorder(
        file_name="drift.out",
        i_nodes=1,
        j_nodes=2,
        dof=1,
        perp_dirn=3,
    )
    with pytest.raises(ValueError, match="recorder manager"):
        recorder.to_tcl()


def test_add_recorder_tags_and_tcl(mesh_maker):
    rm = mesh_maker.recorder
    recorder = rm.node(
        file_name="nodes.out",
        nodes=[1, 2],
        dofs=[1, 2],
        resp_type="disp",
    )
    assert recorder.tag == 1
    assert recorder._owner is rm
    tcl = recorder.to_tcl()
    assert "recorder Node" in tcl
    assert "nodes.out" in tcl


def test_direct_factory_api(mesh_maker):
    rm = mesh_maker.recorder
    drift = rm.drift(
        file_name="drift.out",
        i_nodes=1,
        j_nodes=2,
        dof=1,
        perp_dirn=3,
        cores=0,
    )
    assert "recorder Drift" in drift.to_tcl()
    assert "$pid" in drift.to_tcl()


def test_get_remove_clear(mesh_maker):
    rm = mesh_maker.recorder
    first = rm.node(file_name="a.out", nodes=[1], dofs=[1], resp_type="disp")
    second = rm.node(file_name="b.out", nodes=[2], dofs=[1], resp_type="disp")
    assert len(rm.get_all()) == 2
    assert rm.get(first.tag) is first
    rm.remove(first.tag)
    assert first.tag is None
    assert first._owner is None
    assert len(rm.get_all()) == 1
    assert rm.get(second.tag) is second
    rm.clear()
    assert len(rm.get_all()) == 0
    assert second.tag is None


def test_clear_model_resets_recorders(mesh_maker):
    mesh_maker.recorder.vtkhdf(
        file_base_name="results",
        resp_types=["disp"],
    )
    assert len(mesh_maker.recorder.get_all()) == 1
    mesh_maker.clear_model()
    assert len(mesh_maker.recorder.get_all()) == 0


def test_vtkhdf_supports_force_response_types_and_region_tag(mesh_maker):
    recorder = mesh_maker.recorder.vtkhdf(
        file_base_name="results",
        resp_types=["force2D", "force3D", "localForce2D", "localForce3D"],
        region=7,
    )

    tcl = recorder.to_tcl()
    assert "force2D force3D localForce2D localForce3D -region 7" in tcl


def test_vtkhdf_supports_region_instance(mesh_maker):
    region = mesh_maker.region.element()
    recorder = mesh_maker.recorder.vtkhdf(
        file_base_name="results",
        resp_types=["disp"],
        region=region,
    )

    assert f"-region {region.tag}" in recorder.to_tcl()


def test_vtkhdf_rejects_multiple_regions(mesh_maker):
    recorder = mesh_maker.recorder.vtkhdf(
        file_base_name="results",
        resp_types=["disp"],
        regions=[1, 2],
    )

    with pytest.raises(ValueError, match="exactly one region"):
        recorder.to_tcl()


class _DummyMeshPart:
    def __init__(self, user_name, tag):
        self.user_name = user_name
        self.tag = tag


def _install_pile_mesh_fixture(mesh_maker):
    points = np.array(
        [
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 1.0],
        ]
    )
    cells = np.array([2, 0, 1, 2, 2, 3])
    cell_types = np.array([pv.CellType.LINE, pv.CellType.LINE])
    mesh = pv.UnstructuredGrid(cells, cell_types, points)
    mesh.cell_data["MeshPartTag_celldata"] = np.array([10, 20])
    mesh.cell_data["Core"] = np.array([0, 1])
    mesh.cell_data["Region"] = np.array([0, 0])
    mesh_maker.assembled_mesh = mesh

    parts = {
        "pile1": _DummyMeshPart("pile1", 10),
        "pile2": _DummyMeshPart("pile2", 20),
    }
    mesh_maker.meshpart.get = lambda name: parts.get(name)
    return mesh, parts


def test_pile_vtkhdf_creates_element_group_and_vtkhdf_recorder(mesh_maker):
    mesh, _ = _install_pile_mesh_fixture(mesh_maker)

    recorder = mesh_maker.recorder.pile_vtkhdf(
        ["pile1"],
        file_base_name="piles",
        resp_types=["disp", "force3D", "localForce3D"],
        delta_t=0.01,
    )

    assert isinstance(recorder, VTKHDFRecorder)
    assert mesh.cell_data["Region"].tolist() == [0, 0]
    assert recorder.region is None
    assert recorder.element_group.name == "pile_vtkhdf_region"
    assert recorder.element_group.cell_indices.tolist() == [0]
    assert mesh_maker.group.element.get("pile_vtkhdf_region") is recorder.element_group
    tcl = recorder.to_tcl()
    assert "recorder vtkhdf" in tcl
    assert "disp force3D localForce3D" in tcl
    assert f"-region {recorder.element_group.tag}" in tcl


def test_vtkhdf_accepts_element_group_name(mesh_maker):
    _install_pile_mesh_fixture(mesh_maker)
    group = mesh_maker.group.element.from_meshparts(
        name="pile_group",
        meshparts=["pile1"],
        line_cells_only=True,
    )

    recorder = mesh_maker.recorder.vtkhdf(
        file_base_name="piles",
        resp_types=["disp"],
        group="pile_group",
    )

    assert f"-region {group.tag}" in recorder.to_tcl()


def test_pile_vtkhdf_uses_default_response_types(mesh_maker):
    _install_pile_mesh_fixture(mesh_maker)

    recorder = mesh_maker.recorder.pile_vtkhdf(["pile1"], file_base_name="piles")

    assert recorder.resp_types == ["disp", "vel", "accel", "force3D", "localForce3D"]
