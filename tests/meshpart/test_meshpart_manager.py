import pytest

from femora.components.MeshMaker import MeshMaker
from femora.components.material.nd import ElasticIsotropicMaterial
from femora.core.meshpart_base import MeshPart
from femora.core.meshpart_manager import MeshPartManager


@pytest.fixture
def mesh_maker():
    mk = MeshMaker()
    mk.clear_model()
    return mk


def test_meshpart_manager_model_owned(mesh_maker):
    assert isinstance(mesh_maker.meshpart, MeshPartManager)
    assert mesh_maker.meshpart._mesh_maker is mesh_maker


def test_duplicate_meshpart_manager_rejected(mesh_maker):
    with pytest.raises(ValueError, match="already owns a meshpart manager"):
        MeshPartManager(mesh_maker)


def test_unmanaged_meshpart_has_no_tag(mesh_maker):
    mat = mesh_maker.material.add(ElasticIsotropicMaterial(user_name="m", E=1.0, nu=0.3, rho=0.0))
    ele = mesh_maker.element.brick.std(ndof=3, material=mat)
    from femora.components.mesh.volume_meshparts import StructuredRectangular3D

    part = StructuredRectangular3D(
        user_name="raw",
        element=ele,
        region=mesh_maker.region.global_region,
        x_min=0,
        x_max=1,
        y_min=0,
        y_max=1,
        z_min=0,
        z_max=1,
        nx=1,
        ny=1,
        nz=1,
    )
    assert part.tag is None
    assert part._owner is None


def test_volume_factory_assigns_tag_and_region(mesh_maker):
    mat = mesh_maker.material.add(ElasticIsotropicMaterial(user_name="m2", E=1.0, nu=0.3, rho=0.0))
    ele = mesh_maker.element.brick.std(ndof=3, material=mat)
    part = mesh_maker.meshpart.volume.uniform_rectangular_grid(
        user_name="vol1",
        element=ele,
        x_min=0,
        x_max=1,
        y_min=0,
        y_max=1,
        z_min=0,
        z_max=1,
        nx=1,
        ny=1,
        nz=1,
    )
    assert part.tag == 1
    assert part._owner is mesh_maker.meshpart
    assert part.region is mesh_maker.region.global_region
    assert part.mesh is not None


def test_get_remove_clear(mesh_maker):
    mat = mesh_maker.material.add(ElasticIsotropicMaterial(user_name="m3", E=1.0, nu=0.3, rho=0.0))
    ele = mesh_maker.element.brick.std(ndof=3, material=mat)
    a = mesh_maker.meshpart.volume.uniform_rectangular_grid(
        user_name="a",
        element=ele,
        x_min=0,
        x_max=1,
        y_min=0,
        y_max=1,
        z_min=0,
        z_max=1,
        nx=1,
        ny=1,
        nz=1,
    )
    b = mesh_maker.meshpart.volume.uniform_rectangular_grid(
        user_name="b",
        element=ele,
        x_min=1,
        x_max=2,
        y_min=0,
        y_max=1,
        z_min=0,
        z_max=1,
        nx=1,
        ny=1,
        nz=1,
    )
    assert len(mesh_maker.meshpart.get_all()) == 2
    assert mesh_maker.meshpart.get("a") is a
    mesh_maker.meshpart.remove("a")
    assert a.tag is None
    assert len(mesh_maker.meshpart.get_all()) == 1
    mesh_maker.meshpart.clear()
    assert len(mesh_maker.meshpart.get_all()) == 0
    assert b.tag is None


def test_clear_model_resets_meshparts(mesh_maker):
    mat = mesh_maker.material.add(ElasticIsotropicMaterial(user_name="m4", E=1.0, nu=0.3, rho=0.0))
    ele = mesh_maker.element.brick.std(ndof=3, material=mat)
    mesh_maker.meshpart.volume.uniform_rectangular_grid(
        user_name="z",
        element=ele,
        x_min=0,
        x_max=1,
        y_min=0,
        y_max=1,
        z_min=0,
        z_max=1,
        nx=1,
        ny=1,
        nz=1,
    )
    mesh_maker.clear_model()
    assert len(mesh_maker.meshpart.get_all()) == 0


def test_explicit_constructor_rejects_unknown_kwargs(mesh_maker):
    mat = mesh_maker.material.add(ElasticIsotropicMaterial(user_name="m5", E=1.0, nu=0.3, rho=0.0))
    ele = mesh_maker.element.brick.std(ndof=3, material=mat)
    from femora.components.mesh.volume_meshparts import StructuredRectangular3D

    with pytest.raises(TypeError):
        StructuredRectangular3D(
            user_name="bad",
            element=ele,
            region=mesh_maker.region.global_region,
            x_min=0,
            x_max=1,
            y_min=0,
            y_max=1,
            z_min=0,
            z_max=1,
            nx=1,
            ny=1,
            nz=1,
            unexpected=1,
        )


def test_uniform_rectangular_grid_rejects_legacy_names(mesh_maker):
    mat = mesh_maker.material.add(ElasticIsotropicMaterial(user_name="m6", E=1.0, nu=0.3, rho=0.0))
    ele = mesh_maker.element.brick.std(ndof=3, material=mat)
    with pytest.raises(TypeError):
        mesh_maker.meshpart.volume.uniform_rectangular_grid(
            user_name="legacy",
            element=ele,
            **{
                "X Min": 0,
                "X Max": 1,
                "Y Min": 0,
                "Y Max": 1,
                "Z Min": 0,
                "Z Max": 1,
                "Nx Cells": 1,
                "Ny Cells": 1,
                "Nz Cells": 1,
            },
        )
