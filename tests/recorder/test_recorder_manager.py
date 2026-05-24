import pytest

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
