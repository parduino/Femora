# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

import numpy as np
import pytest
import pyvista as pv

import femora.components.section  # noqa: F401 — register section types

from femora.core.model import Model
from femora.core.event_bus import EventBus, FemoraEvent
from femora.components.interface.embedded_beam_solid_interface import EmbeddedBeamSolidInterface
from femora.components.interface.embedded_node_interface import EmbeddedNodeInterface
from femora.components.interface.embedded_info import EmbeddedInfo
from femora.core.interface_base import InterfaceManager
from femora.components.recorder.recorders import EmbeddedBeamSolidInterfaceRecorder
from femora.components.mesh.line_meshparts import StructuredLineMesh


def _beam_solid_instance_callbacks(interface: EmbeddedBeamSolidInterface) -> list:
    return [
        interface._on_pre_assemble,
        interface._on_post_assemble,
        interface._on_embedded_beam_solid_tcl_export,
    ]


def _assert_beam_solid_instance_callbacks_subscribed(
    mesh_maker, interface: EmbeddedBeamSolidInterface
) -> None:
    subscribers = mesh_maker.events._subscribers
    assert interface._on_pre_assemble in subscribers[FemoraEvent.PRE_ASSEMBLE]
    assert interface._on_post_assemble in subscribers[FemoraEvent.POST_ASSEMBLE]
    assert (
        interface._on_embedded_beam_solid_tcl_export
        in subscribers[FemoraEvent.EMBEDDED_BEAM_SOLID_TCL]
    )


def _assert_beam_solid_instance_callbacks_unsubscribed(
    mesh_maker, interface: EmbeddedBeamSolidInterface
) -> None:
    for callback in _beam_solid_instance_callbacks(interface):
        for subscribers in mesh_maker.events._subscribers.values():
            assert callback not in subscribers


def _assert_beam_solid_instance_callbacks_not_on_global_bus(
    interface: EmbeddedBeamSolidInterface,
) -> None:
    for callback in _beam_solid_instance_callbacks(interface):
        for subscribers in EventBus._subscribers.values():
            assert callback not in subscribers


def _make_node_interface_meshparts(mesh_maker):
    mat = mesh_maker.material.nd.elastic_isotropic(user_name="node_mat", E=1.0, nu=0.3, rho=1.0)
    ele = mesh_maker.element.brick.std(ndof=3, material=mat)
    mesh_maker.meshpart.volume.uniform_rectangular_grid(
        user_name="retained",
        element=ele,
        region=None,
        x_min=0,
        x_max=2,
        y_min=0,
        y_max=2,
        z_min=0,
        z_max=2,
        nx=1,
        ny=1,
        nz=1,
    )
    mesh_maker.meshpart.volume.uniform_rectangular_grid(
        user_name="constrained",
        element=ele,
        region=None,
        x_min=0.5,
        x_max=1.5,
        y_min=0.5,
        y_max=1.5,
        z_min=0,
        z_max=1,
        nx=1,
        ny=1,
        nz=1,
    )


def _assert_node_post_assemble_subscribed(mesh_maker, interface: EmbeddedNodeInterface) -> None:
    assert (
        interface._on_post_assemble
        in mesh_maker.events._subscribers[FemoraEvent.POST_ASSEMBLE]
    )


def _assert_node_post_assemble_unsubscribed(mesh_maker, interface: EmbeddedNodeInterface) -> None:
    assert (
        interface._on_post_assemble
        not in mesh_maker.events._subscribers.get(FemoraEvent.POST_ASSEMBLE, [])
    )


def _assert_manager_conflict_subscribed(mesh_maker, manager: InterfaceManager) -> None:
    assert (
        manager._resolve_beam_solid_conflicts
        in mesh_maker.events._subscribers[FemoraEvent.RESOLVE_CORE_CONFLICTS]
    )
    assert manager._beam_solid_conflict_subscribed is True


def _assert_manager_conflict_unsubscribed(mesh_maker, manager: InterfaceManager) -> None:
    assert (
        manager._resolve_beam_solid_conflicts
        not in mesh_maker.events._subscribers.get(FemoraEvent.RESOLVE_CORE_CONFLICTS, [])
    )
    assert manager._beam_solid_conflict_subscribed is False


def _assert_manager_conflict_not_on_global_bus(manager: InterfaceManager) -> None:
    assert (
        manager._resolve_beam_solid_conflicts
        not in EventBus._subscribers.get(FemoraEvent.RESOLVE_CORE_CONFLICTS, [])
    )


def _assert_no_active_manager_guard_helpers() -> None:
    assert not hasattr(EmbeddedBeamSolidInterface, "_active_interface_manager")
    assert not hasattr(EmbeddedBeamSolidInterface, "_is_active_for_current_model")
    assert not hasattr(EmbeddedNodeInterface, "_active_interface_manager")
    assert not hasattr(EmbeddedNodeInterface, "_is_active_for_current_model")


def _assert_no_class_level_beam_solid_conflict_lifecycle() -> None:
    assert not hasattr(EmbeddedBeamSolidInterface, "_class_subscribed")
    assert not hasattr(EmbeddedBeamSolidInterface, "_active_beam_solid_count")
    assert not hasattr(EmbeddedBeamSolidInterface, "_cls_resolve_core_conflicts")


@pytest.fixture
def mesh_maker():
    mk = Model()
    mk.clear_model()
    EventBus._subscribers.clear()
    mk.interface._beam_solid_count = 0
    mk.interface._beam_solid_conflict_subscribed = False
    return mk


def _make_line_mesh(mesh_maker, *, user_name="beam_mesh"):
    beam_sec = mesh_maker.section.create_section(
        "Elastic", user_name="sec", E=1.0, A=1.0, Iz=1.0, Iy=1.0
    )
    transf = mesh_maker.transformation.transformation3d("Linear", 0, 1, 0)
    beam_ele = mesh_maker.element.beam.disp(ndof=6, section=beam_sec, transformation=transf)
    return mesh_maker.meshpart.line.single_line(
        user_name=user_name,
        element=beam_ele,
        x0=0,
        y0=0,
        z0=0,
        x1=0,
        y1=0,
        z1=1,
        number_of_lines=1,
    )


def _make_structured_line_mesh(mesh_maker, *, user_name="struct_beam"):
    beam_sec = mesh_maker.section.create_section(
        "Elastic", user_name="struct_sec", E=1.0, A=1.0, Iz=1.0, Iy=1.0
    )
    transf = mesh_maker.transformation.transformation3d("Linear", 0, 1, 0)
    beam_ele = mesh_maker.element.beam.disp(ndof=6, section=beam_sec, transformation=transf)
    return mesh_maker.meshpart.line.structured_lines(
        user_name=user_name,
        element=beam_ele,
        base_point_x=0.0,
        base_point_y=0.0,
        base_point_z=0.0,
        normal_x=0.0,
        normal_y=0.0,
        normal_z=1.0,
        grid_size_1=1,
        grid_size_2=1,
        spacing_1=1.0,
        spacing_2=1.0,
        length=1.0,
        number_of_lines=1,
    )


def test_interface_manager_model_owned(mesh_maker):
    assert isinstance(mesh_maker.interface, InterfaceManager)
    assert mesh_maker.interface._mesh_maker is mesh_maker
    _assert_no_active_manager_guard_helpers()


def test_interface_manager_public_api_is_lean(mesh_maker):
    manager = mesh_maker.interface
    assert hasattr(manager, "beam_solid_interface")
    assert hasattr(manager, "node_interface")
    assert hasattr(manager, "get_all")
    assert hasattr(manager, "get")
    assert hasattr(manager, "require")
    assert hasattr(manager, "require_registered")
    assert not hasattr(manager, "create_interface")
    assert not hasattr(manager, "all")


def test_interface_base_has_no_broad_default_event_hooks():
    from femora.core.interface_base import InterfaceBase

    assert not hasattr(InterfaceBase, "_on_pre_assemble")
    assert not hasattr(InterfaceBase, "_on_post_assemble")
    assert not hasattr(InterfaceBase, "_on_pre_export")
    assert not hasattr(InterfaceBase, "_on_post_export")
    assert not hasattr(InterfaceBase, "_on_resolve_core_conflicts")
    assert not hasattr(InterfaceBase, "_on_interface_tcl_export")


def test_interface_subscriptions_are_model_local(mesh_maker):
    _make_line_mesh(mesh_maker)
    _make_node_interface_meshparts(mesh_maker)
    manager = mesh_maker.interface
    beam_iface = manager.beam_solid_interface(
        name="pile_ifc",
        beam_part="beam_mesh",
        radius=0.5,
    )
    node_iface = manager.node_interface(
        name="node_ifc",
        constrained_node="constrained",
    )

    _assert_beam_solid_instance_callbacks_subscribed(mesh_maker, beam_iface)
    _assert_beam_solid_instance_callbacks_not_on_global_bus(beam_iface)
    _assert_node_post_assemble_subscribed(mesh_maker, node_iface)
    _assert_manager_conflict_subscribed(mesh_maker, manager)
    _assert_manager_conflict_not_on_global_bus(manager)
    _assert_no_active_manager_guard_helpers()


def test_require_rejects_unknown_name(mesh_maker):
    with pytest.raises(ValueError, match="not registered in InterfaceManager"):
        mesh_maker.interface.require("missing")


def test_require_registered_rejects_unmanaged(mesh_maker):
    _make_line_mesh(mesh_maker)
    unmanaged = EmbeddedBeamSolidInterface(
        name="orphan",
        beam_part="beam_mesh",
        meshpart=mesh_maker.meshpart,
    )
    with pytest.raises(ValueError, match="not managed by InterfaceManager"):
        mesh_maker.interface.require_registered(unmanaged)


def test_recorder_resolves_interface_name_through_manager(mesh_maker):
    _make_line_mesh(mesh_maker)
    mesh_maker.interface.beam_solid_interface(
        name="pile_ifc",
        beam_part="beam_mesh",
        radius=0.5,
    )
    recorder = mesh_maker.recorder.embedded_beam_solid_interface(
        interface="pile_ifc",
        resp_type=["displacement"],
    )
    resolved = recorder._resolve_interfaces()
    assert len(resolved) == 1
    assert resolved[0].name == "pile_ifc"
    assert resolved[0]._owner is mesh_maker.interface


def test_recorder_rejects_unmanaged_interface_object(mesh_maker):
    _make_line_mesh(mesh_maker)
    unmanaged = EmbeddedBeamSolidInterface(
        name="orphan",
        beam_part="beam_mesh",
        meshpart=mesh_maker.meshpart,
    )
    recorder = EmbeddedBeamSolidInterfaceRecorder(
        interface=unmanaged,
        resp_type=["displacement"],
    )
    mesh_maker.recorder.add(recorder)
    with pytest.raises(ValueError, match="not managed by InterfaceManager"):
        recorder._resolve_interfaces()


def test_unmanaged_recorder_cannot_resolve_interfaces(mesh_maker):
    _make_line_mesh(mesh_maker)
    mesh_maker.interface.beam_solid_interface(
        name="pile_ifc",
        beam_part="beam_mesh",
        radius=0.5,
    )
    recorder = EmbeddedBeamSolidInterfaceRecorder(
        interface="pile_ifc",
        resp_type=["displacement"],
    )
    with pytest.raises(ValueError, match="recorder manager before export"):
        recorder._resolve_interfaces()


def test_first_beam_solid_add_subscribes_manager_conflict_handler(mesh_maker):
    _make_line_mesh(mesh_maker)
    manager = mesh_maker.interface
    assert manager._beam_solid_count == 0
    _assert_manager_conflict_unsubscribed(mesh_maker, manager)
    _assert_no_class_level_beam_solid_conflict_lifecycle()

    mesh_maker.interface.beam_solid_interface(
        name="pile_ifc",
        beam_part="beam_mesh",
        radius=0.5,
    )

    assert manager._beam_solid_count == 1
    _assert_manager_conflict_subscribed(mesh_maker, manager)
    _assert_manager_conflict_not_on_global_bus(manager)


def test_remove_unsubscribes_beam_solid_instance_callbacks(mesh_maker):
    _make_line_mesh(mesh_maker)
    manager = mesh_maker.interface
    iface = mesh_maker.interface.beam_solid_interface(
        name="pile_ifc",
        beam_part="beam_mesh",
        radius=0.5,
    )
    _assert_beam_solid_instance_callbacks_subscribed(mesh_maker, iface)
    _assert_beam_solid_instance_callbacks_not_on_global_bus(iface)
    _assert_manager_conflict_subscribed(mesh_maker, manager)

    mesh_maker.interface.remove("pile_ifc")

    assert iface._owner is None
    _assert_beam_solid_instance_callbacks_unsubscribed(mesh_maker, iface)
    assert manager._beam_solid_count == 0
    _assert_manager_conflict_unsubscribed(mesh_maker, manager)


def test_clear_unsubscribes_beam_solid_instance_callbacks(mesh_maker):
    _make_line_mesh(mesh_maker)
    manager = mesh_maker.interface
    iface = mesh_maker.interface.beam_solid_interface(
        name="pile_ifc",
        beam_part="beam_mesh",
        radius=0.5,
    )
    _assert_beam_solid_instance_callbacks_subscribed(mesh_maker, iface)

    mesh_maker.interface.clear()

    assert iface._owner is None
    _assert_beam_solid_instance_callbacks_unsubscribed(mesh_maker, iface)
    assert manager._beam_solid_count == 0
    _assert_manager_conflict_unsubscribed(mesh_maker, manager)


def test_re_add_after_full_teardown_resubscribes_manager_conflict_handler(mesh_maker):
    _make_line_mesh(mesh_maker)
    manager = mesh_maker.interface
    mesh_maker.interface.beam_solid_interface(
        name="pile_ifc",
        beam_part="beam_mesh",
        radius=0.5,
    )
    mesh_maker.interface.clear()
    _assert_manager_conflict_unsubscribed(mesh_maker, manager)

    mesh_maker.interface.beam_solid_interface(
        name="pile_ifc",
        beam_part="beam_mesh",
        radius=0.5,
    )

    assert manager._beam_solid_count == 1
    _assert_manager_conflict_subscribed(mesh_maker, manager)


def test_structured_line_post_assemble_uses_explicit_attributes(mesh_maker, monkeypatch):
    _make_structured_line_mesh(mesh_maker)
    beam_part = mesh_maker.meshpart.get("struct_beam")
    assert isinstance(beam_part, StructuredLineMesh)
    assert not hasattr(beam_part, "params")

    iface = mesh_maker.interface.beam_solid_interface(
        name="struct_ifc",
        beam_part="struct_beam",
        radius=0.5,
    )
    fork_calls = []
    monkeypatch.setattr(
        iface,
        "_fork_solid_for_single_beam",
        lambda assembled_mesh, beam_cells_idx: fork_calls.append(len(beam_cells_idx)),
    )

    assembled = beam_part.mesh.copy()
    assembled.cell_data["MeshPartTag_celldata"] = np.full(
        assembled.n_cells, beam_part.tag, dtype=np.int32
    )
    assembled.cell_data["Core"] = np.zeros(assembled.n_cells, dtype=np.int32)

    iface._on_post_assemble(assembled_mesh=assembled)

    assert fork_calls
    assert fork_calls[0] > 0


def test_remove_unsubscribes_node_interface_post_assemble(mesh_maker):
    _make_node_interface_meshparts(mesh_maker)
    iface = mesh_maker.interface.node_interface(
        name="node_ifc",
        constrained_node="constrained",
    )
    _assert_node_post_assemble_subscribed(mesh_maker, iface)

    mesh_maker.interface.remove("node_ifc")

    assert iface._owner is None
    _assert_node_post_assemble_unsubscribed(mesh_maker, iface)


def test_clear_unsubscribes_node_interface_post_assemble(mesh_maker):
    _make_node_interface_meshparts(mesh_maker)
    iface = mesh_maker.interface.node_interface(
        name="node_ifc",
        constrained_node="constrained",
    )
    _assert_node_post_assemble_subscribed(mesh_maker, iface)

    mesh_maker.interface.clear()

    assert iface._owner is None
    _assert_node_post_assemble_unsubscribed(mesh_maker, iface)


def test_node_interface_post_assemble_uses_owner_bound_context(mesh_maker, monkeypatch):
    _make_node_interface_meshparts(mesh_maker)
    iface = mesh_maker.interface.node_interface(
        name="node_ifc",
        constrained_node="constrained",
    )
    owner_mesh_maker = mesh_maker
    retained_part = owner_mesh_maker.meshpart.get("retained")

    tet_points = np.array(
        [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        dtype=float,
    )
    tet_cells = np.array([4, 0, 1, 2, 3], dtype=np.int64)
    tet_mesh = pv.UnstructuredGrid(tet_cells, [pv.CellType.TETRA], tet_points)
    tet_mesh.cell_data["MeshPartTag_celldata"] = np.array([retained_part.tag], dtype=np.int32)
    tet_mesh.cell_data["Core"] = np.array([0], dtype=np.int32)

    base_mesh = tet_mesh.copy()
    base_mesh.point_data["ndf"] = np.full(base_mesh.n_points, 3, dtype=np.int32)
    base_mesh.point_data["MeshPartTag_pointdata"] = np.zeros(base_mesh.n_points, dtype=np.uint16)
    base_mesh.point_data["Mass"] = np.zeros((base_mesh.n_points, 6), dtype=np.float32)
    base_mesh.cell_data["ElementTag"] = np.zeros(base_mesh.n_cells, dtype=np.uint16)
    base_mesh.cell_data["MaterialTag"] = np.zeros(base_mesh.n_cells, dtype=np.uint16)
    base_mesh.cell_data["Region"] = np.zeros(base_mesh.n_cells, dtype=np.uint16)
    owner_mesh_maker.assembled_mesh = base_mesh

    owner_context = {"tag": False, "element": False}
    original_asd_embedded_node = owner_mesh_maker.element.special.asd_embedded_node

    def tracked_get_start_node_tag():
        owner_context["tag"] = True
        return owner_mesh_maker._start_nodetag

    def tracked_asd_embedded_node(*args, **kwargs):
        owner_context["element"] = True
        return original_asd_embedded_node(*args, **kwargs)

    monkeypatch.setattr(owner_mesh_maker, "get_start_node_tag", tracked_get_start_node_tag)
    monkeypatch.setattr(
        owner_mesh_maker.element.special,
        "asd_embedded_node",
        tracked_asd_embedded_node,
    )

    def fail_meshmaker_singleton(*args, **kwargs):
        raise AssertionError("Model() singleton must not be used in post-assemble block 11")

    monkeypatch.setattr("femora.Model", fail_meshmaker_singleton)

    offset_points = np.array([[0.1, 0.1, 0.1]], dtype=float)
    monkeypatch.setattr(iface, "_tetrahedralize", lambda mesh: tet_mesh)
    monkeypatch.setattr(
        iface,
        "_create_offset_mesh",
        lambda mesh: (offset_points, np.array([0]), np.array([[0.0, 0.0, 1.0]])),
    )

    iface._on_post_assemble(assembled_mesh=base_mesh.copy())

    assert owner_context == {
        "tag": True,
        "element": True,
    }
    assert owner_mesh_maker.assembled_mesh is not base_mesh
    assert owner_mesh_maker.assembled_mesh.n_cells == base_mesh.n_cells + 1


def test_interface_manager_owns_embeddedinfo_list(mesh_maker):
    assert mesh_maker.interface._embeddedinfo_list == []
    _make_line_mesh(mesh_maker)
    mesh_maker.interface.beam_solid_interface(
        name="pile_ifc",
        beam_part="beam_mesh",
        radius=0.5,
    )
    assert mesh_maker.interface._embeddedinfo_list == []


def test_embeddedinfo_list_is_manager_scoped(mesh_maker):
    manager = mesh_maker.interface
    assert manager._embeddedinfo_list == []
    _assert_no_class_level_beam_solid_conflict_lifecycle()
    manager._embeddedinfo_list.append(
        EmbeddedInfo(beams=(1,), core_number=0, beams_solids=[([1], [2])])
    )
    assert len(manager._embeddedinfo_list) == 1
    manager._embeddedinfo_list.clear()
    assert manager._embeddedinfo_list == []


def test_pre_assemble_clears_manager_owned_embeddedinfo_list(mesh_maker):
    _make_line_mesh(mesh_maker)
    iface = mesh_maker.interface.beam_solid_interface(
        name="pile_ifc",
        beam_part="beam_mesh",
        radius=0.5,
    )
    mesh_maker.interface._embeddedinfo_list.append(
        EmbeddedInfo(beams=(1,), core_number=0, beams_solids=[([1], [2])])
    )

    iface._on_pre_assemble()

    assert mesh_maker.interface._embeddedinfo_list == []
    assert iface._instance_embeddedinfo_list == []


def test_clear_clears_manager_owned_embeddedinfo_list(mesh_maker):
    _make_line_mesh(mesh_maker)
    mesh_maker.interface.beam_solid_interface(
        name="pile_ifc",
        beam_part="beam_mesh",
        radius=0.5,
    )
    mesh_maker.interface._embeddedinfo_list.append(
        EmbeddedInfo(beams=(1,), core_number=0, beams_solids=[([1], [2])])
    )

    mesh_maker.interface.clear()

    assert mesh_maker.interface._embeddedinfo_list == []
