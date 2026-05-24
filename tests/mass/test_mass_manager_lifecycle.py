import numpy as np
import pytest

import femora.components.material.nd  # noqa: F401 — register material types
import femora.components.element.std_brick  # noqa: F401 — register element types

from femora.components.MeshMaker import MeshMaker
from femora.core.mass_manager import MassManager
from femora.core.event_bus import EventBus, FemoraEvent


@pytest.fixture
def mesh_maker():
    MeshMaker._instance = None
    mk = MeshMaker(model_name="mass_lifecycle_test")
    mk.clear_model()
    return mk


def _build_assembled_block(mesh_maker: MeshMaker, user_name: str = "block") -> None:
    mat = mesh_maker.material.nd.elastic_isotropic(
        user_name="mat", E=1.0, nu=0.3, rho=1.0
    )
    ele = mesh_maker.element.brick.std(ndof=3, material=mat)
    mesh_maker.meshpart.volume.uniform_rectangular_grid(
        user_name=user_name,
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
    mesh_maker.assembler.create_section(
        meshparts=[user_name], num_partitions=1, merge_points=False
    )
    mesh_maker.assembler.assemble(merge_points=False)


def test_mass_manager_lives_in_core():
    import femora.core.mass_manager as mass_manager_module

    assert mass_manager_module.__name__ == "femora.core.mass_manager"
    assert MassManager.__module__ == "femora.core.mass_manager"


def test_mesh_maker_imports_core_mass_manager():
    from pathlib import Path

    mesh_maker_source = Path("src/femora/components/MeshMaker.py").read_text(encoding="utf-8")
    assert "from femora.core.mass_manager import MassManager" in mesh_maker_source
    assert "from femora.components.mass.mass_manager import MassManager" not in mesh_maker_source


def test_components_mass_is_not_authoritative():
    from pathlib import Path

    assert not Path("src/femora/components/mass/mass_manager.py").exists()


def test_mass_manager_requires_mesh_maker():
    with pytest.raises(TypeError, match="mesh_maker must be a MeshMaker instance"):
        MassManager(mesh_maker=None)


def test_mass_manager_has_no_singleton_api():
    assert not hasattr(MassManager, "get_instance")
    assert not hasattr(MassManager, "_instance")
    assert not hasattr(MassManager, "bind_mesh_maker")


def test_mesh_maker_owns_mass_manager(mesh_maker):
    assert isinstance(mesh_maker.mass, MassManager)
    assert mesh_maker.mass._mesh_maker is mesh_maker


def test_mass_manager_subscribes_to_model_event_bus(mesh_maker):
    EventBus._subscribers.clear()

    assert mesh_maker.mass._handle_pre_assemble in mesh_maker.events._subscribers[
        FemoraEvent.PRE_ASSEMBLE
    ]
    assert mesh_maker.mass._handle_pre_assemble not in EventBus._subscribers.get(
        FemoraEvent.PRE_ASSEMBLE, []
    )


def test_region_cache_is_instance_owned(mesh_maker):
    MeshMaker._instance = None
    other = MeshMaker(model_name="mass_other_model")
    other.clear_model()

    mesh_maker.mass._region_point_cache[1] = np.array([10])
    assert 1 not in other.mass._region_point_cache


def test_pre_assemble_clears_region_cache(mesh_maker):
    mesh_maker.mass._region_point_cache[1] = np.array([0])
    mesh_maker.events.emit(FemoraEvent.PRE_ASSEMBLE)
    assert mesh_maker.mass._region_point_cache == {}


def test_clear_model_clears_cache_and_reregisters_events(mesh_maker):
    EventBus._subscribers.clear()
    mesh_maker.mass._region_point_cache[1] = np.array([0])

    mesh_maker.clear_model()

    assert mesh_maker.mass._handle_pre_assemble in mesh_maker.events._subscribers[
        FemoraEvent.PRE_ASSEMBLE
    ]
    assert mesh_maker.mass._region_point_cache == {}


def test_get_assembled_mass_array_reads_model_owned_mesh(mesh_maker):
    _build_assembled_block(mesh_maker)

    mass_array = mesh_maker.mass.get_assembled_mass_array()
    assert mass_array is not None
    assert mass_array.shape[0] == mesh_maker.assembled_mesh.n_points


def test_meshpart_mass_edits_do_not_auto_sync_to_assembled_mesh(mesh_maker):
    _build_assembled_block(mesh_maker)

    assembled_before = mesh_maker.mass.get_assembled_mass_array().copy()
    mesh_maker.mass.meshpart.add_all("block", [1.0, 1.0, 1.0], combine="override")
    assembled_after = mesh_maker.mass.get_assembled_mass_array()

    assert np.array_equal(assembled_before, assembled_after)


def test_meshpart_mass_is_authoritative_pre_assembly(mesh_maker):
    mat = mesh_maker.material.nd.elastic_isotropic(
        user_name="mat", E=1.0, nu=0.3, rho=1.0
    )
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
    mesh_maker.mass.meshpart.add_all("block", [2.0, 2.0, 2.0], combine="override")
    mesh_maker.assembler.create_section(
        meshparts=["block"], num_partitions=1, merge_points=False
    )
    mesh_maker.assembler.assemble(merge_points=False)

    assembled_mass = mesh_maker.mass.get_assembled_mass_array()
    assert np.any(assembled_mass[:, :3] == 2.0)
