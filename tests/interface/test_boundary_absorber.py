import pytest

from femora.core.model import Model
from femora.components.material.nd import ElasticIsotropicMaterial


@pytest.fixture
def mesh_maker():
    mm = Model()
    mm.clear_model()
    return mm


def _make_box_meshpart(mm: Model):
    mat = mm.material.add(
        ElasticIsotropicMaterial(user_name="mat", E=200e3, nu=0.3, rho=0.0)
    )
    ele = mm.element.brick.std(ndof=3, material=mat)
    mm.meshpart.volume.uniform_rectangular_grid(
        user_name="box",
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
    mm.assembler.create_section(meshparts=["box"], num_partitions=1, merge_points=False)
    return mm


def test_boundary_absorber_registers_before_assembly(mesh_maker):
    _make_box_meshpart(mesh_maker)
    mesh_maker.interface.boundary.absorber(
        num_layers=1,
        num_partitions=0,
        partition_algo="kd-tree",
        geometry="Rectangular",
        type="Rayleigh",
        rayleigh_damping=0.95,
        match_damping=False,
    )
    assert len(mesh_maker.interface._boundary_absorbers) == 1


def test_boundary_absorber_applies_after_assembly(mesh_maker):
    _make_box_meshpart(mesh_maker)
    mesh_maker.interface.boundary.absorber(
        num_layers=1,
        num_partitions=0,
        partition_algo="kd-tree",
        geometry="Rectangular",
        type="Rayleigh",
        rayleigh_damping=0.95,
        match_damping=False,
    )
    base_cells = None
    mesh_maker.assembler.assemble(merge_points=False)
    assert mesh_maker.assembled_mesh is not None
    assert mesh_maker.assembled_mesh.n_cells > 1
    assert "AbsorbingRegion" in mesh_maker.assembled_mesh.cell_data
    assert int(mesh_maker.assembled_mesh.cell_data["AbsorbingRegion"].max()) > 0


def test_interface_manager_has_boundary_namespace(mesh_maker):
    assert hasattr(mesh_maker.interface, "boundary")
    assert callable(mesh_maker.interface.boundary.absorber)


def test_meshmaker_has_no_drm_runtime(mesh_maker):
    assert not hasattr(mesh_maker, "drm")
