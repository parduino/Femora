import numpy as np
import pytest

import femora.components.material.nd  # noqa: F401 — register material types
import femora.components.element.std_brick  # noqa: F401 — register element types

from femora.core.model import Model
from femora.core.event_bus import EventBus, FemoraEvent
from femora.core.mask_manager import MaskManager


@pytest.fixture
def mesh_maker():
    mk = Model(model_name="mask_lifecycle_test")
    mk.clear_model()
    return mk


def _build_assembled_block(mesh_maker: Model, user_name: str = "block") -> None:
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


def test_components_mask_init_exports_query_types_only():
    import femora.components.mask as mask_pkg

    assert set(mask_pkg.__all__) == {"ElementMask", "MeshIndex", "NodeMask"}
    assert "MaskManager" not in mask_pkg.__all__


def test_mask_manager_lives_in_core():
    import femora.core.mask_manager as mask_manager_module

    assert mask_manager_module.__name__ == "femora.core.mask_manager"
    assert MaskManager.__module__ == "femora.core.mask_manager"


def test_mesh_maker_imports_core_mask_manager():
    from pathlib import Path

    mesh_maker_source = Path("src/femora/core/model.py").read_text(encoding="utf-8")
    assert "from femora.core.mask_manager import MaskManager" in mesh_maker_source
    assert "MaskManager.from_assembled" not in mesh_maker_source
    assert "MaskManager(mesh_maker=self)" in mesh_maker_source


def test_components_mask_module_is_not_authoritative():
    from pathlib import Path

    assert not Path("src/femora/components/mask/mask_manager.py").exists()


def test_mask_manager_has_no_class_level_runtime_state():
    assert not hasattr(MaskManager, "_cached_index")
    assert not hasattr(MaskManager, "_events_subscribed")
    assert not hasattr(MaskManager, "from_assembled")


def test_mesh_maker_owns_mask_manager(mesh_maker):
    assert isinstance(mesh_maker.mask, MaskManager)
    assert mesh_maker.mask._mesh_maker is mesh_maker


def test_mask_requires_assembled_mesh(mesh_maker):
    with pytest.raises(RuntimeError, match="assembled mesh"):
        _ = mesh_maker.mask.nodes


def test_mask_rebuilds_after_post_assemble(mesh_maker):
    _build_assembled_block(mesh_maker)
    assert len(mesh_maker.mask.nodes) == mesh_maker.assembled_mesh.n_points
    assert mesh_maker.mask._mesh_index is not None


def test_mask_cache_is_instance_owned(mesh_maker):
    other = Model(model_name="mask_other_model")
    other.clear_model()
    _build_assembled_block(mesh_maker)

    assert mesh_maker.mask._mesh_index is not None
    assert other.mask._mesh_index is None


def test_mask_manager_subscribes_to_model_event_bus(mesh_maker):
    EventBus._subscribers.clear()
    assert mesh_maker.mask._handle_post_assemble in mesh_maker.events._subscribers[
        FemoraEvent.POST_ASSEMBLE
    ]
    assert mesh_maker.mask._handle_post_assemble not in EventBus._subscribers.get(
        FemoraEvent.POST_ASSEMBLE, []
    )


def test_clear_model_clears_mask_cache_and_reregisters_events(mesh_maker):
    EventBus._subscribers.clear()
    _build_assembled_block(mesh_maker)
    assert mesh_maker.mask._mesh_index is not None

    mesh_maker.clear_model()

    assert mesh_maker.mask._mesh_index is None
    assert mesh_maker.mask._handle_post_assemble in mesh_maker.events._subscribers[
        FemoraEvent.POST_ASSEMBLE
    ]


def test_mask_nodes_and_elements_query(mesh_maker):
    _build_assembled_block(mesh_maker)
    assert len(mesh_maker.mask.nodes) > 0
    assert len(mesh_maker.mask.elements) > 0
    filtered = mesh_maker.mask.nodes.by_bbox(-1, 2, -1, 2, -1, 2)
    assert len(filtered) == mesh_maker.assembled_mesh.n_points
