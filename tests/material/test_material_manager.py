import pytest

from femora.components.MeshMaker import MeshMaker


@pytest.fixture
def mesh_maker():
    mk = MeshMaker()
    mk.clear_model()
    return mk


def test_material_manager_has_no_get_material_alias(mesh_maker):
    assert not hasattr(mesh_maker.material, "get_material")
