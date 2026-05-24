import pytest

from femora.core.assembler import Assembler
from femora.core.model import Model
from femora.components.event.event_bus import EventBus

from femora.components.material.nd import ElasticIsotropicMaterial


@pytest.fixture()
def femora_clean_state():
    """Reset local Femora model state that impacts assembly."""
    old_subscribers = EventBus._subscribers.copy()
    EventBus._subscribers.clear()

    mm = Model()
    mm.clear_model()

    assembler = mm.assembler
    assembler.clear()
    assembler.delete_assembled_mesh()

    try:
        yield mm, assembler
    finally:
        assembler.clear()
        assembler.delete_assembled_mesh()
        mm.clear_model()
        EventBus._subscribers = old_subscribers


def _make_two_adjacent_brick_meshparts(mm: Model):
    mat = mm.material.add(ElasticIsotropicMaterial(user_name="mat", E=200e3, nu=0.3, rho=0.0))
    ele = mm.element.brick.std(ndof=3, material=mat)

    # Two cubes that share the x=1 face (4 coincident points)
    mm.meshpart.volume.uniform_rectangular_grid(
        user_name="part_a",
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

    mm.meshpart.volume.uniform_rectangular_grid(
        user_name="part_b",
        element=ele,
        x_min=1.0,
        x_max=2.0,
        y_min=0.0,
        y_max=1.0,
        z_min=0.0,
        z_max=1.0,
        nx=1,
        ny=1,
        nz=1,
    )

    return "part_a", "part_b"


@pytest.mark.parametrize(
    "participate_b, expected_points",
    [
        (True, 12),   # interface points merged (16 -> 12)
        (False, 16),  # part_b excluded from final merge, no interface merging
    ],
)
def test_final_merge_participation_controls_cross_section_merging(
    femora_clean_state,
    participate_b: bool,
    expected_points: int,
):
    mm, assembler = femora_clean_state
    part_a, part_b = _make_two_adjacent_brick_meshparts(mm)

    assembler.create_section(
        meshparts=[part_a],
        num_partitions=1,
        merge_points=False,
        merge_in_final=True,
    )
    assembler.create_section(
        meshparts=[part_b],
        num_partitions=1,
        merge_points=False,
        merge_in_final=participate_b,
    )

    assembler.assemble(merge_points=True)

    assert mm.assembled_mesh is not None
    assert int(mm.assembled_mesh.n_points) == int(expected_points)
